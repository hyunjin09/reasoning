"""Source-only shared D1 subfact identifiers, frozen before any probe output.

Identifiers point into the existing source atom; they do not replace its content.
Full atom recovery also requires its unenumerated shared topology and bindings.
"""
from scripts.stage14c.common import *


def series(name,n):return [f'{name} {i+1}' for i in range(n)]
def grid(h,w):return [f'row {r+1} column {c+1}' for r in range(h) for c in range(w)]


def main():
    schemas=rows(ROOT/'source/D1_review_schema_v1.jsonl');groups={b:[r for r in schemas if r['benchmark']==b] for b in ['math','MMStar','BlindTest']}
    maps={}
    def put(b,i,j,keys):
        a=groups[b][i]['atoms'][j]
        assert len(keys)==a['subfact_count'],(b,i,j,len(keys),a['subfact_count'])
        assert len(set(keys))==len(keys)
        maps[b,i,j]=keys
    def m(i,j,keys):put('math',i,j,keys)
    def v(i,j,keys):put('MMStar',i,j,keys)
    for i,n in enumerate([1,1,2,3]):
        m(0,i,series('circle',n)+(['left external stub','right external stub'] if i==1 else ['horizontal crossing diameter and extensions']))
    m(1,0,['Adeline-Carole crossing 1','Adeline-Carole crossing 2','Adeline-Benjamin crossing 1','Adeline-Benjamin crossing 2'])
    m(2,0,grid(2,4));m(3,0,series('cell in stated column/level order',12));m(4,0,[f'row {r+1} point {c+1}' for r,n in enumerate([3,4,5,4,3]) for c in range(n)])
    m(5,0,[f'time {x} distance' for x in [0,1,2,3,8,9,12]])
    m(6,2,['upper-left outer corner coincidence','lower-right outer corner coincidence','first-to-middle square contact','middle-to-last square contact'])
    m(7,0,['C inward corner','F inward corner']);m(8,0,[f'{side} half {j+1} inward semicircle' for side in ['top','right','bottom','left'] for j in range(2)])
    m(8,1,['corner overlap lenses white','central outside region white','singly covered regions gray'])
    m(9,0,['XX tens','XX ones','YY tens','YY ones','ZZ tens','ZZ ones','sum hundreds Z','sum tens Y','sum ones X'])
    m(10,0,['ordered bottom prime row','pair-product next row','neighbor-pair centering/narrowing','top K'])
    m(13,0,['central diagonal square']+[f'{s} inward black triangle' for s in ['top','right','bottom','left']])
    m(14,0,series('front column height',4));m(14,1,series('right-view column height',4));m(14,2,grid(4,4))
    m(15,0,['P-U','P-V','P-M','U-V','U-M','V-M','M-W','M-X','M-Q','W-X','W-Q','X-Q'])
    m(16,0,['times 0.5','times one third','square','add 1','terminal box 50'])
    m(17,0,['L/R base and U crossing','M on base LR','P on LU','Q beyond U and M-P-Q order','alpha ULR','beta URL','gamma PQU','delta UPM'])
    m(18,0,grid(5,5));m(19,0,['leftmost triangle vertex','upper-right triangle vertex','lower-right triangle vertex']);m(19,1,series('radial wedge in cyclic order, alternating fill',6));m(19,2,['leftmost triangle vertex','upper-right triangle vertex','lower-right triangle vertex'])
    for i in [20,82]:m(i,0,[f'bottom {x}' for x in grid(3,3)]+[f'middle {x}' for x in grid(2,2)]+['top cube'])
    m(21,0,['Henry','India','Jenny','Ken','Lena']);m(22,0,['unseen back lower-left','back upper-left R','front lower-left P','back lower-right S'])
    m(23,0,['left base box','left exponent box','multiplication sign','right base box','right exponent box'])
    m(24,0,['first shared seam pins','second shared seam pins','left outer edge pins','right outer edge pins'])
    m(25,0,series('top circle',7)+series('middle gap circle',6)+series('bottom circle',7))
    m(26,0,['upper-right (4,2)','lower-right (4,-2)','upper-left (-4,2)','lower-left (-4,-2)']);m(27,0,grid(2,11))
    m(29,0,['A top','B right','C bottom','D left','upper-left shaded face','lower-right shaded face'])
    m(30,0,['(1,0)','(2,0)','(0,1)','(1,1)'])
    m(31,0,list('abcde')+['upper-right join after a','upper-right join after c','lower-left join after b','lower-left join after d','upper area 2','left area 5','right area 9','bottom area 4'])
    m(32,0,['length ten lots','width two lots','A position','B position','C position','D position','E position']);m(32,1,['common start S','1m/h arrow up','2m/h arrow right'])
    m(33,0,['(1,1)A','(1,5)','(2,2)','(2,4)','(3,3)D','(3,4)','(4,1)B','(5,1)C','(5,3)E','(5,5)'])
    m(34,0,series('car in travel order',5));m(35,0,['S1 placement','S3 placement','R1 placement','R2 placement','S2 placement/alignment'])
    m(36,0,['lower-right overlap','black upper-left inside gray','black lower-left on gray bottom']);m(37,0,['right-angle (1,1)','right-angle (2,2)','right-angle (3,3)','grid legs and common hypotenuse line through P'])
    m(39,1,['left-leg shaded region','top-base shaded region','right-leg shaded region']);m(40,0,[f'{s} corner leaf boundary' for s in ['upper-left','upper-right','lower-right','lower-left']])
    m(41,0,grid(3,3));m(43,0,['r1c1=1','r2c1=2','r2c2=1','r1c3 shaded','r3c2 shaded']);m(44,0,series('upper face label',4)+series('lower face label',4))
    m(45,0,[f'{month} {group}' for month in ['Jan','Feb','Mar','Apr','May'] for group in ['Drums','Bugles']]);m(49,0,['Z hypotenuse','X leg','Y leg'])
    m(50,1,series('vertical tile',4)+['top horizontal tile']);m(50,2,series('left-boundary edge in top-down order',6))
    m(51,0,['(1,1)','(1,3)','(2,1)','(2,4)','(3,3)','(3,4)','(4,1)','(4,2)','(4,4)']);m(51,1,series('side-view height',4))
    for j in range(3):m(52,j,series('dart-tip field membership',3))
    m(54,0,['Maria left endpoint','Bianca right endpoint','1/8 interval 100m'])
    m(55,0,[f'v{i}-v{i+1}' for i in range(6)]+['v0 label 1','v6 label x'])
    m(56,0,['central overlap white','singly covered gray portion 1','singly covered gray portion 2','protruding flap tip gray'])
    m(58,0,['upper-left placement','central-square placement','lower-right placement','upper-left side 1','central side 3','lower-right side 1','remaining shaded L'])
    m(60,0,series('equally spaced peripheral position',8)+['common center'])
    m(62,0,['circle-square inscription','square side 2','outer-square shading']);m(62,1,['two-by-two circle layout','tangencies including boundary','square side 2','outside-circle shading']);m(62,2,['square-circle inscription','circle diameter 2','outer-circle shading'])
    m(63,0,['(-7,-4)','(-2,6)','(0,0)','(1,6)','(5,-6)']);m(64,0,series('year column X marks',10));m(65,0,list('MNABCDE'))
    m(66,0,['8-by-8 dimensions','P bottom column 6','Q top column 7']);m(67,0,series('central stacked rectangle',9)+['left full-height rectangle','right full-height rectangle'])
    m(68,0,['inlet fork','left fork','right fork','inner merge','left outlet X','central outlet Y','right outlet Y'])
    m(70,0,grid(2,2));m(70,1,['top triangle','right triangle','bottom triangle','left triangle']);m(71,0,grid(2,4));m(72,0,['D on CB','E on AB'])
    m(73,0,['wide left side','tall left side','wide right side','tall right side','wide top level','tall top level'])
    m(74,0,['top contact','bottom contact','front contact','back contact','left contact','right contact'])
    m(75,0,['bottom endpoint','top endpoint','left endpoint','right endpoint','bottom-left daisies','top-right daisies']);m(76,0,series('nested region inside-out',6))
    m(77,0,['full seven-region arrangement','1 in T/L only','2 in T/R only','question mark in triple overlap'])
    m(78,0,[f'column {j+1} {field}' for j in range(4) for field in ['top animal','bottom animal','sum']]);m(79,0,['H-S','S-P','P-L','L-H']);m(80,0,['R(1,1)','R(1,3)','R(2,3)','G(3,4)'])
    m(81,0,['top','upper-right','middle','lower-left','bottom']);m(81,1,['top','bottom','upper-left','lower-left','upper-right','lower-right'])
    m(83,0,[f'{day} {person}' for day in ['M','Tu','W','Th','F'] for person in ['Asha','Sasha']]);m(85,0,series('clockwise vertex',12))
    m(86,0,['Terrasse-4','4-1','1-2','2-3','2-5','3-5']);m(87,0,['circle pair 1-2','circle pair 1-3','circle pair 2-3']);m(88,0,list('ABCD')+['I on AB','II on BC','III on CD'])
    m(89,0,['(1,1)->(1,2)','(1,3)->(1,2)','(2,3)->(2,2)','(2,2)->(2,1)','(3,3)->(3,2)','(3,2)->(3,1)','(3,1)->(2,1)','(2,1)->(1,1)','(2,2)->(1,2)','(2,2)->(3,2)','(2,3)->(1,3)','(2,3)->(3,3)','(2,1)=7','(3,1)=5','(1,3)=?'])
    m(90,0,sum((series(f'{name} occupied cell in listed order',n) for name,n in [('A',8),('B',7),('C',5),('D',8),('E',5)]),[])+['gate columns 4-6'])
    m(92,0,[f'room {x}' for x in grid(5,5)]+[f'horizontal door r{r} c{c}-c{c+1}' for r in range(1,6) for c in range(1,5)]+[f'vertical door c{c} r{r}-r{r+1}' for r in range(1,5) for c in range(1,6)]+['start top third']+[f'exit {c}' for c in 'ABCDE'])
    m(93,0,[f'row {r} dot {c}' for r in range(1,5) for c in range(1,r+1)]);m(94,0,['upper turns on arc','lower turns on PQ']);m(95,0,series('boundary vertex',9))
    m(98,0,['bottom front edge','bottom back edge','left-right upper ridge']);m(98,1,['bottom left edge','bottom right edge','front-back upper ridge'])
    m(99,0,['L/B/R tip identities','L downward line','B upward line and crossing S','U on LR','V on BR','x=angle UBR'])
    # MMStar identifiers follow the serialized source object's own entry order.
    ordered={0:'A-847 method',2:'balance-sheet entry',4:'triangle side',5:'Rec method',7:'algorithm bar',9:'year unit sale',10:'candy bar',11:'country Nobel entry',13:'year percentage',16:'waiting-time cell in column-major source order',21:'number-array cell in row-major order',24:'observed/regression value in given-year order',26:'cost item',28:'Rebecca endpoint then Mint/DarkCyan vertex',30:'year new/used loan entry',32:'bar',33:'category/segment lower then upper endpoint',35:'rectangle side',39:'people bar',41:'letter-grid cell in row-major order',42:'matrix cell in row-major order',55:'directed labeled edge',57:'bar',58:'circuit component connection',59:'year freight value',61:'score/frequency entry',62:'sequence group',63:'named collection',64:'credit then cash month entry',66:'terminal line',68:'stem/leaf entry in displayed order',70:'horizontal bar',72:'category preference series entry',76:'year value',77:'blue bar top-down',78:'forecast field',79:'fry-type/region cell in row-major order',80:'food-web directed edge',83:'pentagon angle binding',85:'month precipitation',89:'bar',92:'series/model Acc entry',93:'menu item price',98:'satisfaction field',99:'route fare'}
    for i,label in ordered.items():v(i,0,series(label,groups['MMStar'][i]['atoms'][0]['subfact_count']))
    for i in [1,25,45]:v(i,0,['ruler left endpoint','ruler right endpoint'])
    for i,counts in [(3,[4,12]),(34,[3,5]),(87,[11,11]),(95,[4,4])]:
        for j,n in enumerate(counts):v(i,j,['solvent volume']+series('dot at source-listed position',n))
    v(6,0,['demanded quantity at330','supplied quantity at330']);v(12,0,series('Portugal year',13)+series('Switzerland year',13)+series('Romania year',8))
    v(14,0,['transparent lidded jug','side handle and spout','powered base','bubbling water']);v(17,0,['wooden flat circular body','metal side band','handle'])
    for j in range(2):v(23,j,['left magnet size','left pole orientation','right magnet size','right pole orientation','gap'])
    v(27,0,['positive NH3 binding','negative carboxylate oxygen binding']);v(29,0,['cabinet hinged door','dial/keypad lock','interior shelves'])
    v(36,0,['A central Earth','D moon below','incident-light direction','orbital-arrow direction']);v(38,0,['flames beneath vessel','bubbles in liquid','separated moving particles above surface']);v(40,0,['heading','displayed sentence'])
    v(44,0,['crossing -2','crossing 3','positive middle interval','negative outer intervals'])
    for j in range(2):v(46,j,['left size','left pole orientation','right size','right pole orientation','gap'])
    v(48,0,['left bar size/orientation','right bar size/orientation','45mm gap']);v(48,1,['left bar size/orientation','right bar size/orientation','27mm gap','cross-pair size match'])
    v(52,0,['I central Earth','A below Earth','sunlight direction'])
    for j in range(2):v(53,j,['left magnet size','left pole orientation','right magnet size','right pole orientation','gap'])
    v(54,0,['L on RT','W on RS','parallel LW/TS marks'])
    v(56,0,[f'{edge} {field}' for edge in ['A-B','B-C','C-D','D-E','E-F'] for field in ['yield with incoming amount binding','destination amount or blank']])
    v(65,0,['air above interface','plastic below interface','incoming 37-degree interface angle','transmitted 53-degree interface angle'])
    for j in range(3):v(67,j,[f'{metric} at lambda {lam}' for metric in ['diversity','attack effectiveness'] for lam in [0,.1,.2]])
    v(69,0,['printed curve equation','shaded x interval','shading to x-axis']);v(75,0,['X and adjacent vertical 5','hypotenuse13 binding','right-angle vertex'])
    v(81,0,['vertical dashed membrane','equal left/right compartments']+series('left dot position',4)+series('right dot position',6))
    v(82,0,['tangent9 from common exterior point','exterior secant x','interior secant24'])
    v(90,0,['deer toward leafy plant','horse toward leafy plant']);v(91,0,['lower right-angle vertex','perpendicular altitude16','left hypotenuse8','right hypotenuse x','right leg y'])
    v(94,0,['a above b','c slope','angle1 location','angle2 location']);v(96,0,['shared range and left endpoint meeting','subsequent Green below Indigo vertices','straight segment joins'])
    out=[]
    for b,rr in groups.items():
        for i,r in enumerate(rr):
            aa=[]
            for j,a in enumerate(r['atoms']):
                if a['subfact_count']==1:keys=['complete source relation/object']
                elif b=='BlindTest':keys=['two left-middle-right straight polylines','shared three horizontal vertex positions','left blue/red vertical order','middle blue/red vertical order','right blue/red vertical order']
                else:keys=maps[b,i,j]
                assert len(keys)==a['subfact_count']
                aa.append(dict(a,subfact_keys=keys,shared_topology='All source-text bindings remain required for exact atom recovery.'))
            out.append(dict(r,atoms=aa,model_outcomes_used=False))
    path=ROOT/'source/D1_shared_unit_map_v1.jsonl';write_rows(path,out)
    save(ROOT/'audit/D1_shared_unit_map_seal_v1.json',dict(at=now(),files={str(path):sha(path),__file__:sha(__file__)},
        source_schema_sha256=sha(ROOT/'source/D1_review_schema_v1.jsonl'),families=len(out),source_content_changed=False,
        rule='Fixed matching identifiers for existing source units; shared topology/bindings remain mandatory for exact atoms. No solved quantities added. Identical map applies to both models.',
        D1_model_outputs_used=False))


if __name__=='__main__':main()
