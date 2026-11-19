"""Additional source-only field annotations from the fixed candidate pool."""


def supplemental_definitions():
    def f(entity, value, alternate, roi, prefix='', suffix=''):
        return dict(entity=entity, value=value, counterfactual=alternate, roi=roi,
                    render_prefix=prefix, render_suffix=suffix)
    def pair(t, x, answer, family, prompt=None):
        row = dict(T=t, X=x, final_answer=answer, family=family)
        if prompt: row['prompt'] = prompt
        return row
    return {
        'mathvision_704': pair(f('small bottom left square side length','2','2.5',[31,269,82,308]),f('bottom right square side length','3','3.5',[345,290,395,325]),'25','seven_square_tiling'),
        'docvqa_7020': pair(f('Packing Slip Number of Animals','565','575',[558,568,690,620]),f('Animals Received actual number','590','580',[552,833,650,877]),'565','animal_shipment_form','What number of animals is listed in the Packing Slip Description? Give the listed number, reasoning from the form.'),
        'docvqa_234': pair(f('Caryophyllene CAS number','87-44-5','87-44-6',[897,1352,1014,1382]),f('Sclareol CAS number','515-03-7','515-03-8',[897,1396,1028,1425]),'87-44-5','chemical_registry_table','What CAS number is printed for Caryophyllene in the compound table? Reason from the document, then answer.'),
        'docvqa_55466': pair(f('Research Phase Salaries 1980 amount','2.5','3.5',[1280,1107,1349,1138]),f('Research Phase Salaries 1981 amount','5.0','6.0',[1480,1106,1561,1136]),'2.5','grant_budget_by_year','Under B. Research Phase, what Salaries amount is listed in the 1980 column? Give the printed number, reasoning from the table.'),
        'docvqa_59428': pair(f('symposium year printed at bottom','1983','1984',[529,1498,648,1546]),f('symposium June start day','13','14',[507,1420,557,1467]),'1983','symposium_cover'),
        'docvqa_32885': pair(f('Scott county population','34,400','35,400',[460,532,580,569]),f('Stoddard county population','26,800','27,800',[460,597,580,634]),'34,400','county_population_table'),
        'docvqa_50881': pair(f('Canadian Head Office city','Ottawa','Toronto',[1182,1672,1258,1694]),f('Pacific Coast Head Office city','San Francisco','Los Angeles',[1165,1648,1302,1670]),'Ottawa','insurance_cover'),
        'mathvista_215': pair(f('Monday miles hiked','10','12',[132,192,157,210]),f('Tuesday miles hiked','2','4',[136,223,155,242]),'8','weekday_count_table'),
        'mathvista_719': pair(f('Tuesday daily low temperature','20','22',[138,192,162,210]),f('Saturday daily low temperature','7','9',[143,99,161,118]),'13','weekday_count_table'),
        'mathvista_584': pair(f('Aubrey arts education donation','16','21',[291,131,326,149],'$'),f('Connor arts education donation','19','14',[291,162,326,181],'$'),'Connor','donation_table'),
        'mathvista_627': pair(f('Abigail trivia score','6','7',[111,69,129,87]),f('Bernie trivia score','10','8',[108,99,130,118]),'6','named_person_count_table'),
        'mathvista_929': pair(f('toy rocket price','65','55',[187,103,218,123],'$'),f('mystery game price','20','30',[187,167,218,187],'$'),'85','item_price_list'),
        'mathvista_404': pair(f('activity beginning at 11:50 AM',"children's class",'adult class',[2,138,158,161]),f('activity beginning at 11:10 AM','figure skating practice','free skate',[2,110,158,134]),"children's class",'activity_schedule'),
        'mathvista_508': pair(f('Saturday number of inn guests','7','3',[159,162,180,180]),f('Wednesday number of inn guests','4','8',[159,69,180,87]),'5','weekday_count_table'),
        'mathvista_696': pair(f('motorcycle price','998.00','898.00',[145,7,207,27],'$'),f('canoe price','562.00','462.00',[145,39,207,59],'$'),'no','item_price_list'),
        'mathvista_331': pair(f('Bonnie web pages visited','84','92',[147,69,173,87]),f('Finn web pages visited','47','55',[147,223,173,243]),'64','named_person_count_table'),
        'mathvision_2608': pair(f('trapezoid upper base BC length','8','10',[258,22,281,54]),f('trapezoid lower base AD length','16','18',[250,149,291,181]),'34','isosceles_trapezoid_perimeter'),
        'mathvision_2666': pair(f('trapezoid upper base BC length','50','52',[412,34,455,67]),f('trapezoid left side AB length','30','32',[96,159,136,191]),'180','right_height_trapezoid_perimeter'),
        'docvqa_364': pair(f('cotton duck 4 flame out time Before rinse','276','286',[586,1239,632,1261]),f('cotton duck 4 flame out time After rinse','128','138',[731,1239,778,1261]),'276','flame_test_table','In the Flame Test of Cotton Ducks table, what flame-out time is listed for cotton duck 4 Before rinse? Reason from the table, then answer.'),
        'docvqa_612': pair(f('Coca-Cola Company sales percentage','42.2','44.2',[818,1757,898,1784]),f('Pepsico sales percentage','16.6','18.6',[818,1792,898,1821]),'42.2%','market_share_table'),
        'docvqa_59563': pair(f('Staff Travel operating amount','8.00','18.00',[1450,1226,1525,1257]),f('Office Supplies Equipment operating amount','9,006.00','9,016.00',[1379,1189,1525,1221]),'8.00','financial_statement','What amount is printed for Staff Travel under Operating in the financial statement? Reason from the document, then give the amount.'),
        'docvqa_5511': pair(f('National Press Club event weekday','Tuesday','Wednesday',[1050,2541,1254,2598]),f('event December day of month','17','18',[1534,2542,1587,2586]),'Tuesday','event_invitation','Which weekday name is printed for the National Press Club event? Give the weekday name, reasoning from the invitation.'),
        'docvqa_56258': pair(f('secured bank loan interest rate','14.75','15.75',[826,1632,916,1656],'','%'),f('Bodies Corporate loan interest rate range','13.2%-15%','12.2%-14%',[842,1744,992,1779]),'14.75%','loan_interest_table'),
        'docvqa_62504': pair(f('Secretary half time requested budget','2,200.00','2,300.00',[1133,769,1287,803]),f('Animal attendant half time requested budget','2,400.00','2,500.00',[1133,735,1287,769]),'2,200.00','research_budget_table'),
        'docvqa_16835': pair(f('Conference and Full Day Tutorial fee','2195','2295',[1480,1046,1574,1083],'$'),f('Conference Only fee','1795','1895',[1480,1089,1574,1126],'$'),'2195','conference_fee_table'),
        'docvqa_57307': pair(f('closing session start time','11:20','11:30',[429,812,486,833]),f('Retinoids and Bladder Cancer start time','10:45','10:35',[429,535,486,555]),'11:20','conference_program','What is the start time of the closing-session Symposium Summary? Reason from the program, then give the start time.'),
        'docvqa_58779': pair(f('RFC number','880036','880037',[1312,318,1495,358]),f('effective date','9/8/88','9/9/88',[1280,526,1445,559]),'880036','handwritten_change_request'),
        'docvqa_52387': pair(f('Number of Extra Displays','14','15',[931,1432,967,1460]),f('Retail Offers Per Display','40','41',[930,1392,967,1420]),'14','promotion_order_form'),
        'docvqa_16440': pair(f('Lint String pieces in core samples','22','23',[329,1341,364,1365]),f('Paper pieces in core samples','4','5',[346,1391,366,1415]),'22','foreign_matter_count_table'),
    }
