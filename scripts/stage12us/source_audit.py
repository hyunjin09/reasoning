"""Prospective manual cut/content decisions, independent of transfer outcomes."""
import hashlib
import re
from pathlib import Path
from scripts.stage12us.common import ROOT,load,save,sha,now
from scripts.stage12us.protocol import canonical,seed


# Exact first candidate anchors, never selected from new target outcomes.
# Validity refers to the operative derivation at the cut; corrected exploratory
# mistakes are distinguished from material errors still carried into that state.
DECISIONS = [
 ('C','798','That means the **area inside** the wall is 10 × 10',
  'E_FULL','DERIVATION_UNCLEAR',
  'Single-layer cube frame and 4n−4=36 correctly give outer n=10, but the subsequent square-area referent is ambiguous; no certified already-adequate inner-area derivation.',
  ['single layer of cubes','4n - 4 = 36','So the square area has side length 10 cubes.']),
 ('T','798','Then the inner square area would be (10 - 2)^2 = 64.',
  'E_WRONG_OR_CONFLICTING','DERIVATION_FLAWED',
  'Adopts stacked bottom/top cubes contrary to one-cube height; retains conflicting frame examples (inner2x2 called outer3x3). The later m−2 relation is useful but does not erase retained conflicts.',
  ["it's a 3D structure with some cubes on the bottom (gray) and some on top (white).",'3x3 - 2x2 = 9 - 4 = 5 cubes.']),
 ('C','991','If it’s already ordered, then answer is 0.',
  'E_WRONG_OR_CONFLICTING','DERIVATION_FLAWED',
  'Wrong ordered block sizes replace the frozen1/4/2/3 order; move is incorrectly described as preserving relative order.',
  ['in the same relative order','So the stack from bottom to top: [4, 3, 2, 1]']),
 ('T','991',"If it's already ordered, then the answer is 0.",
  'E_WRONG_OR_CONFLICTING','DERIVATION_UNCLEAR',
  'Repeated1/2/3/4 order contradicts second-largest/third-second-smallest facts. Prefix eventually recognizes reversal but does not establish a valid minimal sorting derivation.',
  ['So the initial stack from top to bottom is [1, 2, 3, 4].','select any prefix of the stack']),
 ('C','750','Total length = 6*4 + 7*4 = 12 + 28 = 40 cm.',
  'E_WRONG_OR_CONFLICTING','DERIVATION_FLAWED',
  'Treats cross-AB vertical spans as individual square sides instead of sums of adjacent sides, carrying v2=s2 and an unjustified equal-size assumption.',
  ['$v_2 = s_2$','Suppose all squares have the same side length s.']),
 ('T','750','If s₁ + s₂ + s₃ + s₄ = 24, then total broken line length = 24 + 2*24 = 72 cm.',
  'E_WRONG_OR_CONFLICTING','DERIVATION_FLAWED',
  'Misbinds corner labels and four-square topology; retains an extra uncovered horizontal segment despite the frozen end-to-end partition.',
  ['A₁₂ to B (24 - 4s)','Total broken line length = 24 + 2(s₁ + s₂ + s₃ + s₄)']),
 ('C','2975','y = 180 - 4x = 180 - 4(23.6)',
  'E_WRONG_OR_CONFLICTING','DERIVATION_FLAWED',
  'Near/far secant incidences appear, but O is called a diameter endpoint/midpoint of BT. The radius-chord angle is incorrectly equated to half arcRS, leading to x23.6.',
  ['$B$ and $O$ are endpoints of a diameter','3x - 28^\\circ = \\frac{1}{2} \\times \\text{arc RS}']),
 ('T','2975','Then arc RS = α - β = 96° - 28° = 68°',
  'E_FULL','DERIVATION_VALID',
  'Both source incidences are explicit. At the cut the correct exterior-secant equation and central-angle relation give alpha96,beta28 and identify RS=alpha−beta. Earlier theorem doubts are resolved by the explicit coordinate check.',
  ['B-O-T colinear, O between B and T.','S closer to T, R farther from T',
   'α + β = 124°','α = 180° - 3*28° = 180° - 84° = 96°']),
 ('C','2908','Thus, $a + b = 60 + 10 = 70$.',
  'E_FULL','DERIVATION_FLAWED',
  'All three mutual tangencies are correct; arc60 degrees instead of120 gives coefficient b10. This is a derivation failure given correct incidence evidence.',
  ['each pair is externally tangent','wrap around each circle along a **60° arc**','$a = 60$, $b = 10$']),
 ('T','2908','a + b = 80.',
  'E_FULL','DERIVATION_FLAWED',
  'All pairwise tangencies are explicit and final belt decomposition is useful. Retained terminal coordinate proof uses a false common-tangent line and wrong point distances before obtaining120 degrees; the useful conclusion does not certify all derivation as valid.',
  ['each pair is tangent (distance between centers is 2r = 20)',
   'So tangent line: y = (√3/3)x + c','Total belt length = 6*10 + 2π*10 = 60 + 20π.']),
 ('C','2363','Set them equal: $\\frac{\\tan \\theta}{2} =',
  'E_WRONG_OR_CONFLICTING','DERIVATION_FLAWED',
  'Conflicts between segment/sector identification and using the entire triangle rather than its external portion carry into the first proposed equality.',
  ['Looking at the diagram: the shaded region is the area between chord $ED$ and arc $ED$',
   'probably the large shaded region is the area of triangle $ABC$']),
 ('T','2363','Set equal: θ/2 = (1/2)(tan θ - θ + sin θ)',
  'E_WRONG_OR_CONFLICTING','DERIVATION_FLAWED',
  'The target shading alternates between sector and segment. Subtracts a circular segment rather than the whole sector from triangleABC, so the first equality is an erroneous task-answer candidate.',
  ['Large shaded area = (1/2) tan θ - (θ/2 - (1/2) sin θ)',
   'Case 2: Small shaded area = segment ECD']),
 ('C','2007','Total outer perimeter = 216 (from squares) + 216 (from triangles) = 432 cm.',
  'E_WRONG_OR_CONFLICTING','DERIVATION_FLAWED',
  'Attaches each triangle to the outer/free side of a square instead of a gap between adjacent squares; consequently counts two exposed sides per component.',
  ['a triangle is attached to the *free side* of the square','Two sides are external → each 18 cm']),
 ('T','2007','so perimeter P = 12*18 = 216 cm.',
  'E_FULL','DERIVATION_VALID',
  'Operative state correctly constructs six exterior squares and six gap triangles, counts48 component sides and18 shared edges, yielding12 boundary sides. Earlier tentative layouts are not adopted.',
  ['So triangle k shares two edges with the adjacent squares',
   'Total E_s = 6 + 12 = 18','E_p = 48 - 36 = 12 edges.']),
]


def main():
    assert not (ROOT/'audit/science_launch.json').exists()
    packets={}
    for source,item,*_ in DECISIONS:
        packets[(source,item)]=load(ROOT/'audit/source_packets'/f'{source}_{item}.json')
    # Full-source lexical sweep is preserved so absence claims have an audit trail.
    # It supplements focused semantic reading; it is not a proof of semantic absence.
    candidates=[];rows=[]
    golds={p['item_id']:str(p['gold']) for p in [__import__('json').loads(x) for x in
           Path('outputs/stage12ts/v1/audit/correctness_packets/T.jsonl').read_text().splitlines()]}
    for source,item,marker,e,d,reason,quotes in DECISIONS:
        p=packets[(source,item)];raw=p['raw'];cut=raw.index(marker);prefix=canonical(raw[:cut])
        assert all(q in prefix for q in quotes),(source,item,[q for q in quotes if q not in prefix])
        assert not re.search(r'\\(?:boxed|fbox)\s*\{|Final\s+Answer\s*:',prefix,re.I)
        dest=ROOT/'prefixes'/f'{source}_{item}.txt'
        row=dict(item_id=item,family_id=p['family_id'],cohort=p['cohort'],source=source,question=p['question'],
            raw_cut_offset=cut,raw_length=len(raw),cut_marker=marker,excluded_candidate=raw[cut:cut+240],
            prefix_path=str(dest),canonical_text=prefix,evidence_state=e,derivation_state=d,reason=reason,quotes=quotes,
            EXPLICIT_FINAL_PRESENT=False,ANSWER_CANDIDATE_PRESENT=False,
            GOLD_VALUE_INCIDENTALLY_PRESENT=bool(re.search(r'(?<!\w)'+re.escape(golds[item])+r'(?!\w)',prefix)),
            incidental_method='Exact frozen gold string with word boundaries; descriptive, not semantic answer leakage.',
            generation_path=p['generation_path'],generation_sha256=p['generation_sha256'])
        rows.append(row)
        for m in re.finditer(r'(?i)answer|\\boxed|(?:total|perimeter|volume|minimum|smallest|condition)[^\n]{0,90}|a\s*\+\s*b',raw[:cut+250]):
            candidates.append(dict(source=source,item_id=item,offset=m.start(),context=raw[max(0,m.start()-100):m.end()+180]))
    # Finish all assertions before writing any immutable scientific artifact.
    for row in rows:
        with Path(row['prefix_path']).open('x') as f:f.write(row['canonical_text'])
        row['prefix_sha256']=sha(row['prefix_path'])
    save(ROOT/'audit/candidate_scan.json',dict(at=now(),rows=candidates,
        limitation='Whole-prefix lexical scan plus targeted semantic/content review; not exhaustive independent review of every long-trace sentence.'))
    save(ROOT/'stage12us_source_prefixes.json',dict(at=now(),rows=rows,canonicalization='Only think control wrappers removed'))
    save(ROOT/'stage12us_prefix_content_audit.json',dict(at=now(),rows=[{k:v for k,v in r.items() if k!='canonical_text'} for r in rows],
        new_transfer_outcomes_inspected=False,source_original_outcomes_known_by_cohort=True,
        source_review='Single-agent source/content audit; full-prefix candidate scans and exact quoted support; no independent annotation claim.'))
    save(ROOT/'stage12us_canonical_trace_hashes.json',dict(at=now(),hashes={r['prefix_path']:r['prefix_sha256'] for r in rows}))
    cohorts=load(ROOT/'audit/cohorts.json')['cohorts']
    for cohort,name in [('primary','stage12us_primary_b4_manifest.json'),('secondary','stage12us_secondary_b1_manifest.json')]:
        save(ROOT/name,dict(at=now(),rows=cohorts[cohort],selection='Exact frozen Stage12T-S C−T+ within corresponding B4/B1 stratum; no new outcome selection.'))
    source_index={(r['source'],r['item_id']):r for r in rows};tasks=[]
    primary_order=sorted(cohorts['primary'],key=lambda r:r['family_id'])
    partners={r['item_id']:primary_order[(i+1)%5]['item_id'] for i,r in enumerate(primary_order)}
    for cohort in ['primary','secondary']:
        for r in cohorts[cohort]:
            conditions=['RT_I','RT_T','RC_I','RC_T','Q_I','Q_T']+(['ST_I','SC_T'] if cohort=='primary' else [])
            for condition in conditions:
                target=condition[-1];source=condition[1] if condition[0] in ['R','S'] else None
                source_item=partners[r['item_id']] if condition.startswith('S') else r['item_id']
                prefix=source_index.get((source,source_item))
                for replicate in range(3):
                    tasks.append(dict(task_id=f"{condition}_{r['item_id']}_r{replicate}",phase='science',cohort=cohort,
                        item_id=r['item_id'],family_id=r['family_id'],question=source_index[('T',r['item_id'])]['question'],
                        condition=condition,target=target,source=source,source_item_id=source_item if source else None,
                        source_family_id=prefix['family_id'] if prefix else None,replicate=replicate,
                        seed=seed(r['family_id'],condition,replicate),prefix_path=prefix['prefix_path'] if prefix else None,
                        prefix_sha256=prefix['prefix_sha256'] if prefix else None))
    assert len(tasks)==156
    save(ROOT/'audit/science_execution.json',dict(at=now(),tasks=tasks,shuffle_partners=partners,config_sha256=sha(ROOT/'config.json')))
    files=[ROOT/n for n in ['stage12us_source_prefixes.json','stage12us_prefix_content_audit.json',
            'stage12us_canonical_trace_hashes.json','stage12us_primary_b4_manifest.json','stage12us_secondary_b1_manifest.json',
            'stage12us_reasoning_state_transfer_spec.md','audit/science_execution.json','config.json']]
    save(ROOT/'audit/source_prefix_seal.json',dict(at=now(),hashes={str(p):sha(p) for p in files},
         primary_generation_not_launched=True,primary_correctness_unopened=True))
    print('Sealed14 scientific prefixes and156 target calls.')


if __name__=='__main__':main()
