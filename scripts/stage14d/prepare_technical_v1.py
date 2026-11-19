"""Materialize four actually inspected sources and eight reviewed early prefixes.

Manual source and trace judgments below are not inferred from answer scores.
This creates only technical inputs; it does not certify the 300-family panel.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
from PIL import Image
from tokenizers import Tokenizer
from scripts.stage14d.design import render_directive, fingerprint

ROOT = Path('outputs/stage14d')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f: json.dump(value, f, indent=2, ensure_ascii=False)
def lines(path): return [json.loads(s) for s in Path(path).read_text().splitlines()]


SOURCE = {
 '438': dict(request='Read where the topmost horizontal bar is suspended relative to its two hanging branches.',
   reference='The top bar is suspended centrally, with equal-arm left and right branch attachments.',
   roi=[110,28,597,124], target='topmost bar central suspension and branch attachment relation',
   rule='First balance/suspension fact of the frozen attachment tree, localized to the topmost bar; no weights or solved relations.',
   source_note='Original image shows central ceiling attachment and two branch attachments. Equal-arm depiction is schematic, not a pixel-exact metrology claim.'),
 '2907': dict(request='Read the length label on the leftmost marked interval below the baseline.',
   reference='4 cm', roi=[43,1048,547,1126], target='first of the four explicitly labelled baseline intervals',
   rule='First canonical interval binding in the preserved metadata (four interval bindings and four band colors). Shared-endpoint layout remains parent-object context; no inferred diameter is a target.',
   source_note='Four original bracketed baseline intervals each visibly carry 4 cm. The leftmost is individually bound by its bracket; no sum, radius or area is supplied.'),
 '2212': dict(request='Read how the labelled flower-bed dimensions are oriented relative to the rows.',
   reference='6 feet horizontally along a row; 2 feet vertically between rows.',
   roi=[96,491,497,630], target='dimension-to-direction binding on the lower-left flower bed',
   rule='The sole frozen scalar relation; the question gives the dimensions but not their direction binding.',
   source_note='The 2 label is at the left vertical side and 6 at the bottom horizontal side of the bottom-left bed. No total garden or walkway area supplied.'),
 '694': dict(request='Read the name of the station immediately adjacent to station A on the line.',
   reference='B', roi=[43,120,214,223], target='first adjacency in the frozen ordered station layout, A to its immediate neighbor',
   rule='First source-defined adjacency of the ordered A,B,C,D,E,F object. A is only a locator. The question enumerates names/endpoints but does not explicitly state this adjacency.',
   source_note='Original labels A and B are attached to the first two consecutive stops. This reads the source order; it does not simulate a journey or supply the requested 46th stop.'),
}

# All strings below were read in the original native responses. Boundaries are
# conservative clause/sentence boundaries before the first partial commitment.
TRACE = {
 ('438','I'): dict(boundary='meaning the torques', E0='horizontal bars',
   E1='two equal-length arms below it', E2='where total weight on each side must be equal',
   earliest='meaning the torques', note='Opening weights/torques conflation already uses an equal-arm assumption; stop before that clause. E2 precedes the first explicit geometrical E1.'),
 ('438','T'): dict(boundary="It's a balance, so", E0='structure of the toy',
   E1="a horizontal bar with a pivot in the middle", E2='the total weight on each side should be equal',
   earliest="It's a balance, so", note='A weight equality is used before the queried visual suspension is explicitly described. Retain only the preceding question/goal restatement.'),
 ('2907','I'): dict(boundary='The diagram shows', E0='four semicircles',
   E1='the total diameter is divided into four equal segments of 4 cm each',
   E2='with diameters decreasing by 4 cm each time', earliest='The diagram shows',
   note='All-interval assertion covers the leftmost labelled interval. Stop before any 4-cm source assertion, not after its sentence.'),
 ('2907','T'): dict(boundary='Wait, actually, looking at the image', E0='four semicircles',
   E1='since the first segment is 4 cm', E2='the total length of the base is 4*4 = 16 cm',
   earliest='the description says 4 cm segments', note='Earlier generic 4-cm mention is already partial target value. The full first-segment binding occurs later than a downstream sum.'),
 ('2212','I'): dict(boundary='Each bed is 6 feet wide.', E0='flower beds per row',
   E1='Each bed is 6 feet wide.', E2='6 + 1 + 6 = **13 feet**', earliest='Each bed is 6 feet wide.',
   note='Earlier paragraphs restate supplied dimensions/rows and mention walkway directions, but contain no bed-dimension-to-direction binding. Entire retained prefix reviewed.'),
 ('2212','T'): dict(boundary="So, vertically (let's say the height direction)", E0='flower beds each',
   E1='Each flower bed is 6 feet wide', E2='each bed being 2 feet tall',
   earliest='each bed being 2 feet tall', note='Vertical 2-foot commitment precedes the later horizontal 6-foot statement; cut before that partial binding.'),
 ('694','I'): dict(boundary='This implies that the train', E0='6 stations',
   E1='B → A → F', E2='B → A → F', earliest='B → C → D → E → F',
   note='First route explicitly contains A-B adjacency and an inconsistent A-F departure. E1 and first use coincide in this mixed route; no inference from the final answer. Cut before the route clause.'),
 ('694','T'): dict(boundary='The line is A---B', E0='stations A, B, C, D, E, F',
   E1='The line is A---B---C---D---E---F.', E2='the path would be A-B-C-D-E-F-E-D-C-B-A-B-C-D-E-F',
   earliest='The line is A---B', note='Initial station-name enumeration is a question restatement, not an adjacency claim. Cut before the first explicitly spatial ordered-line assertion.'),
}


def run():
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    cfg=json.loads((ROOT/'spec/pinned_model_revisions_and_recipes.json').read_text())
    selected=lines(ROOT/'cohorts/technical_source4_proposed.jsonl')
    scientific={r['family_id'] for r in lines(ROOT/'cohorts/thinking_strata_300.jsonl')}
    assert len(selected)==4 and not ({r['family_id'] for r in selected}&scientific)
    sources=[]; anchors=[]; rows=[]; originals={}
    for role,row in zip('ABCD',selected):
        item=row['item_id']; s=SOURCE[item]; image=row['original_image']
        assert sha(image)==row['original_image_sha256']
        width,height=Image.open(image).size
        assert 0<=s['roi'][0]<s['roi'][2]<=width and 0<=s['roi'][1]<s['roi'][3]<=height
        target=dict(request=s['request'],source_request_sha256=hashlib.sha256(s['request'].encode()).hexdigest(),
                    review_status='SOURCE_VALID_VALUE_FREE',ROI_id=f'technical_{item}_target')
        source=dict(at=now,role=role,item_id=item,family_id=row['family_id'],original_image=image,
            original_image_sha256=sha(image),original_pixel_dimensions=[width,height],
            pixel_ROI=s['roi'],normalized_ROI=[v/(width if i%2==0 else height) for i,v in enumerate(s['roi'])],
            target_identity=s['target'],model_visible_target=target,evaluator_only_reference=s['reference'],
            primary_atom_index=0,parent_atom_metadata=row['atom_metadata'],selection_reason=s['rule'],
            source_observation=s['source_note'],source_receipt=row['stage14a_receipt'],
            source_review_method='Main agent directly viewed all four original images; same-agent semantic recheck, no independent human/rater.',
            leakage_review='PASS: names position/source only; no correct value, route solution, balance equation, area or gold injection.',
            irrelevant_control_status='IRRELEVANT_CONTROL_INAPPLICABLE',
            irrelevant_reason='No separately task-irrelevant factual source certified outside this compact mathematical diagram. Decorative marks are not used as fabricated factual controls.',
            stage14d_outcomes_seen=False,scope='TECHNICAL_FOUR_ONLY')
        sources.append(source);originals[image]=sha(image);originals[row['stage14a_receipt']]=sha(row['stage14a_receipt'])
        for model in 'IT':
            base=Path(f'outputs/stage14b/raw/mathvision_native/mv_{item}_image_{model}_r0/attempt_0')
            inp=json.loads((base/'input.json').read_text());g=json.loads((base/'generation.json').read_text())
            receipt=json.loads((base/'result.json').read_text())
            assert receipt['input_sha256']==sha(base/'input.json') and receipt['generation_sha256']==sha(base/'generation.json')
            for name in ['input.json','generation.json','result.json']:originals[str(base/name)]=sha(base/name)
            t=TRACE[item,model];raw=g['raw_decoded_response'];ids=g['generated_token_ids']
            tokenizer=Tokenizer.from_file(str(Path(cfg['models'][model]['model']['checkpoint'])/'tokenizer.json'))
            decoded=tokenizer.decode(ids,skip_special_tokens=True)
            assert decoded==raw,('Native decoded bytes differ',item,model)
            b=raw.index(t['boundary']);required_end=max(raw.index(t[k])+len(t[k]) for k in ['E0','E1','E2','earliest'])
            # Decode from saved IDs only; no encode(text) replacement of the prefix.
            lengths=[0]
            for n in range(1,len(ids)+1):
                prefix=tokenizer.decode(ids[:n],skip_special_tokens=True)
                assert raw.startswith(prefix),(item,model,n)
                lengths.append(len(prefix))
                if len(prefix)>required_end+8:break
            boundary=max(n for n,k in enumerate(lengths) if k<=b)
            prefix=tokenizer.decode(ids[:boundary],skip_special_tokens=True)
            assert prefix==raw[:lengths[boundary]] and len(prefix)<=raw.index(t['earliest'])
            def event(key):
                start=raw.index(t[key]);end=start+len(t[key]);lo=max(i for i,z in enumerate(lengths) if z<=start)
                hi=next(i for i,z in enumerate(lengths) if z>=end)
                return dict(quote=t[key],char_start=start,char_end=end,token_start=lo,token_end=hi,
                            interpretation='Explicit reviewed span; timing and partial/contradictory notes govern interpretation')
            anchor=dict(at=now,model=model,item_id=item,family_id=row['family_id'],role=role,
                original_generation=str(base/'generation.json'),original_generation_sha256=sha(base/'generation.json'),
                E0=event('E0'),E1=event('E1'),E2=event('E2'),earliest_value_bearing=event('earliest'),
                anchor_token_index=boundary,anchor_char_index=len(prefix),prefix_text=prefix,
                prefix_generated_token_ids=ids[:boundary],prefix_text_sha256=hashlib.sha256(prefix.encode()).hexdigest(),
                prefix_ids_sha256=fingerprint(ids[:boundary]),source_neutral_prefix_review='PASS',
                review_note=t['note'],fallback=False,reviewed_native_interval=[0,required_end],
                later_trace_contradiction_census='NOT_PERFORMED; this is a technical prefix certificate, not a whole-trajectory scientific annotation',
                reconstructed_prefill=True,historical_hidden_state_identity_claimed=False)
            anchors.append(anchor)
            variants=[('B0','ON','repeat0'),('B0','ON','repeat1'),('THINK_MORE','ON','once'),('LOOK_GENERIC','ON','once')] if role in 'AB' else [('LOOK_TARGET','ON','once'),('LOOK_TARGET','OFF_FUTURE','once')]
            for arm,mode,repeat in variants:
                directive=render_directive(arm,target)
                directive_ids=tokenizer.encode(directive,add_special_tokens=False).ids
                rows.append(dict(task_id=f'technical_{model}_{role}_{arm}_{mode}_{repeat}',role=role,model=model,
                    family_id=row['family_id'],item_id=item,image=image,image_sha256=sha(image),
                    parent_input=str(base/'input.json'),parent_generation=str(base/'generation.json'),
                    parent_input_sha256=sha(base/'input.json'),parent_generation_sha256=sha(base/'generation.json'),
                    prefix_generated_token_ids=ids[:boundary],prefix_text=prefix,
                    directive=directive,directive_ids=directive_ids,arm=arm,image_access=mode,repeat=repeat,
                    seed=int(hashlib.sha256(('stage14d-g0-v1-20261011|generation|'+row['family_id']).encode()).hexdigest(),16)%(2**31),
                    max_tokens=512,scientific=False,correctness_not_a_gate=True))
    assert len(rows)==24 and len({r['task_id'] for r in rows})==24
    save(ROOT/'cohorts/technical_source_QC_v1.json',dict(at=now,records=sources,scientific_sources_certified=0))
    save(ROOT/'anchors/technical_prefix_QC_v1.json',dict(at=now,records=anchors,scientific_anchors_certified=0))
    save(ROOT/'spec/technical_calls_v1.json',dict(at=now,rows=rows,call_ceiling=24,GPU_hour_ceiling=2,
        originals=originals,only_technical=True,max_concurrency=2,scientific_launch=False))
    print(json.dumps(dict(sources=len(sources),anchors=len(anchors),calls=len(rows),
       boundaries=[dict(item=r['item_id'],model=r['model'],tokens=r['anchor_token_index']) for r in anchors]),indent=2))


if __name__=='__main__':run()
