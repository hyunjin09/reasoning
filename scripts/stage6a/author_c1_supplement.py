"""Independent source arithmetic for prospective C1 supplemental candidates."""
import json
from scripts.stage6a.inventory import OUT


DEFINITIONS = {
    'mathvision': [
        (2427,[.038,.505,.09,.586],'44','46','Orthogonal decagon perimeter=2*(width12+left heightT+top step2).'),
        (3020,[.393,.230,.424,.286],'54','66','Triangle horizontal base12 and vertical heightT: area6T.'),
        (2504,[.530,.047,.568,.113],'46','56','L polygon area=9*T-4*(T-4)=5*T+16. AB is the top edge.'),
        (2512,[.445,.010,.494,.099],'28','30','Orthogonal L polygon perimeter=2*(outer widthT+height6).'),
        (1146,[.479,.706,.541,.821],'24','28','Perimeter difference=2*(left3+right4+upper2+lowerT).'),
        (2958,[.290,.169,.327,.225],'84','96','Trapezoid QABO has horizontal parallel basesT,12 and height12; area6*(T+12).'),
        (1735,[.443,.706,.530,.877],'45','80','Five congruent right-isosceles triangles span total hypotenuse lengthT. Each hypotenuseT/5, total areaT²/20.'),
        (3004,[.505,.367,.541,.465],'256*pi','(116+14*sqrt(117))*pi','Frustum radii4,10: bases116pi; lateral area14pi*sqrt(T²+36).'),
        (573,[.810,.144,.895,.235],'9','11','After multiplication by0, then+6, then*4, the value is24. Requested next value24-T.'),
        (802,[.490,.900,.577,.963],'56','112','Four congruent right triangles have long leg14 and short legT-28. Total area28*(T-28).'),
        (355,[.235,.231,.305,.349],'34','36','Alternating triangle-perimeter sum cancels each internal edge: T+11+12+20+9-15-13.'),
        (393,[.302,.130,.355,.224],'18','49/3','Circle tangent at right midpoint: radius=(L-8)/2. Upper intersection gives16+(L/2-T)^2=(L-8)^2/4, henceL=T²/(T-4).'),
    ],
    'mathvista': [
        (928,[.890,.637,.967,.731],'5','7','Navy matT minus yellow towel12.'),
        (802,[.751,.038,.876,.125],'69','71','Four pounds silkT plus four pounds canvas8.17: 4*(T+8.17).'),
        (978,[.680,.238,.729,.305],'7','9','Range=max WednesdayT minus minimum Saturday2.'),
        (948,[.600,.218,.688,.293],'11','12','Eight block counts sum88 initially. Replacing Wendy14 by22 increases mean by1.'),
        (245,[.890,.549,.968,.668],'24','26','Grilled steakT plus mushroom pizza11.'),
        (801,[.636,.622,.710,.696],'10','9','Initial counts: value10 three times,9 twice,4 twice. Thursday10 to9 swaps the unique mode to9.'),
        (739,[.852,.231,.966,.331],'23','25','Baking dishT plus cookie jar13.'),
        (312,[.489,.685,.587,.779],'apples','canola','2003 column: peas9,potatoes4,applesT,canola10. Maximum switches from apples20 to canola10 when T8.'),
        (268,[.689,.660,.736,.743],'10.4','11.7','English muffin unit priceT times1.3kg.'),
        (799,[.842,.054,.972,.203],'13','14','Baking dishT plus casserole3.00 plus ice cream scoop6.00.'),
        (517,[.630,.593,.700,.677],'-1','-3','2015 employees22 minus2014 employeesT, over one year.'),
        (824,[.823,.038,.974,.141],'0.13','0.15','Sour apple candyT plus butterscotch0.07.'),
        (584,[.776,.693,.826,.786],'Connor','Aubrey','Arts education AubreyT versus Connor19. Original16<19, counterfactual21>19.'),
        (471,[.721,.584,.777,.671],'8','7','Original largest frequency18 for score8. After replacing it by9, frequency10 for score7 is uniquely largest.'),
        (121,[.784,.629,.831,.702],'5','7','ThursdayT minus Wednesday2, over one day.'),
        (323,[.648,.414,.742,.596],'green','red','Compare absolute point changes: green+T versus red-40. Original25<40, counterfactual45>40.'),
    ],
}


def main():
    path=OUT/'config/primary_c1_authored_semantics.json';records=json.loads(path.read_text())
    for dataset,definitions in DEFINITIONS.items():
        for idx,box,answer,cf,derivation in definitions:
            records.setdefault(f'{dataset}_{idx}',dict(normalized_roi=box,answer=answer,
                counterfactual_answer=cf,answer_audit=derivation,
                semantic_review='Source image, question and independent arithmetic reviewed before C1 generation.',crop_review='pending'))
    records.setdefault('mathvision_389',dict(status='deferred_semantics',crop_review='deferred',
        reason='Counterfactual consistency across all six triangle-area labels not independently established; no model outcome consulted.'))
    path.write_text(json.dumps(records,indent=2)+'\n')
    print('Authored supplemental candidates',sum(map(len,DEFINITIONS.values())))


if __name__=='__main__':main()
