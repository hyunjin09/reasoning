"""Source-only annotations from the saved full-source review sheets.

Coordinates below are provisional until enlarged glyph/semantic-edit review.
No native model outputs or causal/passive scores enter these definitions.
"""
from scripts.stage7a.common import OUT, write_json


def field(entity, value, alternate, box):
    return dict(entity=entity, value=value, counterfactual=alternate, normalized_roi=box)


def main():
    definitions = {
        'mathvista_824': dict(T=field('sour apple candy price', '0.06', '0.08', [.81,.035,.99,.145]),
                             X=field('butterscotch candy price', '0.07', '0.09', [.81,.868,.99,.978]),
                             final_answer='0.13', family='item_price_list'),
        'mathvista_828': dict(T=field('double chocolate cookie dough price per pound', '3', '4', [.795,.195,.99,.305]),
                             X=field('chocolate chip cookie dough price per pound', '5', '6', [.795,.36,.99,.47]),
                             final_answer='2.7', family='unit_price_list'),
        'mathvista_321': dict(T=field('quantity demanded at price $330', '11,000', '21,000', [.30,.70,.46,.80]),
                             X=field('quantity supplied at price $330', '15,400', '10,400', [.72,.70,.89,.80]),
                             final_answer='surplus', family='supply_demand_table'),
        'mathvista_573': dict(T=field('Thursday number of laps', '53', '55', [.59,.31,.71,.40]),
                             X=field('Sunday number of laps', '55', '53', [.59,.74,.71,.83]),
                             final_answer='53', family='weekday_count_table'),
        'mathvista_44': dict(T=field('oval beads price per kilogram', '2', '4', [.67,.035,.99,.125]),
                            X=field('rectangular beads price per kilogram', '3', '5', [.67,.18,.99,.27]),
                            final_answer='18', family='unit_price_list'),
        'mathvista_867': dict(T=field("Dan's Deep Dish pepperoni pizza revenue", '8', '9', [.436,.70,.50,.80]),
                             X=field("Dan's Deep Dish supreme pizza revenue", '14', '15', [.774,.70,.865,.80]),
                             final_answer='22', family='restaurant_pizza_table'),
        'mathvista_412': dict(T=field('black jacket price', '26', '22', [.825,.87,.985,.98]),
                             X=field('pair of shorts price', '11', '7', [.825,.70,.985,.81]),
                             final_answer='no', family='item_price_list'),
        'mathvision_2728': dict(T=field('rectangle side AB length', '5', '7', [.035,.38,.08,.53]),
                               X=field('rectangle side AD length', '6', '8', [.19,.015,.255,.13]),
                               final_answer='13', family='equal_area_rectangle_right_triangle'),
        'docvqa_61616': dict(T=field('Kahului Kaahumanu swimwear phone number', '877-7260', '877-7261', [.235,.491,.307,.503]),
                            X=field('Kihei Azeka Place swimwear phone number', '879-1448', '879-1449', [.228,.503,.307,.515]),
                            final_answer='877-7260', family='local_business_advertisements'),
        'docvqa_1986': dict(T=field("doctor resume exhibit number", 'D2455', 'D3455', [.16,.700,.235,.714]),
                           X=field('transcript page number printed at top right', '23', '24', [.90,.043,.943,.061]),
                           final_answer='D2455', family='deposition_transcript'),
        'docvqa_50516': dict(T=field('article views', '153', '253', [.297,.535,.34,.55]),
                            X=field('online publication day in March 2012', '19', '20', [.379,.434,.404,.448]),
                            final_answer='153', family='journal_download_page'),
        'docvqa_265': dict(T=field('CELANDO pounds', '94.7680', '95.7680', [.472,.276,.571,.294]),
                          X=field('HALWAY pounds', '142.1520', '143.1520', [.46,.291,.58,.312]),
                          final_answer='94.7680', family='ingredient_batch_table'),
        'docvqa_46719': dict(T=field('Placebo baseline total cholesterol mean', '6.335', '7.335', [.25,.325,.294,.34]),
                            X=field('Placebo twelve-week total cholesterol mean', '5.761', '6.761', [.25,.349,.294,.366]),
                            prompt='What is the mean total cholesterol for the Placebo group at Baseline in Table 1? Give the mean before the plus-minus sign. Reason from the table, then answer.',
                            final_answer='6.335', family='clinical_mean_sd_table'),
        'mathvista_312': dict(T=field('Apples price in 2003', '20', '8', [.46,.67,.61,.77]),
                             X=field('Canola price in 2003', '10', '30', [.46,.84,.61,.94]),
                             final_answer='apples', family='crop_price_year_table'),
        'mathvista_146': dict(T=field('Lorenzo number of science articles', '9', '7', [.60,.89,.66,.96]),
                             X=field('Sophia number of science articles', '5', '3', [.60,.60,.66,.67]),
                             final_answer='4', family='named_person_count_table'),
        'mathvista_332': dict(T=field('January miles', '5,936', '7,936', [.64,.35,.96,.46]),
                             X=field('April miles', '1,937', '2,937', [.64,.84,.96,.95]),
                             final_answer='7873', family='month_measurement_table'),
        'mathvista_799': dict(T=field('baking dish price', '4.00', '5.00', [.83,.07,.99,.22]),
                             X=field('casserole dish price', '3.00', '7.00', [.83,.57,.99,.72]),
                             final_answer='13', family='item_price_list'),
        'mathvista_886': dict(T=field('Greenwood number of stores', '8', '1', [.69,.60,.76,.68]),
                             X=field('Riverside number of stores', '2', '9', [.69,.46,.76,.53]),
                             final_answer='6', family='named_place_count_table'),
        'mathvista_933': dict(T=field('European vacation package price', '7,670', '8,670', [.85,.43,.985,.54]),
                             X=field('Australian vacation package price', '1,936', '2,936', [.85,.63,.985,.74]),
                             final_answer='9606', family='item_price_list'),
        'mathvista_87': dict(T=field('quantity demanded at price $790', '5,100', '17,100', [.30,.675,.45,.78]),
                            X=field('quantity supplied at price $790', '14,700', '4,100', [.72,.675,.89,.78]),
                            final_answer='surplus', family='supply_demand_table'),
        'mathvista_925': dict(T=field('pumpernickel bread crumbs price per pound', '5', '7', [.835,.08,.865,.22]),
                             X=field('whole grain bread crumbs price per pound', '4', '8', [.835,.575,.865,.715]),
                             final_answer='19.5', family='unit_price_list'),
        'mathvista_389': dict(T=field('quantity demanded at price $320', '20,000', '10,000', [.30,.345,.47,.45]),
                             X=field('quantity supplied at price $320', '12,500', '25,000', [.72,.345,.89,.45]),
                             final_answer='shortage', family='supply_demand_table'),
        'mathvista_524': dict(T=field('frequency of sledding three times', '0', '2', [.735,.825,.78,.94]),
                             X=field('frequency of sledding twice', '17', '7', [.72,.65,.785,.78]),
                             final_answer='0', family='frequency_table'),
        'mathvista_268': dict(T=field('English muffins price per kilogram', '8', '9', [.717,.695,.75,.79]),
                             X=field('hamburger buns price per kilogram', '7', '6', [.717,.195,.75,.29]),
                             final_answer='10.4', family='unit_price_list'),
        'docvqa_60463': dict(T=field('INTRODUCTION page number in the table of contents', '3', '4', [.864,.209,.883,.223]),
                            X=field('SEXUALITY CHANGES section preliminary discussion guide page number', '7', '9', [.864,.309,.883,.323]),
                            prompt='In the table of contents, what page number is listed for INTRODUCTION? Reason from the document, then give the page number.',
                            final_answer='3', family='document_table_of_contents'),
        'docvqa_60403': dict(T=field('enclosed check amount', '419.00', '519.00', [.516,.535,.597,.545]),
                            X=field('recipient La Jolla ZIP code', '92093', '92094', [.282,.466,.35,.48]),
                            prompt='What dollar amount is the enclosed check in the letter? Reason from the document, then give the amount.',
                            final_answer='419.00', family='business_letter'),
    }
    # Native-pixel corrections after enlarged crop/component review. Approximate
    # coordinate failures are preserved in audit/source_edit_review_v1.json.
    corrected = {
        'mathvista_824': ([195,7,239,25],[195,167,239,185]),
        'mathvista_573': ([129,69,151,86],[129,162,151,179]),
        'mathvision_2728': ([44,164,67,199],[193,33,217,68]),
        'docvqa_61616': ([414,1101,512,1119],[402,1123,499,1142]),
        'docvqa_1986': ([288,1528,389,1557],[1549,99,1590,127]),
        'docvqa_50516': ([784,1916,850,1951],[860,1558,905,1593]),
        'docvqa_265': ([817,603,960,632],[799,636,960,666]),
        'docvqa_46719': ([557,646,634,676],[557,688,631,716]),
        'mathvista_312': ([104,131,124,148],[104,162,124,179]),
        'mathvista_332': ([79,69,120,86],[79,162,120,179]),
        'mathvista_799': ([177,7,221,26],[177,71,221,90]),
        'mathvista_886': ([158,131,170,147],[158,100,170,117]),
        'mathvista_933': ([294,71,336,88],[294,103,336,120]),
        'mathvista_87': ([105,131,160,149],[253,131,310,149]),
        'mathvista_925': ([259,8,280,27],[259,72,280,91]),
        'mathvista_389': ([106,69,160,87],[255,69,310,87]),
        'mathvista_524': ([257,140,270,156],[253,113,274,130]),
        'mathvista_268': ([178,136,272,156],[178,40,272,60]),
        'docvqa_60463': ([4615,1356,4665,1438],[4620,1974,4676,2057]),
        'docvqa_60403': ([858,1168,980,1198],[483,1016,585,1045]),
    }
    for key, boxes in corrected.items():
        for role, box in zip(['T','X'], boxes):
            definitions[key][role]['roi'] = box
    for role in ['T','X']:
        definitions['docvqa_61616'][role]['light_foreground'] = True
    for key in ['mathvista_799','mathvista_925','mathvista_268']:
        for role in ['T','X']:
            definitions[key][role]['render_prefix'] = '$'
            if key == 'mathvista_268': definitions[key][role]['render_suffix'] = '/kilogram'
    for key in ['mathvista_824','mathvista_828','mathvista_44','mathvista_867','mathvista_412']:
        for role in ['T','X']:
            definitions[key][role]['render_prefix'] = '$'
            if key == 'mathvista_828': definitions[key][role]['render_suffix'] = ' per lb'
            if key == 'mathvista_44': definitions[key][role]['render_suffix'] = '/kilogram'
    from scripts.stage7a.source_supplement import supplemental_definitions
    definitions.update(supplemental_definitions())
    definitions['docvqa_7020']['T']['preserve_native_boxes'] = [[558,616,690,622]]
    for key, row in definitions.items():
        row.update(base_id=key, status='provisional_coordinates',
                   source_review='Full source image and original question read on Stage7A contact sheet; field identity and truth annotated without model outputs.',
                   edit_review='pending enlarged original/sham/semantic-edit review',
                   selection_used_model_outputs=False)
    write_json(OUT / 'annotations/provisional_source_definitions.json', definitions)
    exclusions = {
        'mathvista_860': 'Stem-and-leaf claim requires joint stem/leaf binding; not a singleton editable numeric field in this initial source pass.',
        'mathvision_213': 'Diagram has no localized numeric fact independent of the question; relation-specific edit not authored.',
        'mathvision_2983': 'Single numeric hypotenuse label with supplied trigonometric relation; no suitable distinct confusable field.',
        'mathvision_2389': 'Ten-number cyclic constraint; localized edit consistency not established.',
        'mathvision_2737': 'Lengths are supplied in the question, not independently labeled visual fields.',
        'mathvision_2683': 'Multiple answer-option plots; no singleton editable numeric field.',
        'mathvision_1150': 'Required length is supplied in question; image topology claim needs a different semantic edit.',
        'mathvision_886': 'Dimensions supplied in question; no localized numeric fields.',
        'mathvision_2490': 'Visible side lengths are repeated in the question.',
        'mathvision_207': 'No independent numeric labels; geometric relations are given in the question.',
        'mathvision_848': 'Visible length is repeated in question.',
        'mathvision_2345': 'Visible angle values are repeated in question.',
        'mathvision_1899': 'No localized numeric field in source image.',
        'docvqa_42167': 'Question asks an axis name; image-curve/axis semantic edit not authored in this numeric-field slice.',
        'docvqa_63183': 'Count of objectives is distributed over list entries; not a single localized numeric field.',
    }
    write_json(OUT / 'annotations/source_review_exclusions.json', exclusions)
    print('Provisional source pairs', len(definitions), 'source-only exclusions', len(exclusions))


if __name__ == '__main__':
    main()
