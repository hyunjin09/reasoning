from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from piqd.utils.io import read_json


@dataclass(frozen=True)
class MathVerseSample:
    sample_id: str
    sample_index: str
    problem_index: str
    problem_version: str
    image_path: str
    image_reference: str
    question: str
    prompt: str
    answer: str
    question_type: str
    metadata: dict[str, Any]
    question_for_eval: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def resolve_image_path(root: str | Path, image_reference: str) -> Path:
    root = Path(root)
    raw = Path(image_reference)
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.extend([root / image_reference, root / "images" / image_reference])
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(f"could not resolve MathVerse image reference: {image_reference}")


def inspect_mathverse(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"MathVerse path not found: {root}")
    files = sorted(str(path.relative_to(root)) for path in root.glob("*") if path.is_file())
    dirs = sorted(str(path.relative_to(root)) for path in root.glob("*") if path.is_dir())
    data_path = root / "testmini.json"
    data = read_json(data_path)
    first = data[0] if isinstance(data, list) and data else {}
    image_count = sum(1 for _ in (root / "images").glob("**/*") if _.is_file()) if (root / "images").exists() else 0
    return {
        "root": str(root),
        "files": files,
        "directories": dirs,
        "testmini_count": len(data) if isinstance(data, list) else None,
        "first_keys": sorted(first.keys()),
        "first_sample": first,
        "image_file_count": image_count,
    }


def load_smoke_samples(root: str | Path, limit: int = 10) -> list[MathVerseSample]:
    root = Path(root)
    data = read_json(root / "testmini.json")
    if not isinstance(data, list):
        raise ValueError("MathVerse testmini.json must contain a list")
    samples: list[MathVerseSample] = []
    for row in data:
        if len(samples) >= limit:
            break
        image_ref = str(row.get("image") or "")
        if not image_ref:
            continue
        try:
            image_path = resolve_image_path(root, image_ref)
        except FileNotFoundError:
            continue
        sample_index = str(row.get("sample_index") or len(samples))
        problem_index = str(row.get("problem_index") or sample_index)
        problem_version = str(row.get("problem_version") or "")
        prompt = str(row.get("query_cot") or row.get("query_wo") or row.get("question") or "")
        sample_id = f"{problem_index}:{sample_index}:{problem_version}".replace(" ", "_")
        samples.append(
            MathVerseSample(
                sample_id=sample_id,
                sample_index=sample_index,
                problem_index=problem_index,
                problem_version=problem_version,
                image_path=str(image_path),
                image_reference=image_ref,
                question=str(row.get("question") or ""),
                prompt=prompt,
                answer=str(row.get("answer") or ""),
                question_type=str(row.get("question_type") or ""),
                metadata=dict(row.get("metadata") or {}),
                question_for_eval=str(row.get("question_for_eval") or row.get("question") or ""),
            )
        )
    return samples

