"""Senders: who a document comes from, as people think about filing.

People do not think in conditions ("contains X and Y") but in senders: "post from
Cosmos about the car goes into the car insurance folder". The most reliable hint
to the sender in a letter is its web or mail address (cosmosdirekt.de), so a
sender here is a domain. Measured on the first real archive: 55 % of the
documents have one, and most senders file into exactly one folder.

This module
* detects the sender of a text,
* keeps readable names and the household's own addresses (``senders.json``),
* builds the sender overview (where does each sender's post go, do the rules
  get it right?) and
* proposes a rule in plain words after a document was filed by hand.

Every proposal is measured against all filed documents first: it must find the
new document and must not claim a single document from another folder.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from .index import fold
from .rules import Condition, RuleService, _brief, compile_condition, nospace

HEAD_CHARS = 2500        # the letterhead: an address here counts more
_DOMAIN = re.compile(r"(?<![\w@.-])(?:https?://)?(?:www\.)?((?:[a-z0-9][a-z0-9\-]{0,40}\.)+"
                     r"(?:de|com|net|eu|org|at|ch|info|bank|io))(?![\w-])", re.IGNORECASE)
_MAIL = re.compile(r"[\w.+-]+@((?:[a-z0-9][a-z0-9\-]*\.)+[a-z]{2,6})", re.IGNORECASE)
# mail providers, tech giants and authorities that show up everywhere without being the sender
GENERIC = {
    "gmail.com", "googlemail.com", "web.de", "gmx.de", "gmx.net", "t-online.de", "icloud.com", "me.com",
    "outlook.com", "outlook.de", "hotmail.com", "hotmail.de", "live.de", "yahoo.de", "yahoo.com", "freenet.de",
    "arcor.de", "posteo.de", "mailbox.org", "google.com", "google.de", "apple.com", "microsoft.com",
    "adobe.com", "w3.org", "paypal.com", "paypal.de", "youtube.com", "facebook.com", "instagram.com",
    "twitter.com", "x.com", "linkedin.com", "xing.com", "bundesbank.de", "bafin.de", "europa.eu", "de-mail.de",
}
_WORD = re.compile(r"[a-zäöüß][a-zäöüß\-]{5,30}")
_STOP = {"freundlichen", "grüßen", "geehrte", "geehrter", "damen", "herren", "telefon", "telefax", "internet",
         "e-mail", "postfach", "straße", "strasse", "seite", "datum", "betreff", "rechnung", "kundennummer",
         "vertragsnummer", "anschrift", "mitteilung", "informationen", "unterlagen", "ihrem", "ihrer", "ihren",
         "unsere", "unserer", "bitte", "wurde", "werden", "haben", "können", "sowie", "zwischen", "gemäß",
         "januar", "februar", "april", "august", "september", "oktober", "november", "dezember"}
_IDS = re.compile(r"\b(?:DE|AT|CH|LU|NL)\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,4})?\b"
                  r"|(?:vertrags|versicherungs|kunden|mitglieds|konto|police|zähler|aktenzeichen|kennzeichen)"
                  r"[\w\-]*\s*[:.]?\s*([A-Z0-9][A-Z0-9 \-/.]{4,22}[A-Z0-9])", re.IGNORECASE)


def base_domain(domain: str) -> str:
    parts = domain.lower().strip(".").split(".")
    return ".".join(parts[-2:])


def candidates(text: str) -> Counter:
    """Domains in a text, weighted: an address in the letterhead counts more."""
    found: Counter = Counter()
    for m in list(_DOMAIN.finditer(text)) + list(_MAIL.finditer(text)):
        d = base_domain(m.group(1))
        if d in GENERIC or len(d) < 5 or d[0].isdigit():
            continue
        found[d] += 1 + (3 if m.start() < HEAD_CHARS else 0)
    return found


def detect(text: str, own: set[str]) -> str | None:
    found = Counter({d: n for d, n in candidates(text or "").items() if d not in own})
    return found.most_common(1)[0][0] if found else None


def pretty(domain: str) -> str:
    """A first readable name: "cosmosdirekt.de" → "Cosmosdirekt", "dkb.de" → "DKB"."""
    stem = domain.split(".")[0]
    words = [w for w in stem.split("-") if w]
    if len(words) == 1 and len(words[0]) <= 3:
        return words[0].upper()                       # an abbreviation: DKB, TK, ING
    return " ".join(w.capitalize() for w in words) or domain


def grade(ok: int, total: int, wrong: int = 0) -> str:
    """Traffic light for people: green = sure, yellow = mostly, red = guessing / unknown."""
    if not total:
        return "red"
    if wrong == 0 and ok / total >= 0.8:
        return "green"
    if ok / total >= 0.5 and wrong / total <= 0.1:
        return "yellow"
    return "red"


def rule_grade(inside: int, outside: int) -> str:
    if inside and not outside:
        return "green"
    if inside and outside / (inside + outside) <= 0.1:
        return "yellow"
    return "red"


class SenderBook:
    """Readable names, the household's own addresses and declined proposals (``senders.json``)."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def load(self) -> dict:
        data = {"names": {}, "own": [], "declined": []}
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for key in data:
                if key in raw:
                    data[key] = raw[key]
        return data

    def _save(self, data: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": 1, **data}, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def own(self) -> set[str]:
        return set(self.load()["own"])

    def name(self, domain: str, data: dict | None = None) -> str:
        data = data or self.load()
        return data["names"].get(domain) or pretty(domain)

    def rename(self, domain: str, name: str) -> None:
        name = re.sub(r"\s+", " ", name or "").strip()[:60]
        with self._lock:
            data = self.load()
            if name and name != pretty(domain):
                data["names"][domain] = name
            else:
                data["names"].pop(domain, None)
            self._save(data)

    def set_own(self, domain: str, own: bool) -> None:
        with self._lock:
            data = self.load()
            items = set(data["own"])
            if own:
                items.add(domain)
            else:
                items.discard(domain)
            data["own"] = sorted(items)
            self._save(data)

    def decline(self, domain: str, folder: str) -> None:
        with self._lock:
            data = self.load()
            key = f"{domain}|{folder}"
            if key not in data["declined"]:
                data["declined"].append(key)
                self._save(data)

    def declined(self, domain: str, folder: str) -> bool:
        return f"{domain}|{folder}" in self.load()["declined"]


class SenderService:
    def __init__(self, book: SenderBook, rules: RuleService):
        self.book = book
        self.rules = rules
        self._cache: tuple[tuple, dict] | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------- overview

    def _key(self, corpus) -> tuple:
        def mtime(p: Path) -> int:
            try:
                return p.stat().st_mtime_ns
            except OSError:
                return 0
        return (id(corpus), len(corpus.docs), mtime(self.rules.path), mtime(self.book.path))

    def _by_sender(self) -> dict:
        corpus = self.rules.corpus()
        key = self._key(corpus)
        with self._lock:
            if self._cache and self._cache[0] == key:
                return self._cache[1]
            own = self.book.own()
            match = self.rules.matcher()
            senders: dict[str, list] = defaultdict(list)
            for d in corpus.docs:
                if not d.folder:
                    continue
                s = detect(d.raw, own)
                if not s:
                    continue
                votes = Counter(h["folder"] for h in match(d.raw))
                if not votes:
                    verdict = "none"
                else:
                    top = votes.most_common()
                    verdict = "ok" if top[0][0] == d.folder and (len(top) == 1 or top[1][1] < top[0][1]) else (
                        "conflict" if d.folder in votes else "wrong")
                senders[s].append((d, verdict))
            result = {"senders": senders, "built": time.time()}
            self._cache = (key, result)
            return result

    def overview(self, areas: list[str] | None = None) -> list[dict]:
        data = self.book.load()
        out = []
        for domain, items in self._by_sender()["senders"].items():
            if areas is not None:
                items = [(d, v) for d, v in items if d.area in areas]
            if not items:
                continue
            folders: dict[str, Counter] = defaultdict(Counter)
            for d, verdict in items:
                folders[d.folder][verdict] += 1
            ok = sum(c["ok"] for c in folders.values())
            wrong = sum(c["wrong"] for c in folders.values())
            total = len(items)
            out.append({
                "domain": domain, "name": self.book.name(domain, data), "docs": total,
                "ok": ok, "wrong": wrong, "none": sum(c["none"] for c in folders.values()),
                "grade": grade(ok, total, wrong),
                "folders": sorted(({"folder": f, "docs": sum(c.values()), "ok": c["ok"], "wrong": c["wrong"],
                                    "grade": grade(c["ok"], sum(c.values()), c["wrong"])}
                                   for f, c in folders.items()), key=lambda x: -x["docs"]),
            })
        out.sort(key=lambda x: (-x["docs"], x["name"].casefold()))
        return out

    def documents(self, domain: str, folder: str | None = None, areas: list[str] | None = None,
                  limit: int = 6) -> list[dict]:
        items = self._by_sender()["senders"].get(domain, [])
        docs = [d for d, _ in items if (folder is None or d.folder == folder)
                and (areas is None or d.area in areas) and d.origin == "archive"]
        docs.sort(key=lambda d: d.date or "", reverse=True)
        return [_brief(d) for d in docs[:limit]]

    # ------------------------------------------------------------- proposal

    def propose(self, text: str, folder: str, areas: list[str] | None = None,
                sender: str | None = None) -> dict | None:
        """The simplest rule that would have filed this text into ``folder`` – or None.

        Tried in this order, each must find this text and claim nothing elsewhere:
        1. the sender alone            ("post from Cosmos Direkt")
        2. sender + one word or number ("post from DKB with 'Kreditkartenabrechnung'")
        3. without sender: a number or word pair that only this folder has.
        """
        folder = folder.strip("/")
        if not folder or not text:
            return None
        hits = self.rules.match(text)
        votes = Counter(h["folder"] for h in hits)
        if votes and votes.most_common(1)[0][0] == folder and len(votes) == 1:
            return None                                    # the rules know this already
        own = self.book.own()
        sender = sender or detect(text, own)
        if sender and self.book.declined(sender, folder):
            return None
        corpus = self.rules.corpus()
        folded = fold(text[:20000])
        compact = nospace(folded)

        def measure(conds: list[Condition]) -> dict:
            preds = [compile_condition(c) for c in conds]
            inside = [d for d in corpus.docs if d.folder == folder and all(p(d) for p in preds)]
            outside = [d for d in corpus.docs if d.folder != folder and all(p(d) for p in preds)]
            return {"inside": len(inside), "outside": len(outside), "docs": inside}

        def fits(c: Condition) -> bool:
            if c.type == "id":
                return nospace(fold(c.value)) in compact
            return fold(c.value).strip() in folded

        options: list[tuple[list[Condition], str]] = []
        if sender:
            options.append(([Condition("contains", sender)], "sender"))
            sender_docs = [d for d in corpus.docs if sender in d.text]
            mine = [d for d in sender_docs if d.folder == folder]
            others = [d for d in sender_docs if d.folder != folder]
            other_tokens = set().union(*(d.tokens for d in others)) if others else set()
            # numbers of this document: contract numbers, IBANs …
            for m in _IDS.finditer(text[:20000]):
                value = (m.group(1) or m.group(0)).strip()
                if sum(ch.isdigit() for ch in value) >= 5:
                    options.append(([Condition("contains", sender), Condition("id", value)], "sender+id"))
            # words this sender only uses for this folder
            words = Counter()
            for d in mine:
                words.update(t for t in d.tokens if t not in other_tokens)
            for word in sorted(set(_WORD.findall(folded)) - _STOP, key=lambda w: -words[w]):
                if words[word] >= 1 and word not in other_tokens:
                    options.append(([Condition("contains", sender), Condition("contains", word)], "sender+word"))
                if len(options) > 40:
                    break
        else:
            for s in self.rules.suggest(folder, limit=15, min_precision=1.0):
                conds = [Condition(**c) for c in s["conditions"]]
                if all(fits(c) for c in conds):
                    options.append((conds, "id" if s["kind"] == "id" else "word"))

        best = None
        for conds, kind in options:
            if not all(fits(c) for c in conds):
                continue
            m = measure(conds)
            if m["outside"]:
                continue
            score = m["inside"] * 10 - len(conds) - (0 if kind == "sender" else 1)
            if best is None or score > best[0]:
                best = (score, conds, kind, m)
            if kind == "sender":
                break                                      # nothing beats "all post from X"
        if not best:
            return None
        _, conds, kind, m = best
        # show words as written in the letter ("Kreditkartenabrechnung"), matching ignores case anyway
        conds = [Condition(c.type, _original(text, c.value)) if c.type == "contains" and c.value != sender else c
                 for c in conds]
        examples = [_brief(d) for d in m["docs"] if d.origin == "archive"
                    and (areas is None or d.area in areas)][:3]
        cond_dicts = [asdict(c) for c in conds]
        return {
            "folder": folder, "sender": sender, "sender_name": self.book.name(sender) if sender else "",
            "kind": kind, "conditions": cond_dicts, "label": describe(cond_dicts, self.book.name),
            "inside": m["inside"], "grade": "green", "examples": examples,
        }


def _original(text: str, word: str) -> str:
    m = re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text or "", re.IGNORECASE)
    return m.group(0) if m else word


_DOMAIN_ONLY = re.compile(r"^(?:[a-z0-9][a-z0-9\-]*\.)+[a-z]{2,6}$")


def describe(conditions: list[dict], names) -> str:
    """A rule in plain German: "Post von Cosmos Direkt, in der „Kennzeichen“ vorkommt"."""
    sender = next((c["value"] for c in conditions
                   if c["type"] == "contains" and _DOMAIN_ONLY.match(c["value"].strip().lower())), None)
    rest = [c for c in conditions if c["value"] != sender]
    numbers = [c["value"] for c in rest if c["type"] == "id"]
    words = [c["value"] for c in rest if c["type"] == "contains"]
    patterns = [c for c in rest if c["type"] == "regex"]
    parts = []
    if numbers:
        parts.append("mit der Nummer " + " und ".join(numbers))
    if words:
        parts.append("in der " + " und ".join(f"„{w}“" for w in words) + (" vorkommt" if len(words) == 1 else " vorkommen"))
    if patterns:
        parts.append("die einem Suchmuster entspricht")
    if sender:
        head = f"Post von {names(sender)}"
        return head + (", " + ", ".join(parts) if parts else "")
    if numbers and not words:
        return "Schreiben mit der Nummer " + " und ".join(numbers)
    if words and not numbers:
        return "Schreiben, in denen " + " und ".join(f"„{w}“" for w in words) + (" vorkommt" if len(words) == 1 else " vorkommen")
    return "Schreiben " + ", ".join(parts)
