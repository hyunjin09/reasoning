"""Pure recovery checks. No evaluated-model, gold or oracle imports."""
from pathlib import Path
from scripts.stage14d1.common import load, save, sha, now, rows

R = Path('outputs/stage14d1_sava_recovery/v1')
OLD = Path('outputs/stage14d1_sava')

def remaining_seconds(prior, allocations):
    remaining = 7200-prior-sum(allocations)
    if remaining < 0:
        raise ValueError('Technical allocation budget exceeded')
    return remaining

def replay_comparison(a,b):
    first = next((i for i,(x,y) in enumerate(zip(a['tokens'],b['tokens'])) if x!=y),None)
    if first is None and len(a['tokens'])!=len(b['tokens']):
        first=min(len(a['tokens']),len(b['tokens']))
    identity = all(a[k]==b[k] for k in ['prompt','seed','pixels'])
    return dict(input_identity=identity,token_identity=a['tokens']==b['tokens'],
                first_divergence=first, **{'pass':identity and a['tokens']==b['tokens']})

def require_replay(comparisons):
    if len(comparisons)!=8 or not all(x['pass'] for x in comparisons):
        raise ValueError('Eight-family exact replay gate failed; no acquisition revalidation admission')

CONTROLS = [
    dict(id='positive_flag',expected='QUERY',question='What color is the flag beside the cabin in the image?',
         prefix='The next reasoning step needs the color of the flag beside the cabin. I have not yet observed its color and must obtain that visual fact before answering.'),
    dict(id='positive_label',expected='QUERY',question='Which labeled point is directly above the star in the diagram?',
         prefix='I need to read the label of the point directly above the star. The point label has not been supplied by the question or my reasoning.'),
    dict(id='positive_dots',expected='QUERY',question='How many dots are in the upper-right compartment of the image?',
         prefix='My next step is to read the dot count specifically in the upper-right compartment. I have no observation of this count yet.'),
    dict(id='negative_arithmetic',expected='NONE',question='Compute seven plus five using the numbers in this sentence.',
         prefix='All necessary inputs are stated in the question. The next step is purely arithmetic and requires no image fact.'),
    dict(id='negative_perimeter',expected='NONE',question='A triangle has sides of length three, four, and five. Find its perimeter.',
         prefix='All three side lengths are supplied explicitly by the text. I need only add them; no missing visual measurement or relation is needed.'),
    dict(id='negative_color',expected='NONE',question='The marked cell is blue. Report its color.',
         prefix='The question explicitly gives the requested color as blue. The required fact is already available; no new image fact is needed.')]
