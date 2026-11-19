"""Pre-C4-label freeze of a disclosed CHAIR-compatible inventory normalization."""
import json
from pathlib import Path
from scripts.stage6a.inventory import OUT

categories=json.loads(Path('/data/dataset/COCO2014/annotations/instances_val2014.json').read_text())['categories']
extra={
 'person':['man','men','woman','women','person','people','child','children','boy','boys','girl','girls','player','players','rider','riders','skier','skiers','snowboarder','snowboarders','worker','workers','pedestrian','pedestrians'],
 'bicycle':['bike','bikes'],
 'car':['automobile','automobiles','van','vans','minivan','minivans','sedan','sedans','taxi','taxis','cab','cabs','SUV','SUVs'],
 'motorcycle':['motorbike','motorbikes','motor bike','motor bikes','motor cycle','motor cycles','scooter','scooters'],
 'airplane':['plane','planes','aircraft','jet','jets'],
 'train':['locomotive','locomotives'], 'truck':['pickup truck','pickup trucks','lorry','lorries'],
 'boat':['ship','ships','sailboat','sailboats','canoe','canoes','kayak','kayaks','yacht','yachts'],
 'traffic light':['traffic signal','traffic signals','stoplight','stoplights'],
 'fire hydrant':['hydrant','hydrants'],
 'bird':['duck','ducks','goose','geese','gull','gulls','seagull','seagulls','pigeon','pigeons','swan','swans','parrot','parrots'],
 'cat':['kitten','kittens'], 'dog':['puppy','puppies','pup','pups','canine','canines'],
 'horse':['pony','ponies'], 'cow':['cattle','bull','bulls','calf','calves'],
 'backpack':['rucksack','rucksacks','knapsack','knapsacks'], 'handbag':['purse','purses'],
 'tie':['necktie','neckties','bow tie','bow ties'], 'suitcase':['luggage','suit case','suit cases'],
 'sports ball':['ball','balls','soccer ball','soccer balls','basketball','basketballs','football','footballs','tennis ball','tennis balls'],
 'tennis racket':['racket','rackets','racquet','racquets','tennis racquet','tennis racquets'],
 'knife':['knives'], 'sandwich':['burger','burgers','hamburger','hamburgers','cheeseburger','cheeseburgers'],
 'donut':['doughnut','doughnuts'], 'chair':['stool','stools'],
 'couch':['sofa','sofas','recliner','recliners'], 'potted plant':['houseplant','houseplants'],
 'dining table':['table','tables','desk','desks'], 'tv':['television','televisions','TV','TVs','monitor','monitors'],
 'laptop':['laptop computer','laptop computers','macbook','macbooks'],
 'mouse':['computer mouse','computer mice','mice'], 'remote':['remote control','remote controls'],
 'cell phone':['cellphone','cellphones','mobile phone','mobile phones','smartphone','smartphones','phone','phones','telephone','telephones','iphone','iphones'],
 'oven':['stove','stoves','stovetop','stovetops'], 'refrigerator':['fridge','fridges'],
 'teddy bear':['teddybear','teddybears'], 'hair drier':['hair dryer','hair dryers','hairdryer','hairdryers']}
invariants={'sheep','skis','scissors','broccoli'}
aliases={r['name']:sorted(set([r['name']]+([] if r['name'] in invariants else [r['name']+'s'])+extra.get(r['name'],[]))) for r in categories}
aliases['bus']=sorted(set(aliases['bus']+['buses']))
aliases['bench']=sorted(set(aliases['bench']+['benches']))
aliases['wine glass']=sorted(set(aliases['wine glass']+['wine glasses']))
aliases['skis']=sorted(set(aliases['skis']+['ski']))
aliases['sandwich']=sorted(set(aliases['sandwich']+['sandwiches']))
aliases['toothbrush']=sorted(set(aliases['toothbrush']+['toothbrushes']))
aliases['person']=sorted(set(aliases['person']+['bicyclist','bicyclists','cyclist','cyclists']))
data=dict(method='Stage6A conservative CHAIR-compatible object normalization; not the unmodified reference evaluator',
 source_reference='https://github.com/LisaAnne/Hallucination/blob/master/utils/chair.py',
 reference_principle='Ground-truth inventory is union of COCO instance categories and normalized human reference captions.',
 deviations=['Frozen transparent plural/alias lexicon replaces unavailable pattern/nltk pipeline.',
 'Conservative ambiguous-noun coverage; generic computer/bag/container/seat not automatically assigned a category.',
 'Negated and hypothetical reasoning mentions retained separately from asserted object claims.',
 'Report final-caption object hallucination and whole-trace object hallucination separately; a case-control failure base contains an audited asserted object inconsistency in thinking or final, even if later corrected.',
 'Candidate hallucinations require an independent image audit; annotation absence alone is not treated as conclusive visual absence.'],
 aliases=aliases,attention_used=False,model_scores_used=False)
p=OUT/'config/object_synonyms.json'
if p.exists():raise FileExistsError(p)
p.write_text(json.dumps(data,indent=2)+'\n')
print(len(aliases),'categories frozen')
