"""Explicit source-image review and independent local/final ground truth for C1.

Normalized boxes are authoring coordinates only; released assets use integer
native-pixel rectangles and receive a separate crop/pixel audit.
"""
import json
import math
from scripts.stage6a.inventory import OUT


def r(value, digits=2):
    return f'{value:.{digits}f}'


def authored():
    pi = math.pi; sqrt = math.sqrt
    # base ID, normalized target review rectangle, original answer, CF answer,
    # independent derivation (including any source answer discrepancy).
    return [
        (754,[.235,.355,.309,.450],'50','40','Triangle angles: 180-55-75=50; CF180-65-75=40.'),
        (704,[.861,.583,.939,.658],'534','562','Stepped cross-section area=17*8+4*(h-8); boundary perimeter=2*(17+h); depth3. SA=2*area+3*perimeter.'),
        (673,[.606,.485,.697,.548],r(3*pi*10.5**2+2*pi*10.5*33.1),r(3*pi*10.5**2+2*pi*10.5*35.1),'Hemisphere plus cylinder, exposed base included: SA=3*pi*r^2+2*pi*r*h; r10.5mm.'),
        (786,[.412,.656,.477,.764],'2','2.5','Small circle passes through large center and is internally tangent; its diameter equals large radius4, CF5.'),
        (709,[.396,.384,.439,.449],r(100+20*sqrt(61),1),r(100+20*sqrt(89),1),'Square pyramid base10cm, vertical height6cm: SA=100+20sqrt(25+h^2). Original dataset unit m² is incorrect; image uses cm.'),
        (376,[.005,.444,.070,.522],'4*sqrt(3)','5*sqrt(3)','45-45-90 triangle; both legs equal the single stated leg.'),
        (638,[.259,.856,.307,.925],r(6*sqrt(17**2+12**2)),r(6*sqrt(19**2+12**2)),'Vertical triangular divider area=0.5*height12*base_diagonal sqrt(length^2+12^2).'),
        (707,[.379,.181,.419,.244],r(105+3*(26+sqrt(34))),r(100+3*(25+sqrt(41))),'Right trapezoid bases9,12,height5, prismdepth3. Ends=(a+12)*5; lateral=3*(a+12+5+sqrt(25+(12-a)^2)).'),
        (692,[.567,.610,.620,.668],r(260*pi),r(300*pi),'Pipe length13, outer radius6, inner radius4: pi*(36-16)*length.'),
        (715,[.638,.772,.700,.839],r(1.5*pi*25+1.5*pi*5*12+2*5*12),r(1.5*pi*25+1.5*pi*5*14+2*5*14),'Three-quarter cylinder radius5: two ends1.5*pi*r², curved1.5*pi*r*h, two cutfaces2*r*h.'),
        (651,[.510,.358,.595,.434],r(4*pi*8.8**3/3),r(4*pi*9.8**3/3),'Sphere V=4*pi*r^3/3.'),
        (664,[.541,.402,.609,.469],r(4*pi*11**2),r(4*pi*12**2),'Sphere SA=4*pi*r².'),
        (771,[.292,.231,.339,.319],'49','64','Isosceles triangle subtends diameter2r; height r, area r².'),
        (728,[.229,.927,.295,.991],'1728','2744','Cube V=edge³. Dataset144cm³ is inconsistent with the visible12cm cube; corrected independently to1728cm³.'),
        (635,[.160,.401,.212,.491],'10','2*sqrt(69)','Cone diameter=2sqrt(slant13²-height²); height12 then10.'),
        (735,[.000,.776,.041,.839],'3136','4096','Cross-section comprises four equal squares of side7; depth16. Volume=4*s²*16.'),
        (773,[.212,.433,.268,.496],'15','25','Vertical angle equals40, split into25+x; CF50 givesx25.'),
        (779,[.879,.345,.944,.417],'65','60','Three concurrent straight lines and triangle sums give x=270-(50+60+50+45). Change angleF60 to65.'),
        (756,[.622,.360,.680,.451],'13','20','Shared hypotenuse QS: a²+b²=QR²+RS²=3²+2²; CF4²+2².'),
        (431,[.457,.093,.519,.177],'15','sqrt(337)','Pythagoras: sqrt(westward_distance²+9²).'),
        (646,[.426,.498,.532,.549],r(pi*4.1**2*12.5/3,1),r(pi*4.1**2*14.5/3,1),'Cone volume=pi*r²*h/3 with radius4.1.'),
        (313,[.395,.296,.586,.433],r(pi*3.1**2,1),r(pi*3.6**2,1),'Marked line is diameter6.2cm. Circle area=pi*(diameter/2)².'),
        (307,[.253,.618,.302,.716],'43','42','Angles(x-1)+(3x+c)=180; x=(181-c)/4 and requested RCM=x-1. c5 then9.'),
        (774,[.452,.548,.562,.642],'72','92','a+b=180-T; top x=180-2*(a+b)=2T-180.'),
        (759,[.537,.387,.609,.467],'65','60','2y+T=180 from intersecting lines.'),
        (380,[.057,.500,.113,.570],'1','sqrt(2)','30-60-90 triangle; short leg=long leg/sqrt3. Edit radicand3 to6.'),
        (645,[.391,.265,.424,.330],r(pi*1.5**2*sqrt(81-1.5**2)/6),r(pi*1.5**2*sqrt(100-1.5**2)/6),'Half cone with base diameter3, slant9. V=pi*r²*sqrt(l²-r²)/6.'),
        (698,[.673,.700,.724,.773],r(14*(80-4*pi)),r(16*(80-4*pi)),'Rectangular block cross-section10*8 minus cylindrical hole pi*2²; multiply length.'),
        (385,[.509,.357,.584,.461],'sqrt(30)/2','sqrt(42)/2','Adjacent leg to30° equals sqrt(T)*cos30.'),
        (703,[.805,.736,.854,.846],'388','426','Trapezoid bases10,18,legs5,height3: two ends84, perimeter38. Depth8 gives388; CF9 gives426. Dataset338 is an arithmetic error.'),
        (745,[.767,.503,.984,.585],'14','16','Cylinder radius3, height13: diagonal sqrt(h²+6²), rounded down as requested.'),
        (691,[.486,.532,.542,.619],r(pi*49*15/4,1),r(pi*49*17/4,1),'Visible right-angle cross-section is quarter-circle radius7, despite source wording halfpipe. V=pi*r²*length/4.'),
        (644,[.662,.286,.700,.351],r(4*pi*sqrt(60)/3),r(4*pi*sqrt(77)/3),'Cone radius2, slant8 then9; height=sqrt(slant²-4).'),
        (639,[.578,.565,.633,.644],r(520*pi),r(600*pi),'Pipe outer radius7, inner3: cross-section40*pi, length13 then15.'),
        (777,[.403,.793,.465,.861],'80','70','OA=OB are radii; base angles equal the marked80°, CF70°.'),
        (733,[.154,.060,.203,.148],'399','532','Two congruent trapezoids each bases14,5 andheight7: total cross-section133, prismdepth3 then4.'),
        (690,[.411,.337,.459,.427],r(160*pi),r(176*pi),'Half-cylinder front labeled diameter8, so radius4; length20 then22. V=0.5*pi*4²*length.'),
        (641,[.654,.444,.689,.527],r(288*pi),r(360*pi),'Cylinder radius6, height8 then10; V=pi*r²*h.'),
        (724,[.351,.889,.393,.966],'x^3+12*x^2+48*x+64','x^3+15*x^2+75*x+125','Cube edge x+4 thenx+5; expand cube.'),
        (714,[.721,.817,.789,.891],r(75+10*(17+sqrt(61))),r(75+12*(17+sqrt(61))),'House-shaped prism: two ends75; cross-section perimeter17+sqrt61; length10 then12.'),
        (654,[.246,.267,.374,.364],r(2*pi*25.36**3/3,3),r(2*pi*26.36**3/3,3),'Hemisphere radius is marked on the dashed vertical center-to-top segment; V=2*pi*r³/3.'),
    ]


def authored_mathvision():
    return [
        (1041,[.252,.246,.360,.326],'52','62','Intersecting-line grey angle=T+124-180.'),
        (2980,[.651,.414,.687,.496],'3/5','4/5','sinX=sqrt(10²-T²)/10; adjacent leg8 then6.'),
        (2934,[.085,.667,.140,.803],'15','20','AB=AC, AC=CX. Exterior angle ACX=180-T; base angle AXC=T/2.'),
        (1142,[.503,.050,.649,.192],'A','A','Tangent radii solve adjacent sums. For CD17, radii(A,B,C,D,E)=(10,6,8,9,4); CD19 gives(11,5,9,10,3). Local edge and radius readouts change; final argmax staysA, which is retained without outcome filtering.'),
        (386,[.463,.228,.524,.310],'70','72','Hexagon edge directions imply unknown-left-edge sum=15+11; perimeter=T+12+2*(15+11).'),
        (1658,[.350,.108,.469,.213],'40','48','Time equality6L/v=5*2(L+W)/(3v) givesW=0.8L.'),
        (1960,[.193,.490,.265,.579],'9','14','Isosceles radii and inscribed-angle theorem: x=T-(90-67).'),
        (1951,[.397,.310,.494,.415],'50','45','Square sides are perpendicular; equilateral side directions differ60°. Requested gap=120-T.'),
        (2910,[.031,.465,.059,.513],'40/9','24/5','Crossing right-triangle hypotenuses intersect at height4*T/(4+T); baseAB4, area=8*T/(4+T).'),
        (1012,[.584,.523,.666,.659],'10','12','Inscribed rectangle diagonal equals radiusT; circle diameter=2T. Other rectangle edge4 remains feasible.'),
        (3006,[.525,.895,.616,.956],'145','135','Alternating interior angles of cyclic hexagon sum360: alpha=360-110-T.'),
        (2530,[.270,.424,.314,.522],'64','72','Shaded trapezoid parallel bases10,6 and heightT; area8T.'),
        (2912,[.051,.407,.103,.490],'14','16','Angle-bisector theorem AX/30=AC/45.'),
        (2041,[.505,.377,.558,.432],'315','325','Concurrent cevians: unknown upper-right area70; unknown upper-left area2T/3. Total=5T/3+175, from triangle shared-altitude ratios.'),
        (1805,[.156,.617,.241,.733],'9/4','19/8','Shared angleA: [ADE]/[ABC]=(AD/AB)*(AE/AC)=(10+T)/10*15/24.'),
        (1678,[.493,.055,.564,.240],'24','26','Orthogonal boundary horizontal lengths sum2T+8 and vertical lengths sum6; P=2T+14.'),
        (1089,[.326,.799,.392,.868],'51','56','Two triangle sums using intersections: angleD=180-93-T, angleA=180-100-angleD=T-7.'),
        (2546,[.704,.223,.740,.297],'8','10','Parallelogram upper baseBC has length Cx because B lies on y-axis; height2, area2*Cx. A adjusts consistently with D(3,0).'),
        (342,[.185,.603,.240,.729],'13','20','Tilted-square side has orthogonal projections sqrt(left_area),sqrt(right_area). Its area is their sum, T+4.'),
        (1272,[.350,.680,.438,.788],'65','62.5','ABC angles75,75,30 implyAC=BC=AD. TriangleACD is isosceles with apexT; base angle(180-T)/2.'),
        (2718,[.678,.725,.726,.845],'5','7','Sum of upward/downward orthogonal boundary steps gives X=T-1.'),
        (1186,[.040,.377,.089,.451],'12','16','Four rows contain2+3+4+5=14 congruent rectangles, each area(10/5)*(T/4); subtract triangle10*T/2. Shaded area2T.'),
        (1529,[.040,.625,.105,.752],'12','20','Tilted rectangle has baseDB and altitude fromC toDB; its area=2*[DBC]=original rectangle width4*heightT.'),
        (1334,[.608,.068,.751,.147],'40','30','Three tip angles formed around the marked90° crossing sum90. Top interior=360-T; requested angle=90-(360-T)-20.'),
        (208,[.714,.417,.751,.488],'4','2*sqrt(5)','Circle diameter endpoints(-2,0),(T,0); settingx0 in circle equation givesd²=2T.'),
        (2407,[.140,.126,.200,.239],'15','20','Rectangles share height/width ratios: missing=T*35/14.'),
        (3023,[.623,.792,.679,.879],'1/3','tan(40*pi/180)^2','Right-triangle altitude: areaBDC/areaADC=BD/AD=tan(angleA)^2.'),
        (3005,[.301,.426,.357,.501],'2304','384+sqrt(117*27*13*77)','DiagonalYW=sqrt(32²+24²)=40. AreaYZ W384; triangleXYW sides96,104,40 then90,104,40, by Heron. CF semiperimeter117.'),
        (2525,[.363,.821,.457,.919],'38','42','Union of perpendicular rectangles: horizontal2*T +vertical3*8 -overlap2*3.'),
        (2986,[.507,.220,.543,.286],'3','5','Equal anglesA,B implyBC=AC: 2x+T=3x-1, sox=T+1.'),
        (784,[.561,.479,.620,.657],'46','50','Orthogonal staircase perimeter=2*(sum horizontal15+sum vertical2+T+2).'),
        (754,[.485,.811,.605,.948],'12.5',r(100*66/488),'Original block length12,depth6,height8: SA432. Cut width9,height3 reduces SA54. CF length14 gives SA488, cutwidth11, decrease66. Percent=100*decrease/originalSA.'),
        (2885,[.444,.323,.480,.381],'4/25','1/4','Similar triangles: area ratio=(small baseT/large base10)².'),
        (2950,[.737,.877,.771,.934],'8','10','D,E are midpoints, F is centroid. QuadrilateralDBEF occupies1/3 of triangleABC, whose area=6*T/2; requested area=T.'),
    ]


def authored_mathvista():
    return [
        (271,[.773,.502,.819,.600],'5','10','Equal tick-marked segments y=3y/5+T give y=5T/2.'),
        (678,[.222,.323,.349,.502],'58','61','Angle x=atan(opposite T/adjacent10); use nearest-degree precision corresponding to original numerical options.'),
        (583,[.647,.400,.754,.495],'5.8','6.5','Sine rule x=T*sin21°/sin97°, rounded to one decimal.'),
        (737,[.282,.789,.381,.952],'78','82','Parallelogram perimeter2*(baseT+side16).'),
        (822,[.512,.020,.617,.150],'44','48','Parallelogram perimeter2*(baseT+side10).'),
        (318,[.287,.056,.407,.212],'2256','2304','Right trapezoid area=(upperT+lower53)*height48/2.'),
        (242,[.319,.242,.362,.327],'135','144','Right trapezoid has anglesA=T*x andD=x; A+D180 gives A=180T/(T+1).'),
        (88,[.477,.448,.505,.512],'30','22.5','Square tangent atvertexP: x+90+T*x=180, sox=90/(T+1).'),
        (757,[.322,.330,.452,.489],'7.2','6.7','Two secants from common exterior point: x(x+T)=8(8+12); positive root, nearest tenth.'),
        (726,[.343,.059,.487,.218],'10','15','Exterior secant angle3x=((4x+T)-30)/2, hencex=(T-30)/2.'),
        (304,[.491,.165,.539,.260],'100','81','Straight angle x+y+T=180 andy=x²; positive x10 then9, y100 then81.'),
        (206,[.603,.816,.676,.899],'3','3.6','Dilation centerC: scale CQprime/CQ=T/5.'),
        (386,[.609,.399,.800,.533],'10*sqrt(3)','8*sqrt(6)','Right triangle missingleg=sqrt(hypotenuseT²-10²).'),
        (776,[.526,.453,.574,.561],'18.79','19.29','Incenter equal perpendicular distances: QP=QM=T. Right triangleJPQ has JP16.5, soJQ=sqrt(16.5²+T²), nearest hundredth.'),
        (897,[.781,.344,.838,.488],'40','46','AngleJ=asin(LK/JK)=asin(T/14), nearest degree.'),
        (684,[.802,.415,.888,.518],'55','56','Congruent chords give equal residual minor arcs: 2x-T=83, x=(83+T)/2.'),
        (819,[.287,.224,.347,.319],'7','8','Parallelogram diagonals bisect: halfW-to-center T equals2t-6.'),
        (716,[.197,.477,.287,.635],'16*sqrt(5)','sqrt(7857)/2','AltitudeT²=8*x, totalhypotenuse8+x; rightlegy²=x*(8+x). T16 then18.'),
        (665,[.873,.424,.931,.598],'8','10','Adjacent leg T and angle60 give hypotenuse T/cos60=2T.'),
        (160,[.391,.278,.507,.371],'12','4*sqrt(13)','Pythagoras x=sqrt(T²-9²), hypotenuse15 then17.'),
        (238,[.439,.384,.565,.496],'20/3','sqrt(451)/3','Parallel segments give PT=PR/3; PR=sqrt(T²-15²).'),
        (786,[.135,.685,.220,.769],'100','110','Isosceles trapezoid: upper angleK=180-lower angleM.'),
        (333,[.494,.322,.615,.493],'12/5','2*sqrt(2)','AngleX is upper-left, adjacent leg5: tanX=sqrt(T²-25)/5. Dataset5/12 uses the opposite acute angle and is incorrect for the visible X.'),
        (310,[.156,.515,.198,.628],'40/3','sqrt(1053)/2','Altitude T and near projection6 give far projectionT²/6; z²=(T²/6)*(6+T²/6).'),
        (951,[.594,.732,.680,.820],'12.75','13.75','CE is diameter, so angleD90; 3x+5x-T=90.'),
        (283,[.820,.505,.915,.601],'5','6','Congruent chords WT,WY imply4x=2x+T.'),
        (866,[.673,.570,.748,.672],'135','125','Parallel bases imply adjacent anglesS+R180; midpoint information is irrelevant.'),
        (781,[.180,.595,.235,.672],'18','22','Centroid median throughG impliesG midpointCD, soCD=2DG.'),
        (236,[.758,.445,.801,.535],'12','13','Equal anglesS,T implyRT=RS, so2z-15=T.'),
        (804,[.530,.293,.577,.380],'4.29','5.95','Perpendicular radius bisects chordCE13.5; BD=sqrt(T²-6.75²), nearest hundredth.'),
        (114,[.728,.410,.806,.502],'9.45','13.05','Tangent KL=T, ML=x+10: (x+10)²=x²+T², x=(T²-100)/20.'),
        (408,[.516,.417,.605,.531],'6*sqrt(5)','3*sqrt(30)','Right-triangle leg z²=T*(T+3), by altitude projection theorem.'),
        (925,[.765,.056,.802,.191],'19.5','23.4','Visible pumpernickel unit priceT times requested3.9lb.'),
        (568,[.588,.526,.622,.616],'2','4','Requested car-fare difference: Mukilteu-Clinton T minus Southport5.'),
        (718,[.497,.735,.545,.899],'3/14','4/15','Velvet swirl countT, other counts5+1+5=11. ProbabilityT/(T+11). Preserve exact fraction; source0.21 is rounded.'),
        (359,[.688,.748,.734,.825],'-7','-9','Friday0 minus ThursdayT over one day.'),
        (651,[.808,.842,.854,.938],'7','9','Canada 1990s T minus Italy1.'),
        (831,[.638,.846,.760,.948],'679','699','Thursday374 plus FridayT.'),
        (205,[.722,.657,.789,.736],'24','26','Frequency for more than2runs = three-runT plus four-run10.'),
        (746,[.585,.890,.679,.962],'7','9','2014 entriesT minus2013 entries39, over one year.'),
        (144,[.666,.445,.720,.551],'13.8','18.4','Turmeric priceT per kg times requested4.6kg.'),
        (45,[.635,.445,.720,.523],'-3','-5','SeptemberT minus August17, over one month.'),
        (929,[.865,.881,.962,.963],'85','90','Mystery-game priceT plus toy rocket65.'),
        (332,[.624,.861,.951,.963],'7873','7973','January5936 plus AprilT. Printed comma is a thousands separator.'),
    ]


def main():
    records = {}
    for dataset, definitions in [('mathverse', authored()), ('mathvision', authored_mathvision()), ('mathvista', authored_mathvista())]:
        for idx, box, answer, cf_answer, derivation in definitions:
            base_id = f'{dataset}_{idx}'
            if base_id in records:
                raise ValueError(base_id)
            records[base_id] = dict(normalized_roi=box, answer=answer,
                counterfactual_answer=cf_answer, answer_audit=derivation,
                semantic_review='full-resolution source image and full question reviewed before primary generation',
                crop_review='pending')
    p = OUT / 'config/primary_c1_authored_semantics.json'
    if p.exists():
        existing = json.loads(p.read_text())
        # Preserve manual ROI refinements made after the initial draft.
        for key, value in records.items():
            existing.setdefault(key, value)
        records = existing
    p.write_text(json.dumps(records, indent=2)+'\n')
    print('authored', len(records))


if __name__ == '__main__':
    main()
