from email.message import EmailMessage

import pytest
from fastapi.testclient import TestClient

from conftest import make_pdf
from ordnung.mailin import MailInbox, MailStore, _auth_failed
from ordnung.users import UserError, UserStore
from test_api import client, login  # noqa: F401  (fixture)


def _mail(sender="hanna@example.org", pdfs=(("Rechnung.pdf", "Rechnung Zahnarzt"),), auth=None, subject="Fwd: Rechnung"):
    msg = EmailMessage()
    msg["From"] = f"Hanna <{sender}>"
    msg["To"] = "eingang@rohde.one"
    msg["Subject"] = subject
    if auth:
        msg["Authentication-Results"] = auth
    msg.set_content("Bitte ablegen.")
    for name, text in pdfs:
        msg.add_attachment(make_pdf(text), maintype="application", subtype="pdf", filename=name)
    return msg


@pytest.fixture
def mailbox(tmp_path):
    users = UserStore(tmp_path / "users.json")
    users.create("oliver", "geheim-geheim-1", is_admin=True, emails=["Oliver@Example.org"])
    users.create("hanna", "geheim-geheim-2", areas={"hanna": "write", "gemeinsam": "write"},
                 emails=["hanna@example.org"])
    store = MailStore(tmp_path / "mail.json")
    return MailInbox(store, users, tmp_path / "mail", 10), users


def test_emails_are_checked_and_unique(mailbox):
    _, users = mailbox
    assert users.get("oliver").emails == ["oliver@example.org"]
    assert users.by_email("OLIVER@example.org").name == "oliver"
    with pytest.raises(UserError, match="already belongs to hanna"):
        users.update("oliver", emails=["hanna@example.org"])
    with pytest.raises(UserError, match="invalid e-mail"):
        users.update("oliver", emails=["kein-at-zeichen"])
    assert users.get("hanna").own_area() == "hanna"
    users.update("hanna", mail_area="gemeinsam")
    assert users.get("hanna").own_area() == "gemeinsam"


def test_known_sender_pdfs_land_in_her_area(mailbox, tmp_path):
    inbox, _ = mailbox
    msg = _mail(pdfs=(("Rechnung.pdf", "Rechnung"), ("Rechnung.pdf", "Rechnung"), ("Beleg.pdf", "Beleg")))
    msg.add_attachment(b"GIF89a", maintype="image", subtype="gif", filename="logo.gif")
    event = inbox.process(msg.as_bytes())
    assert event["result"] == "accepted" and event["area"] == "hanna"
    assert sorted(event["files"]) == ["Beleg.pdf", "Rechnung.pdf"]          # same PDF only once, no GIF
    assert sorted(p.name for p in (tmp_path / "mail/hanna").iterdir()) == ["Beleg.pdf", "Rechnung.pdf"]


def test_forwarded_mail_inside_a_mail(mailbox):
    inbox, _ = mailbox
    outer = EmailMessage()
    outer["From"] = "oliver@example.org"
    outer["Subject"] = "Fwd"
    outer.set_content("siehe Anhang")
    outer.add_attachment(_mail(sender="buchhaltung@firma.de"))
    event = inbox.process(outer.as_bytes())
    assert event["result"] == "accepted" and event["user"] == "oliver" and event["area"] == "oliver"


@pytest.mark.parametrize("kwargs, reason", [
    ({"sender": "fremd@spam.example"}, "unknown_sender"),
    ({"pdfs": ()}, "no_pdf"),
    ({"auth": "mx.infomaniak.com; spf=fail smtp.mailfrom=example.org; dkim=none; dmarc=fail"}, "forged"),
])
def test_refused(mailbox, tmp_path, kwargs, reason):
    inbox, _ = mailbox
    event = inbox.process(_mail(**kwargs).as_bytes())
    assert (event["result"], event["reason"]) == ("rejected", reason)
    assert not (tmp_path / "mail").exists()


def test_auth_results():
    def check(value):
        msg = EmailMessage()
        if value:
            msg["Authentication-Results"] = value
        return _auth_failed(msg)
    assert not check(None)                                      # no header: nothing to go by
    assert not check("mx; spf=pass; dkim=pass; dmarc=pass")
    assert not check("mx; spf=softfail; dkim=pass")             # forwarded mails often break SPF only
    assert check("mx; spf=fail; dkim=fail")
    assert check("mx; spf=pass; dmarc=fail")


class FakeIMAP:
    capabilities = ("IMAP4REV1", "MOVE")

    def __init__(self, mails, rejected=()):
        self.mails = dict(mails)
        self.rejected = list(rejected)       # uids already in "Abgelehnt"
        self.moved = {}
        self.deleted = []
        self.folder = "INBOX"
        self.searched = None

    def select(self, folder, readonly=False):
        self.folder = folder.strip('"')
        return "OK", [str(len(self.mails)).encode()]

    def expunge(self):
        return "OK", []

    def create(self, folder):
        return "NO", [b"exists"]

    def uid(self, cmd, *args):
        if cmd == "SEARCH" and self.folder == "Abgelehnt":
            self.searched = args
            return "OK", [b" ".join(self.rejected)]
        if cmd == "SEARCH":
            return "OK", [b" ".join(self.mails)]
        if cmd == "STORE":
            self.deleted.append((self.folder, args[0]))
            self.mails.pop(args[0], None) if self.folder == "INBOX" else None
            return "OK", []
        if cmd == "FETCH":
            return "OK", [(b"1 (BODY[] {n}", self.mails[args[0]]), b")"]
        if cmd == "MOVE":
            self.moved[args[0]] = args[1].strip('"')
            del self.mails[args[0]]
            return "OK", []
        raise AssertionError(cmd)

    def logout(self):
        pass


def test_fetch_moves_mails(mailbox, monkeypatch):
    inbox, _ = mailbox
    inbox.store.update({"enabled": True, "host": "imap.example.org", "user": "eingang", "password": "pw"})
    fake = FakeIMAP({b"1": _mail().as_bytes(), b"2": _mail(sender="x@spam.example").as_bytes()})
    monkeypatch.setattr(inbox, "_connect", lambda config: fake)
    assert inbox.fetch() == {"started": True, "mails": 2, "accepted": 1, "files": 1, "rejected": 1}
    assert fake.moved == {b"1": "Abgelegt", b"2": "Abgelehnt"}
    events = inbox.store.events()
    assert [e["result"] for e in events] == ["rejected", "accepted"]      # newest first


def test_api_and_inbox(client: TestClient, settings):  # noqa: F811
    login(client, "oliver", "geheim123")
    res = client.put("/api/mail", json={"enabled": True, "host": "imap.example.org", "user": "eingang", "password": "geheim"})
    assert res.status_code == 200 and res.json()["has_password"] and "password" not in res.json()
    assert "geheim" not in client.get("/api/mail").text
    assert client.put("/api/mail", json={"clear_password": True}).status_code == 400   # still switched on
    assert client.patch("/api/users/oliver", json={"emails": ["oliver@example.org"]}).json()["mail_target"] == "oliver"
    event = client.app.state.mail.process(_mail(sender="oliver@example.org").as_bytes())
    assert event["result"] == "accepted"
    files = client.app.state.mail.target / "oliver"
    import os, time
    past = time.time() - 60
    for p in files.iterdir():
        os.utime(p, (past, past))
    client.app.state.inbox.scan()
    items = [i for i in client.get("/api/inbox").json()["items"] if i["inbox"] == "mail"]
    assert [i["rel"] for i in items] == ["oliver/Rechnung.pdf"]
    client.app.state.inbox.extract_pending(client.app.state.extractor)
    item = next(i for i in client.get("/api/inbox").json()["items"] if i["inbox"] == "mail")
    assert item["suggestion"]["area"] == "oliver"


def test_refused_mails_are_deleted_after_the_set_days(mailbox, monkeypatch):
    inbox, _ = mailbox
    inbox.store.update({"enabled": True, "host": "imap.example.org", "user": "eingang", "password": "pw"})
    assert inbox.store.load().reject_days == 7
    fake = FakeIMAP({}, rejected=[b"7", b"8"])
    monkeypatch.setattr(inbox, "_connect", lambda config: fake)
    inbox.fetch()
    assert fake.deleted == [("Abgelehnt", b"7"), ("Abgelehnt", b"8")]
    assert fake.searched[1] == "BEFORE" and fake.searched[2][3:6] in (
        "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())
    fake.deleted.clear()
    inbox.fetch()                                   # at most once an hour
    assert fake.deleted == []


def test_zero_days_deletes_at_once(mailbox, monkeypatch):
    inbox, _ = mailbox
    inbox.store.update({"enabled": True, "host": "imap.example.org", "user": "eingang", "password": "pw",
                        "reject_days": 0})
    fake = FakeIMAP({b"1": _mail(sender="x@spam.example").as_bytes(), b"2": _mail().as_bytes()})
    monkeypatch.setattr(inbox, "_connect", lambda config: fake)
    inbox.fetch()
    assert ("INBOX", b"1") in fake.deleted and fake.moved == {b"2": "Abgelegt"}
    with pytest.raises(Exception, match="days"):
        inbox.store.update({"reject_days": -1})
