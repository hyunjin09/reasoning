"""Prospective C2 field pairs, independently read from the source documents."""
import json
from scripts.stage6a.inventory import OUT


def designs():
    return [
        (57889,[609,1335,743,1379],[609,1620,800,1683],
         'WP2(2)','WP2(4)','Mid 1999','Late 1999/Early 2000',[
             'What Target Date is listed for WP2(2)?',
             'In the Phase 2 Papers table containing WP2(2), what Target Date is listed for WP2(4)?',
             'What target date is in the second row under Phase 2 Papers?',
             'What target date is in the fourth row under Phase 2 Papers?']),
        (65115,[563,1579,755,1677],[563,1694,773,1800],
         'Snack Bar','Marine Store','3','4',[
             'What building number contains the Snack Bar in the list?',
             'In the numbered list containing the Snack Bar, what building number contains the Marine Store?',
             'What number starts the list entry containing Pool/Patio Deck?',
             'What number starts the list entry containing Fuel Dock?']),
        (51586,[223,317,558,370],[574,665,681,710],
         'letter date','recipient ZIP code','December 29, 1976','20005',[
             'What is the letter date?',
             'On the letter with the letter date, what ZIP code appears in the recipient address?',
             'What complete value appears on the isolated typed line between the letterhead and the recipient address?',
             'Which five digits end the last line of the recipient address?']),
        (60971,[849,619,928,659],[1209,684,1301,722],
         'P.O. Box','ZIP code','1028','65101',[
             'What P.O. Box number is printed in the address?',
             'In the address containing the P.O. Box, what ZIP code is listed?',
             'Which four digits end the second-to-last printed address line?',
             'Which five digits end the last printed address line?']),
        (52481,[247,319,288,356],[247,585,288,622],
         'Voluntary Issues','Regulatory Issues','1','2',[
             'What agenda number is assigned to Voluntary Issues?',
             'In the agenda containing Voluntary Issues, what number is assigned to Regulatory Issues?',
             'What number precedes the first underlined agenda heading?',
             'What number precedes the second underlined agenda heading?']),
        (58683,[1070,581,1141,615],[1070,540,1141,580],
         'Budget History','Weekly Activity','25.00','15.00',[
             'What Cost is quoted for the Budget History report under Price Quotation?',
             'In the support-services table containing Budget History, what Cost is quoted for the Weekly Activity report under Price Quotation?',
             'What cost is in the second service row under Price Quotation?',
             'What cost is in the first service row under Price Quotation?']),
        (48149,[995,396,1366,444],[1455,232,1632,271],
         'letter date','telephone number','February 13, 1979','(202) 452-1300',[
             'What is the letter date?',
             'On the letter with the letter date, what telephone number is printed in the header?',
             'What date is typed on its own line below the letterhead and above the recipients?',
             'What number is printed beneath Telephone in the upper-right corner?']),
        (15351,[277,1560,302,1603],[326,1560,373,1603],
         'current page','total pages','3','12',[
             'What current page number is shown in the footer?',
             'In the footer containing the current page number, how many total pages are stated?',
             'Which number appears immediately before the word of in the lower-left footer?',
             'Which number appears immediately after the word of in the lower-left footer?']),
        (44271,[701,937,900,981],[701,1012,947,1057],
         'Purpose/Objectives','Inclusion/Exclusion Criteria','Protocol; p. 2','Protocol; pp. 5-7',[
             'What Section is listed for Purpose/Objectives in the meeting topics table?',
             'In the table containing Purpose/Objectives, what Section is listed for Inclusion/Exclusion Criteria?',
             'What text is in the middle column of the first meeting-topic row?',
             'What text is in the middle column of the second meeting-topic row?']),
        (4440,[1430,1235,1640,1338],[225,154,586,250],
         'calendar year','calendar month','2006','September',[
             'What year is shown on the calendar?',
             'On the calendar showing a year, what month is named?',
             'Which four digits are inside the lower-right black rectangle?',
             'What word is inside the upper-left black rectangle?']),
        (50316,[262,511,506,566],[509,734,790,782],
         'office phone number','home phone number','3266200','3255543',[
             'What office phone number is written on the Phone line?',
             'On the message slip with the office phone number, what home phone number is written in the message?',
             'What seven-digit number is on the long ruled line directly above the checkboxes?',
             'What seven-digit number ends the handwritten message line?']),
        (56368,[665,1140,697,1183],[618,1740,648,1779],
         'Figure number','page number','2','7',[
             'What Figure number identifies the bar chart?',
             'On the page with the Figure number beneath the chart, what page number is printed near the bottom?',
             'Which single digit follows the word directly beneath the bar chart?',
             'Which single digit is centered near the bottom below the paragraphs?']),
        (58269,[1322,652,1450,692],[1200,652,1325,692],
         '2006 options granted','2005 options granted','60,95,625','14,48,071',[
             'How many options were granted or allocated in 2006 in the upper table?',
             'In the upper options table containing 2006, how many options were granted or allocated in 2005?',
             'What number is in the last year column before Total in the upper options-granted table?',
             'What number is in the second-to-last year column before Total in the upper options-granted table?']),
        (56412,[1710,322,1781,370],[1470,674,1535,718],
         '1980 SCN Direct','1979 SCN Direct','300','205',[
             'What value is printed above the SCN Direct bar for 1980?',
             'In the chart containing the 1980 SCN Direct bar, what value is printed above the SCN Direct bar for 1979?',
             'What value is printed above the tallest bar in the rightmost year group?',
             'What value is printed above the tallest bar in the second year group from the right?']),
        (53573,[330,1180,411,1228],[330,1586,411,1629],
         'Salem easel card','Salem display','25%','75%',[
             'What percentage of the time was the Salem easel card placed?',
             'In the section containing the Salem easel card question, what percentage of the time was the display placed?',
             'What percentage is printed under the first question beneath the second boxed heading?',
             'What percentage is printed under the third question beneath the second boxed heading?']),
        (50879,[456,291,512,344],[764,205,813,238],
         'receipt number','P.O. Box','82','3013',[
             'What receipt number appears above Received?',
             'On the receipt showing its receipt number, what P.O. Box is printed beneath the dealer heading?',
             'What two-digit identifier appears near the upper left above Received?',
             'Which four digits follow P.O. Box beneath the dealer heading?']),
        (18508,[318,596,411,632],[318,688,411,724],
         'B.S. degree','M.S. degree','1969','1973',[
             'In what year was the B.S. degree awarded?',
             'In the education list containing the B.S. degree, in what year was the M.S. degree awarded?',
             'Which year starts the second line of the first education entry?',
             'Which year starts the second line of the second education entry?']),
        (56580,[787,180,886,214],[832,159,926,190],
         'Sao Paulo','Rio de Janeiro','258-1222','224-7727',[
             'What telephone number is printed for Sao Paulo at the top of the receipt?',
             'In the header listing Sao Paulo, what telephone number is printed for Rio de Janeiro?',
             'What telephone number ends the second address line at the top of the receipt?',
             'What telephone number ends the first address line at the top of the receipt?']),
        (39864,[816,819,902,864],[816,720,902,765],
         'Carbohydrates','Protein','27.8','11.5',[
             'What Carbohydrates value is listed for Atole in the 1969–1971 period?',
             'In the nutrient table containing Carbohydrates, what Protein value is listed for Atole in the 1969–1971 period?',
             'What is the leftmost numeric value in the fourth nutrient row?',
             'What is the leftmost numeric value in the second nutrient row?']),
        (55213,[1048,867,1210,904],[1048,907,1210,944],
         'Domestic Refrigerators','Commercial Refrigerators','4.0 - 8.0','3.0 - 5.4',[
             'What cost range is listed for Domestic Refrigerators?',
             'In the cost table containing Domestic Refrigerators, what range is listed for Commercial Refrigerators?',
             'What range is in the third cost-category row of the boxed table?',
             'What range is in the fourth cost-category row of the boxed table?']),
        (19093,[244,523,531,563],[204,440,495,480],
         'Division','Title','Product Evaluation','Senior R&D Chemist',[
             'What Division is entered on the documentation approval form?',
             'On the form with a Division field, what Title is entered for S. Keith Cole?',
             'What text is entered on the ruled line between Title and Date?',
             'What text is entered on the ruled line immediately below Name?']),
        (3135,[674,925,776,960],[680,958,770,993],
         'Silica','Iron','37.8','3.1',[
             'What parts-per-million value is listed for Silica in the left Analysis table?',
             'In the Analysis table containing Silica, what parts-per-million value is listed for Iron?',
             'What numerical value is in the first data row of the left Analysis table?',
             'What numerical value is in the second data row of the left Analysis table?']),
        (61355,[236,1876,362,1908],[236,1904,362,1937],
         'Kauai reservation hotline','Maui reservation hotline','245-9622','877-6626',[
             'What is the Kauai reservation hotline in the Rent-a-Jeep advertisement?',
             'In the Rent-a-Jeep advertisement listing the Kauai reservation hotline, what is the Maui reservation hotline?',
             'What telephone number is on the first island line beneath Reservation Hotline in the jeep advertisement?',
             'What telephone number is on the second island line beneath Reservation Hotline in the jeep advertisement?']),
        (5611,[1674,376,2040,449],[1730,178,1950,244],
         'Delivery Point','Effective Date','Phipps Bend','3-19-01',[
             'What Delivery Point is handwritten in the upper-right block?',
             'On the profile listing a Delivery Point, what Effective Date is handwritten?',
             'What handwritten place name fills the bottom line of the upper-right block?',
             'What hyphen-separated value fills the top completed line of the upper-right block?']),
        (6351,[321,453,518,495],[321,495,518,535],
         'Telephone No.','Fax No.','336-741-1781','336-741-5334',[
             'What Telephone No. is printed for Rebecca Badgett?',
             'In Rebecca Badgett\'s contact block containing Telephone No., what Fax No. is printed?',
             'What number appears on the first numeric line directly below Rebecca Badgett\'s name and department?',
             'What number appears on the second numeric line directly below Rebecca Badgett\'s name and department?']),
        (6775,[416,747,524,790],[610,938,643,990],
         'Date','Total Pieces Faxed','6/6/96','1',[
             'What Date appears below the recipient on this fax?',
             'On this fax containing the Date, what Total Pieces Faxed is listed?',
             'What slash-separated value is on the line directly below the recipient?',
             'What single digit is at the end of the line immediately above Including Cover?']),
        (58332,[190,493,285,538],[192,555,286,605],
         'Zero Time','Out of Chamber','2:00','4:00',[
             'What time is scheduled for Zero Time in the chamber?',
             'On the schedule containing Zero Time, what time is listed for Out of Chamber?',
             'What time appears in the third timed row of the schedule?',
             'What time appears in the fourth timed row of the schedule?']),
        (4930,[1230,296,1560,361],[1160,1190,1320,1251],
         'Effective Date','delivery ZIP code','3-28-2001','37074',[
             'What is the Effective Date on this form?',
             'On the form containing the Effective Date, what ZIP code is in the Point of Delivery address?',
             'What handwritten value is on the ruled line directly beneath Attachment 2?',
             'Which five digits end the bold address block in the middle of the page?']),
        (63596,[1300,666,1438,716],[1300,738,1438,791],
         'Frances E. Brock','Irene Karl','465.00','333.33',[
             'What salary amount is entered for Frances E. Brock in the lower journal entry?',
             'In the journal entry listing Frances E. Brock, what salary amount is entered for Irene Karl?',
             'What amount appears in the first employee row of the lower journal entry?',
             'What amount appears in the second employee row of the lower journal entry?']),
        (49234,[984,1690,1066,1744],[1017,1787,1045,1824],
         'workshop date','Lecture Hall','1987','3',[
             'What year is printed in the workshop date?',
             'On the cover with the workshop date, what Lecture Hall number is listed?',
             'Which four-digit number ends the line directly above the lecture hall line?',
             'Which digit follows the hash symbol on the line directly below the dated line?']),
        (50717,[1160,1300,1457,1343],[1160,1328,1469,1365],
         'NMD1','NMD2','STH Replacement, GC-MSD','Robotics/Analytical Chemist',[
             'What does NMD1 stand for in the footnotes?',
             'In the footnotes containing NMD1, what does NMD2 stand for?',
             'What definition follows the equals sign in the first of the three lower-right footnotes?',
             'What definition follows the equals sign in the second of the three lower-right footnotes?']),
        (7014,[1250,308,1426,357],[166,718,351,766],
         'Statement Date','Date Sent','12/13/99','11/19/99',[
             'What is the Statement Date in the upper-right table?',
             'On the memorandum with the Statement Date, what Date Sent is listed in the middle table?',
             'What slash-separated value is in the middle column of the upper-right three-column table?',
             'What slash-separated value is in the first column of the long table across the middle?']),
    ]


def main():
    path=OUT/'config/primary_c2_authored_semantics.json'
    records=json.loads(path.read_text()) if path.exists() else {}
    for idx,roi,other_roi,entity,other_entity,answer,other_answer,prompts in designs():
        key=f'docvqa_{idx}'
        records.setdefault(key,dict(base_id=key,roi=roi,other_roi=other_roi,
            entity=entity,other_entity=other_entity,answers=[answer,other_answer],prompts=prompts,
            semantic_review='Full document independently read before primary inference; two distinct fields and four natural prompts.',
            roi_crop_review='pending',attention_or_causal_data_used=False))
    path.write_text(json.dumps(records,indent=2)+'\n');print('Authored C2 families',len(records))


if __name__=='__main__':main()
