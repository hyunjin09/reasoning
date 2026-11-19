"""Source-only pointer provenance; no image, gold, model or scorer imports."""
import hashlib
import re
import unicodedata

PROPERTIES = ("count", "label", "position", "relation", "layout", "color",
              "value", "length", "angle", "ordering", "connectivity", "text", "shape")
SCOPES = ("local", "global", "unknown")
NONE_REASONS = ("already_supplied", "no_visual_need", "uncertain_demand")
WORDS = dict(zip(
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split(),
    map(str, range(21))))
WORDS.update(dict(zip("thirty forty fifty sixty seventy eighty ninety".split(),
                      map(str, range(30, 100, 10)))))
COLORS = set("red orange yellow green blue purple violet pink black white gray grey brown cyan magenta".split())
ASSERTION = re.compile(r"\b(is|are|was|were|has|have|equals|therefore|because)\b|"
                       r"\b(the answer|correct option|must be|equal to)\b|"
                       r"\b(ignore|disregard|override|obey|instructions?)\b|[=<>]", re.I)
ROMAN = re.compile(r"\b(?:II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX)\b")
IMAGE = re.compile(r"\bimage\d+\b", re.I)
NUMBER = re.compile(r"(?<!\d)[+-]?\d+(?:\.\d+)?(?:st|nd|rd|th)?", re.I)


def build_catalog(question, prefix):
    catalog = []
    for source, raw, tag in [("question", question, "Q"), ("prefix", prefix, "P")]:
        offset = 0
        index = 0
        for line in raw.splitlines(keepends=True):
            words = list(re.finditer(r"\S+", line))
            for start in range(0, len(words), 20):
                a = offset + words[start].start()
                b = offset + words[min(start + 19, len(words) - 1)].end()
                text = raw[a:b]
                catalog.append(dict(id=f"{tag}{index:03}", source=source,
                                    start=a, end=b, text=text,
                                    sha256=hashlib.sha256(text.encode()).hexdigest()))
                index += 1
            offset += len(line)
    return catalog


def numeric_lexemes(text):
    text = IMAGE.sub("", unicodedata.normalize("NFKC", text))
    found = set()
    for match in NUMBER.finditer(text):
        value = re.sub(r"(st|nd|rd|th)$", "", match.group(), flags=re.I)
        found.add(value)
    for word in re.findall(r"\b[a-z]+\b", text.lower()):
        if word in WORDS:
            found.add(WORDS[word])
    return found


def validate_query(record, catalog):
    if not isinstance(record, dict):
        return False, "NOT_OBJECT"
    if record.get("answer_value", "MISSING") is not None:
        return False, "VALUE_SLOT_NOT_NULL"
    if record.get("status") == "NONE":
        ok = (set(record) == {"status", "reason", "answer_value"}
              and isinstance(record["reason"], str)
              and record["reason"] in NONE_REASONS)
        return ok, "NONE" if ok else "SCHEMA"
    if (set(record) != {"status", "target", "property", "scope", "source_refs", "answer_value"}
            or record.get("status") != "QUERY"):
        return False, "SCHEMA"
    target = record["target"]
    if not isinstance(target, str) or not 1 <= len(target.strip()) <= 240:
        return False, "TARGET_TEXT"
    guard_target = re.sub(r"<image\d+>", "", target)
    if "\n" in target or "\r" in target or ASSERTION.search(guard_target):
        return False, "ASSERTION_OR_NARRATIVE"
    if (not isinstance(record["property"], str) or record["property"] not in PROPERTIES
            or not isinstance(record["scope"], str) or record["scope"] not in SCOPES):
        return False, "SCHEMA"
    refs = record["source_refs"]
    if (not isinstance(refs, list) or not 1 <= len(refs) <= 8
            or not all(isinstance(x, str) for x in refs) or len(set(refs)) != len(refs)):
        return False, "REFERENCES"
    index = {r["id"]: r for r in catalog}
    if not all(ref in index for ref in refs):
        return False, "UNKNOWN_REFERENCE"
    selected = [index[ref] for ref in refs]
    if any(hashlib.sha256(s["text"].encode()).hexdigest() != s["sha256"] for s in selected):
        return False, "CATALOG_HASH"
    text = " ".join(s["text"] for s in selected)
    question = " ".join(s["text"] for s in catalog if s["source"] == "question")
    target_norm = unicodedata.normalize("NFKC", target)
    if not set(s.lower() for s in IMAGE.findall(target_norm)) <= set(s.lower() for s in IMAGE.findall(question)):
        return False, "UNKNOWN_STRUCTURAL_IMAGE_ID"
    if not set(ROMAN.findall(target)) <= set(ROMAN.findall(text)):
        return False, "UNSUPPORTED_ROMAN_IDENTIFIER"
    if not numeric_lexemes(target) <= numeric_lexemes(text):
        return False, "UNSUPPORTED_NUMBER"
    colors = set(re.findall(r"\b[a-z]+\b", target.lower())) & COLORS
    if not colors <= set(re.findall(r"\b[a-z]+\b", text.lower())):
        return False, "UNSUPPORTED_COLOR_DESCRIPTOR"
    return True, "PROVENANCE_VALID_SEMANTICS_UNCERTIFIED"


def compile_query(record, catalog):
    ok, reason = validate_query(record, catalog)
    if not ok:
        raise ValueError(reason)
    if record["status"] == "NONE":
        return dict(record)
    selected = {s["id"]: s for s in catalog}
    return dict(
        record,
        query=f"What is the {record['property']} of {record['target']} in the original image?",
        source_spans=[dict(selected[s]) for s in record["source_refs"]],
        provenance_notice="Exact spans from the supplied question or possibly mistaken prefix; "
                          "these are provenance, not certified visual observations.")


def object_schema(properties):
    return dict(type="object", properties=properties, required=list(properties),
                additionalProperties=False)


QUERY_SCHEMA = {
    "anyOf": [
        object_schema(dict(
            status={"const": "QUERY"}, target={"type": "string", "minLength": 1, "maxLength": 240},
            property={"enum": list(PROPERTIES)}, scope={"enum": list(SCOPES)},
            source_refs={"type": "array", "minItems": 1, "maxItems": 8,
                         "items": {"type": "string"}},
            answer_value={"type": "null"})),
        object_schema(dict(status={"const": "NONE"}, reason={"enum": list(NONE_REASONS)},
                           answer_value={"type": "null"})),
    ]
}


def query_prompt(row):
    catalog = build_catalog(row["question"], row["prefix"])
    listing = "\n".join(f"{s['id']} [{s['source']}] {s['text']}" for s in catalog)
    return (
        "You are pausing a solver at its current reasoning prefix. Identify exactly ONE "
        "new visual fact needed by its next reasoning step. Use only the supplied question "
        "and prefix. Do not solve the problem or guess the requested value. "
        "Choose a target noun phrase and a property to read. Select exact source_refs from "
        "the host catalog below; do not write quotations or invent reference IDs. "
        "The prefix may be mistaken. A source reference does not certify its truth. "
        "Keep target value-free: do not state what its property equals or insert a guessed "
        "number/color. Source-given numbers and image identifiers may address a source, "
        "but numbers in the target must occur in cited spans. Omit unneeded numbers. "
        "Use NONE if no new visual fact is needed; do not force QUERY.\n"
        'QUERY example: {"status":"QUERY","target":"marked point",'
        '"property":"label","scope":"unknown","source_refs":["Q000"],"answer_value":null}\n'
        f"Properties: {', '.join(PROPERTIES)}. Scope: local, global, unknown.\n"
        'NONE example: {"status":"NONE","reason":"no_visual_need","answer_value":null}\n'
        f"NONE reasons: {', '.join(NONE_REASONS)}.\n"
        "Return the compact JSON object directly; no explanation or additional reasoning.\n\n"
        "Source catalog (question first, then current prefix; exact supplied text):\n" + listing)


# Qwen3-VL native coordinate transport, converted once into the unchanged crop API.
from copy import deepcopy
from scripts.stage14d1.contracts import validate_address, helper_prompt as legacy_helper_prompt
from scripts.stage14d1.contracts_v3 import SCHEMAS as LEGACY_SCHEMAS
SCHEMAS = deepcopy(LEGACY_SCHEMAS)
SCHEMAS["query"] = QUERY_SCHEMA
SCHEMAS["locate"]["properties"]["boxes"]["items"]["items"] = {
    "type": "integer", "minimum": 0, "maximum": 1000}


def normalize_address(raw):
    if not isinstance(raw, dict) or set(raw) != {"mode", "boxes", "source_reference", "uncertainty"}:
        raise ValueError("Invalid address schema")
    if not isinstance(raw["source_reference"], str) or raw["uncertainty"] not in ("certain", "uncertain"):
        raise ValueError("Invalid address metadata")
    if not isinstance(raw["boxes"], list):
        raise ValueError("Invalid boxes")
    result = deepcopy(raw)
    boxes = []
    for box in raw["boxes"]:
        if not isinstance(box, list) or len(box) != 4 or not all(type(v) is int and 0 <= v <= 1000 for v in box):
            raise ValueError("Coordinates must be integers on the declared 0..1000 scale")
        boxes.append([v / 1000 for v in box])
    result["boxes"] = boxes
    if not validate_address(result, 1000, 1000):
        raise ValueError("Invalid area or mode/cardinality")
    return result


def helper_prompt(row, kind, query=None, address=None):
    text = legacy_helper_prompt(row, kind, query, address)
    if kind == "locate":
        text = text.replace(
            "boxes are normalized [xmin,ymin,xmax,ymax] in the original full image",
            "boxes are integer [xmin,ymin,xmax,ymax] relative coordinates from 0 to 1000 "
            "in the original full image (Qwen3-VL coordinate convention)")
    return text
