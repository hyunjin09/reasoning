"""Record the main agent's ground-truth-blind extraction review decisions."""
import json
from datetime import datetime, timezone
from prepare_block0 import ROOT, digest, save


def main():
    auto = json.loads((ROOT/'audit'/'automatic_extraction_freeze.json').read_text())
    decisions = []
    wrappers = {'2621':'E','108':'A','1038':'C','58':'E','2328':'C','2116':'E',
                '834':'C','2270':'C','1017':'A'}
    explicit = {
        '120': ('6', '**6 units**', '6', 'The concluding difference is explicitly 6 units; remove units and emphasis.'),
        '12': ('10', '**10**', '10', 'The concluding digit sum is explicitly 10; remove emphasis.'),
        '30': ('2', '**tiger** (number 2)', '2', 'The answer identifies tiger by displayed number 2; retain its explicit numeric identifier.'),
        '1177': ('E', '**Answer: E**', 'E', 'Explicit answer E; remove Markdown emphasis.'),
        '2155': ('B', '\\boxed{\\text{B. } \\frac{44}{3}}', 'B', 'Final box explicitly selects B alongside its value; remove formatting.'),
        '21': ('A', '**A**', 'A', 'The final answer explicitly selects A.'),
        '1180': ('D', '**D**', 'D', 'The final answer explicitly selects D.'),
        '1340': ('C', 'option C', 'C', 'The final 45-percent conclusion explicitly identifies option C; preserve that choice.'),
        '2412': ('\\frac{7}{9}', '\\boxed{\\frac{7}{9}}', '\\frac{7}{9}', 'Confirm the automatic final boxed fraction unchanged; the existing numeric-equivalence adapter handles choices.'),
        '1349': ('5', 'Total: 2 + 2 + 1 = 5.', '5', 'The final complete enumeration states five matrices after correcting an earlier four-case count. Subsequent algebra restarts verification without retracting this completed total; preserve the explicit last total despite the cap.'),
    }
    unresolved = {
        '2835':'No final n extraction; reviewed tail is still revising the two-ray recurrence and ends mid-sentence.',
        '1868':'Tail revises incompatible circle centers/radii and ends mid-coordinate computation; no adopted radius is established.',
        '2861':'Tail is still deriving polygon areas; no selected a+b is established.',
        '756':'Repeated Y=8 proposals are followed by explicit impossibility/rejection and more multiplication trials. Do not normalize a provisional Y=8 into an adopted answer.',
        '1176':'Tail tries and rejects domino arrangements and ends in a partial table; no minimum step count is established.',
        '2750':'Tail proposes 8 tentatively and restarts a case enumeration; no unambiguous adopted count is established.',
        '728':'The post-think section identifies one overlapping segment but continues searching other segments and is interrupted; this is not a maximum-common-length answer.',
        '2329':'Earlier E and latest likely-A proposals remain tentative; the latter is immediately tested in an unfinished coordinate calculation, not adopted.',
        '1637':'118 is a candidate construction; the tail continues optimizing general sums and ends mid-derivation without adopting a greatest value.',
        '2055':'Tail is solving and rejecting modular candidates and continues another CRT case; no final requested label is established.',
        '639':'Tail remains an enumeration of individual room codes; no completed total is established.',
        '2780':'Automatic expression 512-X-Y+Z contains unresolved counts; later tail revises disjoint-line counting and supplies no completed configuration count.',
        '2869':'Candidate grid dimensions change; final calculation of a binomial expression degenerates into a truncated factorial digit run. No adopted path count is established.',
    }
    for candidate in auto['manual_candidates']:
        item = candidate['item_id']
        packet_path = ROOT/'audit'/'blind_extraction'/f'{item}.json'
        packet = json.loads(packet_path.read_text()); text=packet['scope_text']
        assert packet['ground_truth_excluded'] and 'answer' not in packet
        if item in wrappers:
            value = wrappers[item]; quote = '\\boxed{\\text{'+value+'}}'; literal=value
            rationale = 'Final box explicitly selects this option; remove the LaTeX text wrapper only.'
        elif item in explicit:
            value,quote,literal,rationale=explicit[item]
        else:
            assert item in unresolved, item
            value=quote=literal=None; rationale=unresolved[item]
        span=None
        if value is not None:
            offset=text.rfind(quote);assert offset>=0,(item,quote)
            inside=quote.rfind(literal);assert inside>=0
            begin=packet['scope_offset']+offset+inside;span=[begin,begin+len(literal)]
        decisions.append(dict(item_id=item, extracted=value, span=span, quote=quote, literal=literal,
            scope=packet['automatic']['scope'], method='blind_manual_extraction' if value is not None else 'blind_review_unresolved',
            status='extracted' if value is not None else 'unresolved', rationale=rationale,
            generation_sha256=packet['generation_sha256'], packet_sha256=digest(packet_path),
            review_scope='explicit final-answer tail/automatic extraction; for whole-response ambiguity, candidate-marker windows and tail, not exhaustive semantic annotation',
            ground_truth_excluded=True))
    assert len(decisions)==len(set(wrappers)|set(explicit)|set(unresolved))==32
    save(ROOT/'audit'/'manual_extraction_freeze.json',dict(at=datetime.now(timezone.utc).isoformat(),
        automatic_freeze_sha256=digest(ROOT/'audit'/'automatic_extraction_freeze.json'),
        reviewer='main agent, single annotator', ground_truth_excluded=True, rows=decisions))
    print('Blind extraction frozen:',len(decisions),'reviewed;',sum(r['extracted'] is not None for r in decisions),'adopted;',sum(r['extracted'] is None for r in decisions),'unresolved')


if __name__ == '__main__':
    main()
