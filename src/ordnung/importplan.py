"""Import planner: where each folder of the current archive should go.

Nothing is copied here. The planner looks at the folders of the current
(source) archive – today the Paperless originals – and proposes a target path
for each one, cleaning up on the way:

* doubled levels   ``Finanzamt/Finanzamt/Belege``   → ``Finanzamt/Belege``
* spelling variants ``Kontoauszüge`` next to ``kontoauszüge`` → one folder
* files without an area (loose files in the archive root) are flagged
* folders with a single document are pointed out (merge into the parent?)

Only the user's own decisions are stored (``import-plan.json``); suggestions
are recomputed from the index every time.
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .index import Index, fold


@dataclass
class Decision:
    target_area: str
    target_folder: str
    confirmed: bool = False
    changed: str = ""


@dataclass
class Plan:
    decisions: dict[str, Decision] = field(default_factory=dict)   # "area|folder" -> decision


def key(area: str, folder: str) -> str:
    return f"{area}|{folder}"


def collapse_doubles(folder: str) -> str:
    parts: list[str] = []
    for part in folder.split("/"):
        if parts and fold(parts[-1]) == fold(part):
            continue
        parts.append(part)
    return "/".join(parts)


class ImportPlanner:
    def __init__(self, path: Path, index: Index):
        self.path = path
        self.index = index
        self._lock = threading.Lock()

    # ---------------------------------------------------------- persistence

    def load(self) -> Plan:
        if not self.path.exists():
            return Plan()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return Plan(decisions={k: Decision(**v) for k, v in raw.get("decisions", {}).items()})

    def _save(self, plan: Plan) -> None:
        data = {"version": 1, "decisions": {k: asdict(v) for k, v in sorted(plan.decisions.items())}}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    # ---------------------------------------------------------- suggestions

    def _folders(self) -> list[tuple[str, str, int]]:
        with self.index.connect() as con:
            return [(r[0], r[1], r[2]) for r in con.execute(
                "SELECT area, folder, COUNT(*) FROM files GROUP BY area, folder ORDER BY area, folder")]

    def suggestions(self) -> list[dict]:
        folders = self._folders()
        # preferred spelling per folded path: the variant with the most documents
        spelling: dict[str, tuple[int, str]] = {}
        for _area, folder, n in folders:
            cleaned = collapse_doubles(folder)
            k = fold(cleaned)
            if k not in spelling or n > spelling[k][0]:
                spelling[k] = (n, cleaned)
        # the same folder name in several places of one area (e.g. T-Roc under Auto and Auto/HUK24)
        places: dict[tuple[str, str], set[str]] = {}
        for area, folder, _n in folders:
            if folder:
                places.setdefault((area, fold(folder.split("/")[-1])), set()).add(folder)
        rows = []
        for area, folder, n in folders:
            reasons: list[str] = []
            target = collapse_doubles(folder)
            if target != folder:
                reasons.append("double")
            preferred = spelling[fold(target)][1]
            if preferred != target:
                target = preferred
                reasons.append("spelling")
            hints: list[str] = []
            if not area:
                hints.append("no_area")
            if n == 1 and folder.count("/") >= 1:
                hints.append("single")
            same_name = places.get((area, fold(folder.split("/")[-1]))) if folder else None
            if same_name and len(same_name) > 1:
                hints.append("scattered")
            rows.append({"area": area, "folder": folder, "count": n,
                         "suggested_area": area, "suggested_folder": target,
                         "reasons": reasons, "hints": hints,
                         "same_name": sorted(same_name - {folder}) if same_name and len(same_name) > 1 else []})
        return rows

    # ----------------------------------------------------------------- plan

    def view(self) -> dict:
        plan = self.load()
        rows = []
        for row in self.suggestions():
            decision = plan.decisions.get(key(row["area"], row["folder"]))
            if decision:
                row.update(target_area=decision.target_area, target_folder=decision.target_folder,
                           confirmed=decision.confirmed, manual=True)
            else:
                row.update(target_area=row["suggested_area"], target_folder=row["suggested_folder"],
                           confirmed=False, manual=False)
            row["moves"] = (row["target_area"], row["target_folder"]) != (row["area"], row["folder"])
            rows.append(row)
        targets = {(r["target_area"], r["target_folder"]) for r in rows if r["target_area"]}
        summary = {
            "documents": sum(r["count"] for r in rows),
            "folders_before": len(rows),
            "folders_after": len(targets),
            "moves": sum(1 for r in rows if r["moves"]),
            "moved_documents": sum(r["count"] for r in rows if r["moves"]),
            "no_area": sum(r["count"] for r in rows if not r["target_area"]),
            "confirmed": sum(1 for r in rows if r["confirmed"]),
            "open": sum(1 for r in rows if not r["confirmed"]),
        }
        return {"rows": rows, "summary": summary}

    def decide(self, area: str, folder: str, target_area: str, target_folder: str,
               confirmed: bool = True) -> None:
        target_folder = "/".join(p.strip() for p in target_folder.strip().strip("/").split("/") if p.strip())
        if any(p in (".", "..") for p in target_folder.split("/")):
            raise ValueError("invalid folder name")
        with self._lock:
            plan = self.load()
            plan.decisions[key(area, folder)] = Decision(
                target_area=target_area.strip(), target_folder=target_folder, confirmed=confirmed,
                changed=time.strftime("%Y-%m-%dT%H:%M:%S"))
            self._save(plan)

    def reset(self, area: str, folder: str) -> None:
        with self._lock:
            plan = self.load()
            plan.decisions.pop(key(area, folder), None)
            self._save(plan)

    def rename_target(self, old: str, new: str) -> None:
        with self._lock:
            plan = self.load()
            for d in plan.decisions.values():
                if d.target_folder == old or d.target_folder.startswith(old + "/"):
                    d.target_folder = new + d.target_folder[len(old):]
            self._save(plan)

    def confirm_all(self, only_unchanged: bool = False) -> int:
        """Confirm every row as currently shown (suggestion or own decision)."""
        view = self.view()
        count = 0
        with self._lock:
            plan = self.load()
            for r in view["rows"]:
                if r["confirmed"] or not r["target_area"]:
                    continue
                if only_unchanged and r["moves"]:
                    continue
                plan.decisions[key(r["area"], r["folder"])] = Decision(
                    target_area=r["target_area"], target_folder=r["target_folder"], confirmed=True,
                    changed=time.strftime("%Y-%m-%dT%H:%M:%S"))
                count += 1
            self._save(plan)
        return count

    def mapping(self) -> dict[tuple[str, str], tuple[str, str]]:
        """(area, folder) of the source -> (area, folder) in the new archive, as shown."""
        return {(r["area"], r["folder"]): (r["target_area"] or r["area"], r["target_folder"])
                for r in self.view()["rows"]}

    def folder_mapping(self) -> dict[str, str]:
        """Old folder -> new folder, ignoring areas (the target used by most documents)."""
        votes: dict[str, dict[str, int]] = {}
        for r in self.view()["rows"]:
            if r["folder"]:
                bucket = votes.setdefault(r["folder"], {})
                bucket[r["target_folder"]] = bucket.get(r["target_folder"], 0) + r["count"]
        return {old: max(targets.items(), key=lambda kv: kv[1])[0] for old, targets in votes.items()}

    def target_tree(self) -> dict:
        """The merged folder tree as it would look after the import."""
        root = {"name": "", "path": "", "count": 0, "children": {}}
        for r in self.view()["rows"]:
            if not r["target_area"]:
                continue
            node = root
            node["count"] += r["count"]
            path = []
            for part in [p for p in r["target_folder"].split("/") if p]:
                path.append(part)
                node = node["children"].setdefault(part, {"name": part, "path": "/".join(path),
                                                          "count": 0, "children": {}})
                node["count"] += r["count"]

        def finish(n):
            return {"name": n["name"], "path": n["path"], "count": n["count"],
                    "children": [finish(c) for c in sorted(n["children"].values(), key=lambda c: fold(c["name"]))]}
        return finish(root)
