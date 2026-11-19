"""Seal main-agent answer extraction without loading gold or dose mapping."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('outputs/stage8c_v3/v1/annotations/dev_extraction_v1')


def main():
    packet_path = ROOT / 'packets.json'
    packet = json.loads(packet_path.read_text())
    wrappers = {
        1:'A', 2:'C', 8:'C', 12:'A', 13:'C', 16:'C', 23:'C', 25:'C',
        28:'A', 30:'E', 32:'B', 34:'B', 35:'C', 41:'C', 48:'C', 53:'B',
        54:'A', 57:'C', 67:'A',
    }
    explicit = {
        4: ('C', '**C**', 'Final answer C; remove Markdown emphasis.'),
        9: ('B', '**B**', 'Explicit concluding option B.'),
        14: ('16', r'\boxed{16}', 'Preserve final literal 16; do not infer an option.'),
        18: ('C', '**C**', 'Final answer C; remove Markdown emphasis.'),
        39: ('15/4', 'But the correct answer is 15/4.', 'Last explicit adopted answer is 15/4. Later attempted derivation yields 2.25, explicitly rejected as not an option, without replacing this answer. Preserve the emitted answer despite unfinished verification.'),
        64: ('A', 'This matches **Option A**.', 'The final boxed value is explicitly identified as Option A; retain the emitted choice.'),
        65: ('B', '**B**', 'Explicit concluding option B.'),
        70: ('C', '**Answer: C**', 'Explicit concluding option C.'),
        75: ('16', r'\boxed{16}', 'Preserve final literal 16; do not infer an option.'),
    }
    groups = [
        ([3,5,45,71], 'Post-think clock candidates are repeatedly rejected; the capped tail remains in alternating trials, with no adopted time.'),
        ([6,11,68,73], 'Likely-B proposal remains tentative, followed by revised incompatible area calculations and an unfinished Total; no adopted answer.'),
        ([7,37,77], 'Earlier five-grid candidate is followed by an explicit critical-error correction; later cases are enumerated but no new completed total is emitted. Tail starts another unfinished case.'),
        ([10,29,43,72], 'Angle-sum formulas are challenged by conflicting limiting/numeric checks; tail is an unfinished numerical series, with no adopted requested answer.'),
        ([15,50,58,61], 'Square geometry/optimization remains under revision; tail is an unfinished coordinate feasibility check, not an adopted minimum area.'),
        ([17,49,69], 'Folded-triangle coordinates are repeatedly rejected and reset; no adopted area at cap.'),
        ([19,27,47,74], 'Automatic extraction merely restates the requested a-b-sqrt(c) form. Later union-area proposal is questioned and revised; no adopted requested sum.'),
        ([20,44,59,66], 'Piecewise area formulas are explicitly rejected; response ends in an unfinished integral, without the requested volume.'),
        ([21,52,55,62], 'Entire post-think section only explains the petal process and begins optimization; cap interrupts before a minimum is stated.'),
        ([22,31,46,63], 'Small-grid examples and general edge formulas are explored/revised; no completed value for the requested 2018-square problem.'),
        ([24,26,56,76], 'Folded-square perimeter candidate is explicitly rejected as not an option; new coordinate derivation is unfinished at cap.'),
        ([33,38,40,78], 'Area ratios are restated with an undetermined scale; tail continues deriving the square area without an adopted value.'),
        ([36,42], 'Column-sum candidates are contradicted by subsequent calculations and the table/formula is restarted; no settled maximum column/result.'),
        ([51], 'Post-think section reaches only an unfinished shoelace calculation; no shaded fraction is stated.'),
        ([60], 'A completed five-configuration proposal is followed by a conflicting enumeration through Config 8 and renewed algebra. No unambiguous final count is adopted.'),
    ]
    unresolved = {n: reason for ns, reason in groups for n in ns}
    assert len(wrappers) + len(explicit) + len(unresolved) == 78
    rows = []
    for p in packet['packets']:
        n = int(p['blind_id'][1:]); body = p['body']
        if n in wrappers:
            value = wrappers[n]; quote = r'\boxed{\text{' + value + '}}'
            reason = 'Final box explicitly selects this option; remove only the LaTeX text wrapper.'
        elif n in explicit:
            value, quote, reason = explicit[n]
        else:
            value = quote = None; reason = unresolved[n]
        span = None
        if value is not None:
            start = body.rfind(quote)
            assert start >= 0, (n, quote)
            start += quote.rfind(value)
            span = [start, start + len(value)]
            assert body[slice(*span)] == value
        rows.append(dict(blind_id=p['blind_id'], extracted=value, literal=value,
            body_span=span, quote=quote, rationale=reason,
            status='extracted' if value is not None else 'declared_unresolvable',
            body_sha256=hashlib.sha256(body.encode()).hexdigest(),
            raw_text_sha256=p['raw_text_sha256']))
    output = dict(at=datetime.now(timezone.utc).isoformat(), labels_sealed=True,
        extraction_review_closed=True, reviewer='main agent, single annotator',
        ground_truth_and_dose_hidden=True, limitation=packet['limitation'],
        review_scope='Final-answer tail and automatic span; ambiguous whole responses additionally reviewed using candidate-marker windows. Not exhaustive semantic annotation.',
        packet_sha256=hashlib.sha256(packet_path.read_bytes()).hexdigest(),
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), rows=rows)
    with (ROOT/'manual_extraction_seal.json').open('x') as f:
        json.dump(output, f, indent=2, ensure_ascii=False); f.write('\n')
    print(json.dumps(dict(reviewed=len(rows), extracted=sum(r['extracted'] is not None for r in rows),
                         declared_unresolvable=sum(r['extracted'] is None for r in rows))))


if __name__ == '__main__':
    main()
