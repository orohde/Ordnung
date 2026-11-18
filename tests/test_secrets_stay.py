"""A stored key or token belongs to the address it was given for: changing the address never sends it on."""
from ordnung.ai import AIService
from ordnung.security import SecurityStore


def test_the_ai_key_does_not_follow_a_new_address(tmp_path):
    ai = AIService(tmp_path / "ai.json")
    ai.update({"provider": "anthropic", "api_key": "sk-ant-geheim"})
    ai.update({"model": ai.load().model, "enabled": True})               # saving the rest keeps the key
    assert ai.load().api_key == "sk-ant-geheim"
    ai.update({"provider": "openai", "base_url": "https://fremd.example/v1"})
    assert ai.load().api_key == ""                                       # a new address: the key is gone
    ai.update({"provider": "openai", "base_url": "https://fremd.example/v1", "api_key": "sk-neu"})
    assert ai.load().api_key == "sk-neu"                                 # given together: kept
    ai.update({"base_url": "https://fremd.example/v1/"})                 # the same address, written otherwise
    assert ai.load().api_key == "sk-neu"


def test_the_ntfy_token_does_not_follow_a_new_address(tmp_path):
    store = SecurityStore(tmp_path / "security.json")
    store.update({"ntfy_url": "https://ntfy.example/thema", "ntfy_token": "tk_geheim"})
    store.update({"ntfy_url": "https://ntfy.example/thema", "ntfy_token": ""})
    assert store.load().ntfy_token == "tk_geheim"
    store.update({"ntfy_url": "https://fremd.example/thema"})
    assert store.load().ntfy_token == ""
    store.update({"ntfy_url": "https://fremd.example/thema", "ntfy_token": "tk_neu"})
    assert store.load().ntfy_token == "tk_neu"


def test_the_mail_password_does_not_follow_a_new_server(tmp_path):
    from ordnung.mailin import MailStore
    store = MailStore(tmp_path / "mail.json")
    store.update({"host": "imap.example", "user": "post", "password": "geheim"})
    store.update({"host": "imap.example", "password": ""})
    assert store.load().password == "geheim"
    store.update({"host": "imap.fremd.example"})
    assert store.load().password == ""
