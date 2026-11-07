"""Folder cards and filing rules.

A rule belongs to a folder of the shared folder template and consists of
conditions that must all match the document text. Every rule is measured
against the documents already filed: how many it finds in its own folder and
how many it would wrongly claim from elsewhere.

Rules live in ``rules.json`` in the data folder – they are configuration and
cannot be rebuilt from the archive.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .index import Index, fold

CONDITION_TYPES = ("contains", "id", "regex")
MATCH_CHARS = 20_000        # rules look at the beginning of a document
MINE_CHARS = 12_000         # suggestion mining looks at a bit less
SAMPLE = 25                 # how many misses/outsiders are listed

_TOKEN_RE = re.compile(r"[a-zäöüß][a-zäöüß0-9\-]{4,40}")
_IBAN_RE = re.compile(r"\b(?:DE|AT|CH|LU|NL|FR|BE|IT|ES)\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,4})?\b")
# A label that names a lasting identifier, directly followed by its value.
# Invoice numbers are left out on purpose: they change with every document.
_LABELED_RE = re.compile(
    r"\b(?:(?:vertrags|versicherungsschein|versicherungs|kunden|mitglieds|policen|konto|personal|"
    r"steuer|zähler|vorgangs|mandats|referenz|objekt|liegenschafts|fahrzeugident)[\s\-]?"
    r"(?:nummer|nr\.?|no\.?)|steuer-?id|aktenzeichen|az\.|kennzeichen)\s*[:.]?\s*"
    r"([A-Z0-9](?:[A-Z0-9\-/\.]|\s(?=\d)){4,24}[A-Z0-9])",
    re.IGNORECASE,
)
_DATE_RE = re.compile(r"^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$")


def _good_identifier(value: str) -> bool:
    if not 5 <= len(value) <= 26 or _DATE_RE.match(value):
        return False
    if sum(ch.isdigit() for ch in value) < 4:
        return False
    return re.search(r"[a-zäöüß]{3}", value) is None  # running text, not a number


class RuleError(ValueError):
    pass


@dataclass
class Condition:
    type: str
    value: str


@dataclass
class Rule:
    id: str
    folder: str
    conditions: list[Condition]
    enabled: bool = True
    source: str = "manual"       # manual | suggestion | ai | auto | starter | learned
    note: str = ""
    created: str = ""
    label: str = ""              # in plain words, e.g. "Post von Cosmos Direkt" (learned rules)


@dataclass
class FolderCard:
    description: str = ""


@dataclass
class RuleBook:
    folders: dict[str, FolderCard] = field(default_factory=dict)
    rules: list[Rule] = field(default_factory=list)


def nospace(text: str) -> str:
    return re.sub(r"\s+", "", text)


def compile_condition(cond: Condition):
    """Return a predicate on a prepared document."""
    if cond.type == "contains":
        needle = fold(cond.value).strip()
        return lambda d: needle in d.text
    if cond.type == "id":
        needle = nospace(fold(cond.value))
        return lambda d: needle in d.compact
    if cond.type == "regex":
        try:
            pattern = re.compile(cond.value, re.IGNORECASE)
        except re.error as exc:
            raise RuleError(f"invalid regex: {exc}") from exc
        return lambda d: pattern.search(d.raw) is not None
    raise RuleError(f"unknown condition type: {cond.type}")


def check_conditions(conditions: list[dict]) -> list[Condition]:
    result = []
    for raw in conditions:
        ctype = raw.get("type")
        value = (raw.get("value") or "").strip()
        if ctype not in CONDITION_TYPES:
            raise RuleError(f"unknown condition type: {ctype}")
        if len(value) < 3:
            raise RuleError("condition too short (min. 3 characters)")
        cond = Condition(ctype, value)
        compile_condition(cond)
        result.append(cond)
    if not result:
        raise RuleError("a rule needs at least one condition")
    return result


# --------------------------------------------------------------------- corpus

@dataclass
class Doc:
    idx: int
    id: str
    folder: str
    area: str
    title: str
    date: str | None
    raw: str          # original text (start of document)
    text: str         # folded
    compact: str      # folded, without whitespace
    tokens: frozenset
    origin: str = "archive"   # archive | reference (the learning set, e.g. the old Paperless files)


class Corpus:
    """All filed documents with their text, prepared for rule matching."""

    def __init__(self, docs: list[Doc]):
        self.docs = docs
        self.by_folder: dict[str, list[Doc]] = {}
        for d in docs:
            self.by_folder.setdefault(d.folder, []).append(d)
        self.df: Counter = Counter()
        for d in docs:
            self.df.update(d.tokens)

    @classmethod
    def load(cls, index: Index, reference: Index | None = None,
             mapping: dict[tuple[str, str], tuple[str, str]] | None = None) -> "Corpus":
        """Documents of the archive, plus those of the learning set that are not filed yet.

        Folders of the learning set are translated with ``mapping`` (the import
        plan), so its documents count for the folder they are going to land in.
        """
        docs: list[Doc] = []
        seen: set[str] = set()
        sources = [(index, "archive", None)]
        if reference is not None:
            sources.append((reference, "reference", mapping or {}))
        for source, origin, folder_map in sources:
            with source.connect() as con:
                rows = con.execute(
                    """SELECT f.short_id, f.sha256, f.folder, f.area, f.title, f.doc_date,
                              substr(t.body, 1, ?) AS body
                       FROM files f JOIN texts t ON t.sha256 = f.sha256
                       WHERE length(t.body) > 0
                       GROUP BY f.sha256""",
                    (MATCH_CHARS,),
                ).fetchall()
            for r in rows:
                if r["sha256"] in seen:
                    continue   # already filed in the archive: the archive copy counts
                seen.add(r["sha256"])
                area, folder = r["area"], r["folder"]
                if folder_map is not None:
                    area, folder = folder_map.get((area, folder), (area, folder))
                folded = fold(r["body"])
                docs.append(Doc(
                    idx=len(docs), id=r["short_id"] or r["sha256"][:6], folder=folder, area=area,
                    title=r["title"], date=r["doc_date"], raw=r["body"], text=folded,
                    compact=nospace(folded), tokens=frozenset(_TOKEN_RE.findall(folded[:MINE_CHARS])),
                    origin=origin,
                ))
        return cls(docs)


# -------------------------------------------------------------------- service

class RuleService:
    def __init__(self, path: Path, index: Index):
        self.path = path
        self.index = index
        self._lock = threading.Lock()
        self._corpus: Corpus | None = None
        self._corpus_key: tuple | None = None
        self._corpus_lock = threading.Lock()
        self.generation: dict = {"running": False}
        self.reference: Index | None = None   # learning set, set by the app
        self.mapping = None                   # callable -> {(area, folder): (area, folder)}

    # ---------------------------------------------------------- persistence

    def load(self) -> RuleBook:
        if not self.path.exists():
            return RuleBook()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return RuleBook(
            folders={k: FolderCard(**v) for k, v in raw.get("folders", {}).items()},
            rules=[Rule(**{**r, "conditions": [Condition(**c) for c in r["conditions"]]})
                   for r in raw.get("rules", [])],
        )

    def _save(self, book: RuleBook) -> None:
        data = {
            "version": 1,
            "folders": {k: asdict(v) for k, v in sorted(book.folders.items()) if v.description},
            "rules": [asdict(r) for r in sorted(book.rules, key=lambda r: (r.folder, r.created))],
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    # --------------------------------------------------------------- corpus

    def corpus(self) -> Corpus:
        meta = self.index.meta()
        key: tuple = (str(self.index.archive), meta["last_scan"], meta["texts"]["done"], meta["total"])
        mapping = None
        if self.reference is not None:
            ref = self.reference.meta()
            mapping = self.mapping() if self.mapping else {}
            key += (str(self.reference.archive), ref["last_scan"], ref["texts"]["done"], ref["total"],
                    hash(frozenset(mapping.items())))
        with self._corpus_lock:
            if self._corpus is None or self._corpus_key != key:
                self._corpus = Corpus.load(self.index, self.reference, mapping)
                self._corpus_key = key
            return self._corpus

    def invalidate(self) -> None:
        with self._corpus_lock:
            self._corpus = None

    # -------------------------------------------------------------- editing

    def set_description(self, folder: str, description: str) -> None:
        with self._lock:
            book = self.load()
            book.folders[folder.strip("/")] = FolderCard(description=description.strip()[:2000])
            self._save(book)

    def create(self, folder: str, conditions: list[dict], source: str = "manual", note: str = "",
               label: str = "") -> Rule:
        conds = check_conditions(conditions)
        rule = Rule(id=uuid.uuid4().hex[:8], folder=folder.strip("/"), conditions=conds,
                    source=source if source in ("manual", "suggestion", "ai", "auto", "starter", "learned") else "manual",
                    note=note.strip()[:200], created=time.strftime("%Y-%m-%dT%H:%M:%S"), label=label.strip()[:120])
        with self._lock:
            book = self.load()
            book.rules.append(rule)
            self._save(book)
        return rule

    def update(self, rule_id: str, conditions: list[dict] | None = None, enabled: bool | None = None,
               note: str | None = None, folder: str | None = None) -> Rule:
        with self._lock:
            book = self.load()
            rule = next((r for r in book.rules if r.id == rule_id), None)
            if not rule:
                raise RuleError("unknown rule")
            if conditions is not None:
                rule.conditions = check_conditions(conditions)
            if enabled is not None:
                rule.enabled = enabled
            if note is not None:
                rule.note = note.strip()[:200]
            if folder is not None:
                rule.folder = folder.strip("/")
            self._save(book)
            return rule

    def rename_folder(self, old: str, new: str) -> int:
        """Keep rules and descriptions attached when a folder is renamed or moved."""
        def move(path: str) -> str:
            return new + path[len(old):] if path == old or path.startswith(old + "/") else path
        with self._lock:
            book = self.load()
            changed = 0
            for r in book.rules:
                if move(r.folder) != r.folder:
                    r.folder = move(r.folder)
                    changed += 1
            book.folders = {move(k): v for k, v in book.folders.items()}
            self._save(book)
        return changed

    def remap(self, mapping: dict[str, str]) -> int:
        """Point rules and folder cards to new folder names (exact folders, not subtrees)."""
        mapping = {k: v for k, v in mapping.items() if k and v and k != v}
        with self._lock:
            book = self.load()
            changed = 0
            for r in book.rules:
                if r.folder in mapping:
                    r.folder = mapping[r.folder]
                    changed += 1
            cards: dict[str, FolderCard] = {}
            for k, v in book.folders.items():
                target = mapping.get(k, k)
                if target in cards and cards[target].description:
                    continue
                cards[target] = v
            book.folders = cards
            self._save(book)
        return changed

    def delete(self, rule_id: str) -> None:
        with self._lock:
            book = self.load()
            before = len(book.rules)
            book.rules = [r for r in book.rules if r.id != rule_id]
            if len(book.rules) == before:
                raise RuleError("unknown rule")
            self._save(book)

    # ----------------------------------------------------------- evaluation

    def evaluate(self, folder: str, conditions: list[Condition]) -> dict:
        """Measure conditions against the filed documents."""
        folder = folder.strip("/")
        corpus = self.corpus()
        preds = [compile_condition(c) for c in conditions]
        inside_total = len(corpus.by_folder.get(folder, []))
        hits_in, outside, missed, examples = 0, [], [], []
        for d in corpus.docs:
            hit = all(p(d) for p in preds)
            if d.folder == folder:
                if hit:
                    hits_in += 1
                    if d.origin == "archive":
                        examples.append(d)
                else:
                    missed.append(d)
            elif hit:
                outside.append(d)
        return {
            "inside": hits_in,
            "inside_total": inside_total,
            "outside": len(outside),
            "precision": round(hits_in / (hits_in + len(outside)), 3) if hits_in + len(outside) else None,
            "outside_docs": [_brief(d) for d in outside[:SAMPLE]],
            "missed_docs": [_brief(d) for d in missed[:SAMPLE]],
            "examples": [_brief(d) for d in sorted(examples, key=lambda d: d.date or "", reverse=True)[:3]],
            "grade": ("green" if hits_in and not outside else
                      "yellow" if hits_in and len(outside) / (hits_in + len(outside)) <= 0.1 else "red"),
        }

    def folder_view(self, folder: str) -> dict:
        folder = folder.strip("/")
        book = self.load()
        rules = [r for r in book.rules if r.folder == folder]
        corpus = self.corpus()
        return {
            "folder": folder,
            "description": book.folders.get(folder, FolderCard()).description,
            "doc_count": len(corpus.by_folder.get(folder, [])),
            "rules": [{**asdict(r), "stats": self.evaluate(folder, r.conditions)} for r in rules],
        }

    def overview(self) -> dict:
        book = self.load()
        counts = Counter(r.folder for r in book.rules)
        corpus = self.corpus()
        return {
            "rule_count": len(book.rules),
            "docs": {f: len(d) for f, d in corpus.by_folder.items()},
            "reference": sum(1 for d in corpus.docs if d.origin == "reference"),
            "folders": {f: {"rules": counts.get(f, 0),
                            "description": bool(book.folders.get(f, FolderCard()).description)}
                        for f in set(counts) | set(book.folders)},
        }

    def matcher(self):
        """A function text -> rule hits, with all enabled rules compiled once."""
        compiled = []
        for r in self.load().rules:
            if not r.enabled:
                continue
            try:
                compiled.append((r, [compile_condition(c) for c in r.conditions]))
            except RuleError:
                continue

        def run(text: str) -> list[dict]:
            folded = fold(text[:MATCH_CHARS])
            doc = Doc(-1, "", "", "", "", None, text[:MATCH_CHARS], folded, nospace(folded), frozenset())
            return [{"rule": r.id, "folder": r.folder, "source": r.source,
                     "conditions": [asdict(c) for c in r.conditions]}
                    for r, preds in compiled if all(p(doc) for p in preds)]
        return run

    def match(self, text: str, rules: list[Rule] | None = None) -> list[dict]:
        """Which enabled rules fire for a text (used by the inbox)."""
        folded = fold(text[:MATCH_CHARS])
        doc = Doc(-1, "", "", "", "", None, text[:MATCH_CHARS], folded, nospace(folded), frozenset())
        hits = []
        for r in (rules if rules is not None else self.load().rules):
            try:
                if r.enabled and all(compile_condition(c)(doc) for c in r.conditions):
                    hits.append({"rule": r.id, "folder": r.folder, "source": r.source,
                                 "conditions": [asdict(c) for c in r.conditions]})
            except RuleError:
                continue
        return hits

    # ------------------------------------------------------ shipped rules

    def _known(self) -> set[tuple]:
        return {(r.folder, tuple(sorted((c.type, fold(c.value)) for c in r.conditions)))
                for r in self.load().rules}

    def install_starter(self) -> int:
        """Add the shipped rules as they are (for the starter folders)."""
        from .starter import starter_rules
        known, added = self._known(), 0
        for folder, conds in starter_rules():
            if (folder, tuple(sorted((c["type"], fold(c["value"])) for c in conds))) in known:
                continue
            self.create(folder, conds, source="starter", note="Standardregel")
            added += 1
        return added

    def adapt_starter(self, min_hits: int = 3, min_precision: float = 0.8, dry_run: bool = False) -> dict:
        """Move each shipped rule to the folder of this archive where it finds its documents.

        Rules that hit too few documents or spread over several folders are left out.
        """
        from .starter import starter_rules
        corpus = self.corpus()
        known = self._known()
        added, skipped = [], 0
        for _folder, conds in starter_rules():
            preds = [compile_condition(Condition(**c)) for c in conds]
            hits = Counter(d.folder for d in corpus.docs if all(p(d) for p in preds))
            total = sum(hits.values())
            if not total:
                skipped += 1
                continue
            folder, n = hits.most_common(1)[0]
            if not folder or n < min_hits or n / total < min_precision:
                skipped += 1
                continue
            key = (folder, tuple(sorted((c["type"], fold(c["value"])) for c in conds)))
            if key in known:
                continue
            if not dry_run:
                self.create(folder, conds, source="starter", note=f"Standardregel, angepasst: {n} von {total} Treffern")
            known.add(key)
            added.append({"folder": folder, "conditions": conds, "inside": n, "outside": total - n})
        return {"added": len(added), "skipped": skipped, "rules": added}

    # ------------------------------------------------- generate from archive

    def generate_all(self, min_docs: int = 2, max_rules: int = 3, target_coverage: float = 0.9) -> dict:
        """Create rules for every folder from the filed documents – no AI, no outsiders allowed.

        Per folder, suggestions are taken greedily until they cover ``target_coverage``
        of its documents or ``max_rules`` is reached. Folders that already have rules
        are skipped, so the run can be repeated safely.
        """
        if self.generation.get("running"):
            raise RuleError("generation already running")
        corpus = self.corpus()
        have = {r.folder for r in self.load().rules}
        todo = [f for f, docs in corpus.by_folder.items() if f and len(docs) >= min_docs and f not in have]
        todo.sort(key=lambda f: -len(corpus.by_folder[f]))
        self.generation = {"running": True, "done": 0, "total": len(todo), "rules": 0, "covered": 0,
                           "folders_with_rules": 0, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
        try:
            for folder in todo:
                docs = corpus.by_folder[folder]
                got: set[int] = set()
                picked = 0
                for s in self.suggest(folder, limit=15, min_precision=1.0):
                    conds = [Condition(**c) for c in s["conditions"]]
                    preds = [compile_condition(c) for c in conds]
                    hits = {d.idx for d in docs if all(p(d) for p in preds)}
                    if not hits - got:
                        continue
                    self.create(folder, s["conditions"], source="auto",
                                note=f"aus dem Bestand: {s['inside']} von {s['inside_total']}")
                    got |= hits
                    picked += 1
                    if len(got) >= target_coverage * len(docs) or picked >= max_rules:
                        break
                g = self.generation
                g["done"] += 1
                g["rules"] += picked
                g["covered"] += len(got)
                g["folders_with_rules"] += 1 if picked else 0
        finally:
            self.generation["running"] = False
            self.generation["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        return self.generation

    # ------------------------------------------------------------ AI rules

    def ai_suggest(self, folder: str, ai, excluded_areas: list[str]) -> dict:
        """Let the configured AI propose rules, then measure each one against the archive."""
        folder = folder.strip("/")
        corpus = self.corpus()
        own = corpus.by_folder.get(folder, [])
        if not own:
            raise RuleError("folder has no documents of its own")
        docs = [d for d in own if d.area not in excluded_areas]
        if not docs:
            raise RuleError("no documents that may be sent to the AI")
        # newest first, spread over the folder
        docs.sort(key=lambda d: d.date or "", reverse=True)
        step = max(1, len(docs) // AI_SAMPLES)
        samples = docs[::step][:AI_SAMPLES]
        siblings = sorted({d.folder for d in corpus.docs if d.folder and d.folder != folder
                           and d.folder.split("/")[0] == folder.split("/")[0]})
        description = self.load().folders.get(folder, FolderCard()).description
        completion = ai.complete(AI_SYSTEM, _ai_prompt(folder, description, samples, siblings),
                                 max_tokens=4000, effort="medium")
        results = []
        for raw in _parse_ai_rules(completion.text):
            try:
                conds = check_conditions(raw.get("conditions") or [])
            except RuleError:
                continue
            stats = self.evaluate(folder, conds)
            results.append({"conditions": [asdict(c) for c in conds], "kind": "ai",
                            "reason": str(raw.get("reason", ""))[:300],
                            "inside": stats["inside"], "inside_total": stats["inside_total"],
                            "outside": stats["outside"], "outside_docs": stats["outside_docs"]})
        results.sort(key=lambda r: -(r["inside"] - 3 * r["outside"]))
        return {"suggestions": results, "model": completion.model, "cost": round(completion.cost, 4),
                "samples": len(samples), "seconds": completion.seconds}

    # ----------------------------------------------------------- suggestions

    def suggest(self, folder: str, limit: int = 12, min_precision: float = 0.9) -> list[dict]:
        """Conditions that find this folder's documents and (almost) nothing else – no AI.

        Candidates are scored on token sets first (fast), only the best ones are
        measured exactly. Near misses are kept on purpose: an outsider is often a
        misfiled document.
        """
        folder = folder.strip("/")
        corpus = self.corpus()
        docs = corpus.by_folder.get(folder, [])
        n = len(docs)
        if n == 0:
            return []
        existing = {tuple(sorted((c.type, fold(c.value)) for c in r.conditions))
                    for r in self.load().rules if r.folder == folder}
        scored: list[tuple[float, list[Condition], str]] = []

        def consider(conds: list[Condition], kind: str, inside: int, outside: int) -> None:
            if inside == 0 or inside / (inside + outside) < min_precision:
                return
            if kind != "id" and inside < 2:
                return
            scored.append((inside - 3 * outside, conds, kind))

        # 1) lasting identifiers found in this folder: contract numbers, IBANs, number plates …
        ids = Counter()
        for d in docs:
            found = {nospace(m.group(0)) for m in _IBAN_RE.finditer(d.raw)}
            found |= {nospace(m.group(1)).strip(".-/") for m in _LABELED_RE.finditer(d.raw)}
            ids.update(i for i in found if _good_identifier(i))
        for value, _ in ids.most_common(25):
            needle = fold(value)
            inside = sum(1 for d in docs if needle in d.compact)
            outside = sum(1 for d in corpus.docs if d.folder != folder and needle in d.compact)
            consider([Condition("id", value)], "id", inside, outside)

        # 2) words typical for this folder
        local = Counter()
        for d in docs:
            local.update(d.tokens)
        for token, inside in local.most_common(400):
            if inside < 2:
                break
            consider([Condition("contains", token)], "word", inside, corpus.df[token] - inside)

        # 3) pairs of frequent words that are not exclusive on their own
        frequent = [tok for tok, c in local.most_common(80)
                    if c >= max(2, int(n * 0.5)) and corpus.df[tok] < len(corpus.docs) * 0.25][:25]
        others = [d for d in corpus.docs if d.folder != folder]
        for i, a in enumerate(frequent):
            for b in frequent[i + 1:]:
                inside = sum(1 for d in docs if a in d.tokens and b in d.tokens)
                if inside < max(2, n * 0.5):
                    continue
                outside = sum(1 for d in others if a in d.tokens and b in d.tokens)
                consider([Condition("contains", a), Condition("contains", b)], "pair", inside, outside)

        scored.sort(key=lambda s: (-s[0], len(s[1]), s[2] != "id"))
        results, seen = [], set()
        for _, conds, kind in scored:
            key = tuple(sorted((c.type, fold(c.value)) for c in conds))
            if key in seen or key in existing:
                continue
            seen.add(key)
            stats = self.evaluate(folder, conds)   # exact numbers on the full text
            if not stats["inside"] or (stats["precision"] or 0) < min_precision:
                continue
            results.append({"conditions": [asdict(c) for c in conds], "kind": kind,
                            "inside": stats["inside"], "inside_total": stats["inside_total"],
                            "outside": stats["outside"], "outside_docs": stats["outside_docs"]})
            if len(results) >= limit:
                break
        return results


AI_SYSTEM = """You write filing rules for a family document archive (mostly German letters,
invoices, contracts and statements). A rule is a list of conditions that must ALL match the
document text. Condition types:
- "contains": a word or phrase that literally appears in the text (case-insensitive)
- "id": a lasting identifier such as a contract, customer or policy number, IBAN or number plate
  (spaces are ignored when matching)
- "regex": a Python regular expression, only when nothing simpler works

Goal: rules that catch the documents of ONE target folder and nothing else in the archive.
Prefer sender names, lasting identifiers and terms specific to this kind of document. Avoid
words that occur in many unrelated letters (greetings, dates, legal boilerplate, the
recipient's own name or address). Two conditions combined are often more precise than one.
Every value must be copied exactly as it appears in the sample texts.

Answer with JSON only, no prose:
{"rules": [{"conditions": [{"type": "contains", "value": "..."}], "reason": "short German explanation"}]}
Give at most 6 rules, best first."""

AI_SAMPLES = 8
AI_SAMPLE_CHARS = 1800


def _ai_prompt(folder: str, description: str, samples: list[Doc], siblings: list[str]) -> str:
    parts = [f"Target folder: {folder}"]
    if description:
        parts.append(f"Description of the folder: {description}")
    if siblings:
        parts.append("Other folders in the archive that must NOT be matched (examples): " + "; ".join(siblings[:40]))
    for i, d in enumerate(samples, 1):
        parts.append(f"--- Sample document {i}: \"{d.title}\" ---\n{d.raw[:AI_SAMPLE_CHARS]}")
    return "\n\n".join(parts)


def _parse_ai_rules(text: str) -> list[dict]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise RuleError("AI answer contained no JSON")
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise RuleError("AI answer was not valid JSON") from exc
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, list):
        raise RuleError("AI answer had no rules")
    return rules


def _brief(d: Doc) -> dict:
    return {"id": d.id, "title": d.title, "folder": d.folder, "area": d.area, "date": d.date,
            "origin": d.origin}
