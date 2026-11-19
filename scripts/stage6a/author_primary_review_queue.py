"""Prospective C1 visual-review queue. These are candidates, not accepted bases."""
import json
import re
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def main():
    source = [json.loads(l) for l in (OUT / 'cohort/semantic_candidate_order.jsonl').read_text().splitlines()]
    specifications = {
        'MathVerse': [
            (754,'55','65','angle label'), (704,'16','18','prism dimension'),
            (684,'19','21','cuboid dimension'), (673,'33.1','35.1','cylinder height'),
            (676,'14.2','16.2','cylinder length'), (786,'4','5','circle radius'),
            (266,'33','43','angle MNQ'), (709,'6','8','pyramid vertical height'),
            (376,'4','5','leg coefficient'), (744,'5','6','inscribed-cylinder height'),
            (638,'17','19','cuboid length'), (707,'9','8','trapezoid upper base'),
            (692,'13','15','pipe length'), (715,'12','14','partial-cylinder length'),
            (651,'8.8','9.8','sphere radius'), (664,'11','12','sphere radius'),
            (771,'7','8','circle radius'), (728,'12','14','cube edge'),
            (635,'12','10','cone vertical height'), (735,'7','8','marked common edge'),
            (773,'40','50','angle m'), (779,'60','65','angle at F'),
            (756,'3','4','right-triangle leg QR'), (431,'12','16','westward distance'),
            (646,'12.5','14.5','cone vertical height'), (313,'6.2','7.2','circle diameter'),
            (307,'5','9','additive angle constant'), (774,'126','136','interior angle'),
            (759,'50','60','known intersecting-line angle'), (380,'3','6','leg radicand'),
            (645,'9','10','half-cone slant height'), (698,'14','16','block length'),
            (385,'10','14','hypotenuse radicand'), (703,'8','9','prism depth'),
            (745,'13','15','cylinder height'), (691,'15','17','quarter-cylinder length'),
            (644,'8','9','cone slant height'), (639,'13','15','pipe length'),
            (777,'80','70','base angle'), (733,'3','4','prism depth'),
            (666,'56.17','66.17','sphere radius'), (690,'20','22','half-cylinder length'),
            (641,'8','10','cylinder height'), (724,'4','5','cube edge additive constant'),
            (714,'10','12','prism length'), (654,'25.36','26.36','hemisphere radius'),
        ],
        'MathVision': [
            (1041,'108','118','known angle'), (2980,'8','6','right-triangle leg'),
            (2934,'30','40','isosceles base angle'), (1142,'17','19','pentagon edge DC'),
            (386,'6','8','hexagon upper edge'), (1658,'50','60','pool length'),
            (1960,'32','37','inscribed angle'), (1951,'70','75','square-side angle'),
            (2910,'5','6','triangle height AC'), (1012,'5','6','rectangle diagonal'),
            (3006,'105','115','cyclic hexagon angle'), (2530,'8','9','trapezoid height'),
            (2912,'21','24','side AC'), (2041,'84','90','subtriangle area'),
            (1805,'26','28','side DB'), (1678,'5','6','garden outer width'),
            (1089,'58','63','angle at B'), (2546,'4','5','point C x-coordinate'),
            (342,'9','16','left square area'), (1272,'50','55','angle CAD'),
            (2718,'6','8','right vertical edge'), (1186,'6','8','stack height'),
            (1529,'3','5','rectangle height'), (1334,'330','320','reflex angle'),
            (208,'8','10','point B x-coordinate'), (2407,'6','8','upper-left area'),
            (3023,'30','40','right-triangle angle'), (3005,'96','90','quadrilateral side XY'),
            (762,'4','5','square edge'), (2525,'10','12','horizontal extent'),
            (2986,'2','4','side BC additive constant'), (784,'4','6','middle vertical step'),
            (754,'12','14','block length'), (2885,'4','5','small triangle base'),
            (2950,'8','10','point C x-coordinate'),
        ],
        'MathVista': [
            (271,'2','4','right segment additive constant'), (678,'16','18','opposite leg'),
            (583,'16','18','side BC'), (737,'23','25','parallelogram base'),
            (822,'12','14','parallelogram base'), (318,'41','43','trapezoid upper base'),
            (242,'3','4','angle A multiplier'), (88,'2','3','right angle-expression multiplier'),
            (757,'15','17','upper secant internal length'), (726,'50','60','arc additive constant'),
            (304,'70','90','known angle'), (206,'15','18','dilated center-to-point distance'),
            (386,'20','22','hypotenuse'), (776,'9','10','inradius'),
            (897,'9','10','opposite leg LK'), (684,'27','29','arc subtractive constant'),
            (819,'8','10','half diagonal'), (716,'16','18','right-triangle altitude'),
            (665,'4','5','adjacent leg'), (160,'15','17','hypotenuse'),
            (238,'25','26','hypotenuse'), (786,'80','70','lower base angle'),
            (333,'13','15','hypotenuse'), (310,'8','9','altitude'),
            (951,'12','20','angle subtractive constant'), (283,'10','12','side additive constant'),
            (816,'9','10','tangent length'), (866,'45','55','angle R'),
            (781,'9','11','half side DG'), (236,'9','11','equal side RT'),
            (804,'8','9','radius'), (114,'17','19','tangent length'),
            (408,'12','15','hypotenuse projection'),
            (925,'5','6','pumpernickel price'), (568,'7','9','Mukilteu-Clinton car fare'),
            (718,'3','4','velvet swirl count'), (359,'7','9','Thursday shell count'),
            (651,'8','10','Canada Nobel count in 1990s'), (831,'305','325','Friday word count'),
            (205,'14','16','three-run frequency'), (746,'46','48','2014 entry count'),
            (144,'3','4','turmeric price'), (45,'14','12','September waiting time'),
            (929,'20','25','mystery game price'), (332,'1937','2037','April miles'),
        ],
    }
    lookup = {r['base_id']: r for r in source}
    review = []
    for dataset, candidates in specifications.items():
        for i, (idx, value, cf, entity) in enumerate(candidates):
            base_id = dataset.lower() + '_' + str(idx)
            r = lookup[base_id]
            question = re.split(r'\n\s*Choices\s*:', r['question'], maxsplit=1, flags=re.I)[0]
            question = re.sub(r'<image\d+>', '', question).replace('\\n', '\n').strip()
            review.append({**r, 'review_order': i, 'status': 'pending_full_resolution_review',
                'proposed_target': dict(value=value, counterfactual=cf, entity=entity),
                'proposed_prompt': question + '\nReason carefully from the figure, then give the requested answer.',
                'selection_inputs': ['source image', 'original question', 'objective editability'],
                'attention_or_causal_data_used': False})
    p = OUT / 'cohort/primary_c1_review_queue.jsonl'
    if p.exists():
        raise FileExistsError(p)
    write(p, review)
    print({d: sum(r['dataset'] == d for r in review) for d in specifications})


if __name__ == '__main__':
    main()
