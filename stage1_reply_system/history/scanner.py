"""Scan historical project folders and pair incoming letters with replies."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from .advice import infer_stage, normalize_title

SUPPORTED = {".doc", ".docx", ".pdf"}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_reply(path: Path) -> bool:
    context = "\\".join(path.parts[-4:])
    return bool(re.search(r"复函|回函", path.stem)) and bool(re.search(r"回函|复函", context))


def _is_incoming(path: Path) -> bool:
    if _is_reply(path):
        return False
    context = "\\".join(path.parts[-4:])
    return bool(re.search(r"征求.*意见.*函|报审.*函|申请.*函", path.stem)) or bool(
        re.search(r"报审单位提供资料|报审资料", context)
        and re.search(r"函|报审|申请|征求意见", path.stem)
        and path.suffix.lower() in SUPPORTED
    )


def _project_root(path: Path, scan_root: Path) -> Path:
    relative = path.resolve().relative_to(scan_root.resolve())
    return scan_root / relative.parts[0] if relative.parts else scan_root


def scan_documents(roots: Iterable[str | Path]) -> dict[str, list[dict[str, object]]]:
    incoming: list[dict[str, object]] = []
    replies: list[dict[str, object]] = []
    for raw_root in roots:
        root = Path(raw_root)
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED or path.name.startswith("~$"):
                continue
            role = "reply" if _is_reply(path) else "incoming" if _is_incoming(path) else None
            if not role:
                continue
            item = {
                "path": str(path.resolve()),
                "root": str(root.resolve()),
                "project_root": str(_project_root(path, root).resolve()),
                "stage": infer_stage(str(path)),
                "title_key": normalize_title(path.name),
                "extension": path.suffix.lower(),
                "size": path.stat().st_size,
            }
            (replies if role == "reply" else incoming).append(item)
    return {"incoming": incoming, "replies": replies}


def _char_similarity(left: str, right: str) -> float:
    def grams(value: str) -> set[str]:
        value = re.sub(r"\W", "", value)
        return {value[index:index + 2] for index in range(max(0, len(value) - 1))}

    a, b = grams(left), grams(right)
    return len(a & b) / len(a | b) if a and b else 0.0


def cluster_replies(scan: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    """Cluster editable and stamped variants while retaining separate reply rounds."""
    grouped: dict[tuple[str, str | None], list[dict[str, object]]] = defaultdict(list)
    for reply in scan["replies"]:
        grouped[(str(reply["project_root"]), reply.get("stage"))].append(reply)

    clusters: list[dict[str, object]] = []
    for (project_root, stage), candidates in grouped.items():
        local: list[list[dict[str, object]]] = []
        for candidate in sorted(candidates, key=lambda item: str(item["path"])):
            for cluster in local:
                same_parent = Path(str(candidate["path"])).parent == Path(str(cluster[0]["path"])).parent
                similarity = _char_similarity(str(candidate["title_key"]), str(cluster[0]["title_key"]))
                if same_parent and similarity >= 0.58:
                    cluster.append(candidate)
                    break
            else:
                local.append([candidate])
        for documents in local:
            editable = next((item for ext in (".docx", ".doc") for item in documents if item["extension"] == ext), None)
            official = next((item for item in documents if item["extension"] == ".pdf"), None)
            primary = editable or official or documents[0]
            clusters.append({
                "project_root": project_root,
                "stage": stage,
                "reply_documents": documents,
                "primary_reply": primary,
                "editable_reply": editable,
                "official_reply": official,
            })
    return clusters


def pair_incoming(cluster: dict[str, object], incoming: list[dict[str, object]]) -> dict[str, object] | None:
    candidates = [item for item in incoming if item["project_root"] == cluster["project_root"]]
    if not candidates:
        return None
    reply = cluster["primary_reply"]
    best = None
    best_score = -1.0
    for item in candidates:
        stage_score = 1.0 if item.get("stage") == cluster.get("stage") else 0.25 if not item.get("stage") else 0.0
        title_score = _char_similarity(str(item["title_key"]), str(reply["title_key"]))
        score = 0.65 * stage_score + 0.35 * title_score
        if score > best_score:
            best, best_score = item, score
    return {**best, "pair_score": round(best_score, 4)} if best else None
