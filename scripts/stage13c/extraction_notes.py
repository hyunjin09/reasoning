"""Source-grounded draft annotations; sealed only after itemwise leakage review."""
NOTES={
'3022':[
('Writing β=angleABC and γ=angleACB, β+γ=110°.','β + γ = 110°.','Triangle angle sum.'),
('The corrected ABC-to-PAQ correspondence maps A to P, giving angleAPQ=70°.','∠APQ = 70° (from ABC ~ PAQ, since A corresponds to P)','Retain explicitly corrected source correspondence, not initial mistaken mapping.'),
('Since Q and P lie on BC and AC, angleQCP=angleACB; the second similarity also gives angleQCP=angleABQ, so β=γ=55°.','Hence, β = γ = 55°','Equal base angles; exclude BAQ15/PQC15 and all equivalents of asked angle.')],
'1082':[
('The source assigns a maximum of two cut pieces to O, three to F and three to H.','H: three pieces.','MIXED_OR_UNCLEAR: O through its hole yields2; exact F/H maxima depend on the pictured font geometry. The supplied description alone does not certify all these maxima. No M count or winning glyph is supplied.')],
'460':[
('Connecting ten paver centers gives nine segments.','the black line is a path with 9 segments','Open path edge count.'),
('The segment sequence contains five long-direction and four short-direction segments.','5 Ls and 4 Ss','Count the frozen sequence without summing weighted length.'),
('A long-direction center separation is6dm and a short-direction separation is4dm.','if the segment is L (parallel to long edge), length 6 dm; S (parallel to short edge), length 4 dm.','Center distance across full aligned pavers; exclude total46.')],
'2742':[
('There are four possible first-step M cells adjacent to the center.','So four possible M positions.','Adjacency count; source corrected omitted bottomM.'),
('Each reachable M has three adjacent C cells.','for each M, we have three possible Cs.','Grid neighbor enumeration.'),
('Each reachable C has two adjacent8cells.','All have two. So no issues.','Grid neighbor enumeration; exclude product24 and final path count.')],
'2587':[
('Square perpendicularity with P=(p,0) gives p(2-p)=0; the nondegenerate root gives P=(2,0).','OP • PQ = 0 => p(2 - p) + 0*2 = 0 => p = 0 or 2. p=0 invalid, so p=2.','Coordinate binding beyond axis fact; askedpoint isT.'),
('The remaining square vertex is R=(0,2), and the square area is4.','R = Q + QR vector = (2,2) + (-2, 0) = (0, 2).','Square geometry; exclude Tcoordinate, PT4 or equation directly fixingT.')],
'2890':[
('The crease is the perpendicular bisector of AC.','the fold line l is the perpendicular bisector of segment AC','Reflection geometry beyond supplied endpoints.'),
('With A=(8,h), B=(b,h), C=(0,c), the bottom-right corner D=(8,0), reflection gives BA=BC=5 and b=3.','b = w - 5.','Use width8; B lies on crease and is equidistantA,C.'),
('Writing d=h-c, BC²=b²+d² yields d=4; perpendicular slopes give hd=40 and h=10.','d = 4 = 40/h ⇒ h = 10','Pythagoras and crease orthogonality; exclude lengthBD sqrt125/5sqrt5.')],
'392':[
('The five integer roots sum to11 and have product7.','r1 * r2 * r3 * r4 * r5 = 7.','Vieta signs for monic degree5.'),
('Every integer root is among ±1 and ±7.','the possible integer roots are ±1, ±7.','Integer-root divisibility.'),
('The positive product forces an even number of negative roots.','the number of negative roots must be even (0, 2, 4).','Sign constraint; exclude complete root multiset and multiplicity of1.')],
'1876':[
('Two distinct straight streets cannot intersect twice.','straight lines can intersect at most once','Geometric constraint applied to this street system; no house named as answer.'),
('Three straight streets can produce at most three pairwise intersections.','three straight lines can intersect at up to three points','Choose3pairs.'),
('Four straight streets could produce at most six pairwise intersections.','four straight lines can intersect up to 6 times','Choose6pairs; compare original seven crossings without identifying resident.')],
'1841':[
('S must be supplied by box1, since no other box contains S.','Box1 must be S (since we need S in the letters).','Unique-symbol binding, not targetbox2.'),
('Once box4 supplies M, boxes1,2,3,5 must supply S,I,O,N without repetition.','the letters to be selected from Boxes 1,2,3,5 must be S, I, O, N.','Residual constraint beyond the supplied sets; no answer binding.')],
'2213':[
('The arrangement has dihedral symmetry D3, with three rotations and three reflections, order6.','the dihedral group D3, which has 6 elements','Equilateral triangular arrangement.'),
('The identity fixes60 colorings.','Identity: 60 fixed colorings','6!/(3!2!1!)=60.'),
('A nonidentity120-degree rotation has two3-cycles, so none of these colorings is fixed.','no fixed colorings for rotations','Red count2 and green1 incompatible with3-cycles.'),
('Each reflection fixes4 colorings.','4 fixed colorings per reflection','Two singletons must carry green and blue in2orders; two pairs red and blue in2orders.')],
'1124':[
('Use lower squares [0,1]×[0,1] and [1,2]×[0,1], with upper square [0.5,1.5]×[1,2].','C spans (0.5, 1)-(1.5, 2).','Coordinate representation.'),
('The diagonal joins (0.5,2) to (2,0), with slope-4/3.','The slope would be (0 - 2)/(2 - 0.5) = (-2)/1.5 = -4/3.','Derived slope; numeric1 only incidental coordinate.'),
('It intersects the common horizontal boundary at (1.25,1).','The line enters Square C at (0.5, 2) [top-left corner] and exits Square C at (1.25, 1)','Substitute y=1 in line; not total shaded area.')],
'3019':[
('Triangle ADC has equal base angles DAC=ACD=40°.','angle ACD = angle DAC. Since angle ACD is 40°, then angle DAC is 40°.','EqualAD,CD and DbetweenB,C.'),
('Angle ADC is100°, so its supplement ADB is80°.','angle ADC = 100°, so angle ADB = 80°.','Triangle sum and straightBC.'),
('Triangle ADB therefore has BAD=ABD=50°.','angle BAD = 50°, which is angle ABD = 50°.','EqualAD,BD; do not sum into askedBAC.')],
'825':[
('At top-left grid alignment, the A mask overlaps dots at (1,1),(1,3),(2,2),(2,4), four positions.','(1,1), (1,3), (2,2), (2,4) → 4 dots.','Correct overlap computation for this explicit alignment; no optimality or final option.'),
('At that alignment, D overlaps dots at (1,1),(1,3),(2,2),(3,1), also four positions.','(1,1), (1,3), (2,2), (3,1) → 4 dots.','Correct local binary overlap count; does not answer maximum over placements.')],
'1318':[
('The octahedron has12edges, since8triangular faces contribute24edge incidences and each edge belongs to2faces.','total edges = (8*3)/2 = 12','Euler/edge incidence count.'),
('Every face contributes to3vertex sums, and there are6vertices; if the common vertex sum is S, 6S=3times the sum of all face labels.','6S = 3*(sum of all faces)','Incidence count independent of ambiguous net folding.'),
('All face labels sum to44, making the common vertex sum22.','total sum = 27+17=44. Therefore, 2S=44 => S=22.','Verify 2+4+6+7+8+9+3+5=44. Neither askedB+D nor its value.')],
'603':[
('Closing the cover matches its column indices directly to the other half.','But from the grid, with the columns matching.','VERIFIED_ERROR: actual vertical hinge reflects c to13-c. Preserve source mapping error; no vehicle named.')],
'1877':[
('There are6face-center stickers and12edge stickers,18stickers in total.','6 face stickers (centers). Total stickers: 18.','Count cube faces and edges.'),
('The sticker diagonal equals the whole10cm cube edge, so its side is5√2cm and its area50cm².','The length of the cube edge is 10 cm, which is the diagonal of the sticker. So the sticker\'s diagonal is 10 cm, so side length 5√2 cm, area 50 cm².','VERIFIED_ERROR: lying along an edge does not span its full length; corner contacts require diagonal5. Retain original incorrect intermediate, exclude total900.')],
'936':[
('The proposed horizontal folding sequence is row1overrow2, then row2overrow3, producing stack row1,row2,row3.','- First fold: row 1 over row 2.','VERIFIED_ERROR: those sequential over-folds invert the first stack rather than preserve row1 on top; source claim retained. Exclude final row-major mapping and a,b,c values.')],
'353':[
('The northwest observer is treated as facing northwest, with right directed east.','From northwest: observer facing northwest. Right direction is east','VERIFIED_ERROR: northwest observer faces southeast toward the base; right is southwest, not east.'),
('The east observer is treated as facing east, with right directed south.','From east: observer facing east. Right direction is south.','VERIFIED_ERROR: observer faces west and right is north; preserve perspective-binding error, exclude lean-direction conclusion.')],
'2963':[
('The square area is 36 square units.','So area of square is 36 square units.','6 squared is36; this is not the requested coefficient sum.'),
('Place the square vertices at (0,0), (6,0), (6,6), (0,6).','the square has vertices at (0,0), (6,0), (6,6), (0,6).','Valid rigid-coordinate representation.'),
('Adjacent corner quarter-disks have no interior overlap; their common point is the intervening side midpoint.','the only intersection point between bottom-left and bottom-right quarter-circles inside the square is at (3,0)','Center distance6 equals radius sum6; external tangency.'),
('Opposite corner centers are 6√2 apart, exceeding the radius sum 6, so those quarter-disks do not overlap.','6√2 ≈ 8.485 > 6','Distance check.'),
('Each quarter-circle area is 9π/4.','each quarter-circle area is (1/4)π(3)² = (1/4)(9π)','Quarter disk formula; no coefficient identification or sum.')],
'2829':[
('A side-n hexagon has 6n lattice vertices on its perimeter.','6(n + 1) - 6 = 6n vertices on the perimeter','Count side vertices once at shared corners.'),
('The triangular-lattice hexagon of radius r has 2r+1 horizontal rows.','the number of rows (heights) is 2r + 1','Rows at integer heights-r throughr.'),
('For a hexagon of side n, the number of horizontal edges is 3n(n+1)/2.','the number of horizontal edges is 3n(n + 1)/2','VERIFIED_ERROR: n=1 has4 horizontal edges, not3. Source intermediate formula is retained without correction.')],
'3030':[
('Writing s for the square side, s=6√2.','s = 12/√2 = 6√2','Diagonal relation.'),
('Use W=(0,0), X=(s,0), Y=(s,s), Z=(0,s), A=(s/2,0).','Point A is the midpoint of WX, so A = (s/2, 0)','Coordinate representation combining square and midpoint.'),
('For B=(b,0) with b>s, perpendicularity makes C=(s/2,k), and equal legs imply k=b-s/2.','So k = b - s/2.','C is above base because Y lies insideBC.'),
('Collinearity gives (2b-s)(b-2s)=0; b>s selects b=2s.','(2b - s)(b - 2s) = 0','Quadratic eliminates nonadmissible root.'),
('Consequently AB=AC=3s/2 and C=(s/2,3s/2).','C: (s/2, c), and c = AB = 2s - s/2 = 3s/2','Retain corrected symbolicC, exclude earlier numericC typo and askedBC conclusion.')],
'2077':[
('The center has degree5, even inner-ring vertices degree4, odd inner-ring vertices degree3, and outer vertices degree4.','- Type A (0,2,4,6,8): d=4, 5 nodes','Count original adjacency; source corrected outer degree3 slip.'),
('With x_i coins and degree d_i, stationarity requires x_j = sum over neighbors i of x_i/d_i.','x_j = sum_{i ~ j} (x_i / d_i)','Conservation at each vertex; no target value.'),
('The center equation is x_C=(x_1+x_3+x_5+x_7+x_9)/3.','(x_1 + x_3 + x_5 + x_7 + x_9) / 3','Each odd-ring neighbor degree3.'),
('For inner node1, x_1=x_C/5+x_0/4+x_2/4.','x_1 = (x_C / d_C) + (x_0 / d_A) + (x_2 / d_A)','Its three neighbors have degrees5,4,4.')],
'2456':[
('If c is the x-intercept, m=-b/c.','m = -b / c','Intercept equation; c is not the requested product.'),
('The product can be rewritten as mb=-b²/c.','mb = -b² / c','Transformed expression without final range or option.')],
'2997':[
('The white triangle height h satisfies 6²+h²=10², hence h=8 cm.','6² + h² = 10² => 36 + h² = 100 => h² = 64 => h = 8 cm.','Pythagorean theorem; asked quantity is shaded area.')],
'2472':[
('The L can be represented by a 5-by-8 bounding rectangle with its upper-right corner removed.','imagine a 5x8 rectangle','Coordinate decomposition, supported by later explicit intervals.'),
('Its left rectangular part has area2×8=16; the right bottom extension has width3 and area3×2=6.','- Right part (x=2-5): height 2, width 3, so area = 3*2 = 6.','Two intermediate component areas; exclude their summed asked area22.')],
'2360':[
('With table height T, long block side L and short side W, the two top-surface heights in Figure1 are T+L and W.','Height of top of table block: T + L','Derived height representation, no target table height.'),
('The Figure1 height difference gives T+L-W=32.','Difference: (T + L) - W = 32.','Algebraic relation beyond original placement facts.'),
('In Figure2 the height difference gives T+W-L=28.','Difference: (T + W) - L = 28.','Keep both source equations, exclude2T=60,T=30 and optionC.')],
'2640':[
('The original triangle area W is (1/2)×3×4=6.','W =','Must match source area calculation in final audit.'),
('For an attached right-isosceles triangle with supporting side s as a leg, area is s²/2; if it is the hypotenuse, area is s²/4.','X = 9/4, Y=16/4, Z=25/4','Similar right-isosceles formula. Do not supply the selected relation X+Y=Z.')],
'1269':[
('Use A=(0,0), B=(l,0), C=(l,w), D=(0,w); triangle ABD has hypotenuse sqrt(l²+w²).','BD: distance from B to D: sqrt(l² + w²)','Coordinate representation and Pythagoras.'),
('Its inradius is r=lw/(l+w+sqrt(l²+w²))=(l+w-sqrt(l²+w²))/2.','r = (l + w - sqrt(l² + w²))/2.','Area/semiperimeter identity.'),
('The incenter O has coordinates (r,r).','the incenter O has coordinates (r, r).','Equal distance from the two perpendicular axes; exclude OPCR area.')],
}
