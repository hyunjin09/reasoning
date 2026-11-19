# Family 2908: frozen source blocks

A belt is drawn tightly around three circles of radius $10$ cm each, as shown. The length of the belt, in cm, can be written in the form $a + b\pi$ for rational numbers $a$ and $b$. What is the value of $a + b$?

## B1 · steps 1–17 · RAW_EVIDENCE_AND_BINDING · 542 tokens

This is a complex or challenging question, and it is difficult to provide a direct and correct answer. I need to think about it.
Well, so we have three circles, each with radius 10 cm, and a belt going around them tightly. We need to find the total length of the belt, which should be a combination of straight segments and curved parts, right? Let me visualize this first. The problem says "as shown," but since I can't see the picture, but the description is three circles of radius 10, tight belt around them. Wait, actually, in the standard problem with three equal circles, the belt around them usually makes a sort of triangular shape with the three circles tangent to each other and the belt, so the belt goes along the outside of all three circles, touching each one at two points, maybe? Wait, no, for three circles each tangent to the other two, the belt should wrap around each circle, but the straight parts are between the points where the belt changes direction, which should be at the points of tangency between the belt and the circles. Wait, maybe I should sketch this mentally: three circles, each radius r = 10, centers forming an equilateral triangle because each pair is tangent (distance between centers is 2r = 20). Then the belt is a closed loop around all three circles, so it's like a "triangle" made up of straight segments and arcs.

Let me recall: when you have a tangent line to a circle, the length of the tangent segment between two tangent points (for two circles) is equal to the distance between the centers times the sine of half the angle between the radii? Wait, no, maybe better to think about the angle each straight segment makes. Let's denote the centers of the three circles as A, B, C, forming an equilateral triangle with side length 2r = 20 cm (since each pair of circles is tangent, distance between centers is sum of radii, which is 10 + 10 = 20). Now, the belt is tangent to each circle, so for each circle, the belt touches it at one point, and between two adjacent circles, the belt is a straight line segment tangent to both. Wait, yes! Between two circles, say center A and center B, the belt has a straight segment that's tangent to both circle A and circle B, and this segment should be external tangent, not crossing between them (since it's a belt going around the outside). For two circles of equal radius, the external tangent lines have some properties.

Let me formalize this. 

## B2 · steps 18–72 · DERIVED_RELATIONS · 2278 tokens

Take two circles, centers separated by distance d = 20 cm, radius r = 10 each. The external tangent segment between them: if we draw the radii to the tangent points, those radii are both perpendicular to the tangent line, so they are parallel to each other (both perpendicular to the same line, so parallel). Therefore, the quadrilateral formed by the two centers and the two tangent points has two right angles at the tangent points, and two parallel sides (the radii), so it's a trapezoid, specifically a right trapezoid with two right angles at the tangent points. If we connect the centers A and B, length AB = 20, and if we draw the radii to the tangent points, say A to P (on circle A) and B to Q (on circle B), then AP and BQ are both radius r = 10, perpendicular to PQ (the tangent segment). So if we translate vector AP to start at B, we get a vector of length r, so the segment PQ should be equal in length to the segment between the feet of the perpendiculars from A and B to the line PQ? Wait, maybe better to use the right triangle formed by moving from A to B, then to the point where the perpendicular from B meets the line AP (since AP is perpendicular to PQ, and BQ is perpendicular to PQ, so AP and BQ are both perpendicular to PQ, so quadrilateral APQB has two right angles, so AB is the hypotenuse of a right triangle with legs equal to PQ and the difference in radii? Wait, no, external tangent: for equal radii, the difference in radii is zero, so actually, the line connecting the centers and the tangent segment form a rectangle? Wait, yes! If the radii to the external tangent points are both perpendicular to the tangent line, then they are parallel, and since the radii are equal, the segment between the centers and the segment between the tangent points should form a rectangle. Wait, let's see: centers A and B, tangent points P on A, Q on B, AP ⊥ PQ, BQ ⊥ PQ, so AP || BQ, and AP = BQ = 10. Therefore, if we draw a line from A parallel to PQ, meeting BQ at some point R, then APRQ is a rectangle, so PR = AQ? Wait, maybe better: the distance between A and B is 20, the vertical distance (if we set coordinates) between the two centers along the direction perpendicular to the tangent line. Wait, let's assign coordinates to make this concrete.

Let’s place center A at (0, 0), center B at (20, 0). Since the circles have equal radius 10, the external tangent lines above the x-axis: the tangent points should be at the same height above the x-axis? Wait, for external tangent, the tangent line doesn't cross the line segment AB, so for two circles of equal radius, the external tangent lines are symmetric with respect to the line AB. Let's find the equation of the external tangent above the x-axis. The tangent line must be at distance r from each center. The equation of a line tangent to circle centered at (0,0) with radius 10 is y = mx + c, distance from (0,0) to line is |c| / sqrt(m² + 1) = 10, so c² = 100(m² + 1). Similarly, distance from (20,0) to line is |20m + c| / sqrt(m² + 1) = 10, so (20m + c)² = 100(m² + 1). Now, let's subtract the first equation from the second: (20m + c)² - c² = 0 ⇒ 400m² + 40mc = 0 ⇒ 40m(10m + c) = 0 ⇒ m = 0 or c = -10m. m = 0 would be the x-axis, which is a common tangent (the line y=0 is the x-axis, but the circles are on the x-axis, radius 10, so each circle touches the x-axis at (±10, 0), so y=0 is a tangent line for both circles? Wait, circle A: (x-0)² + y² = 10², so y=0 is tangent at (0,0)? Wait, no! Wait, center at (0,0), radius 10, so the circle goes from y=-10 to y=10, so y=0 is a secant line, not tangent. Wait, I messed up: distance from center to line must be equal to radius for tangency. So for line y = mx + c, distance to (0,0) is |c| / sqrt(m² + 1) = 10, so |c| = 10 sqrt(m² + 1). Distance to (20,0) is |20m + c| / sqrt(m² + 1) = 10, so |20m + c| = 10 sqrt(m² + 1). Therefore, either |c| = |20m + c|, which implies 20m = 0 ⇒ m = 0, or |c| = -|20m + c|, but absolute values can't be negative, so that would imply 20m + c = -c ⇒ 20m = -2c ⇒ c = -10m. Okay, so m = 0 is the x-axis, but let's check m=0: line y = c, distance from (0,0) is |c| = 10 ⇒ c=10 or c=-10. c=10: y=10, distance from (0,0) is 10, good; distance from (20,0) is 10, good, so y=10 is an external tangent above the x-axis, touching circle A at (0,10) and circle B at (20,10). Similarly, y=-10 is the lower external tangent. Wait, but m=0 is horizontal tangent, which are the top and bottom tangents between the two circles. But what about the other external tangents? Wait, no, for two circles, there are four external tangents? Wait, no: two circles, two external tangents (that don't cross between them) and two internal tangents (that cross between them). For equal radii, the external tangents are parallel, and the internal tangents intersect at the midpoint of the line segment connecting centers? Wait, in our case, for two circles of equal radius, the external tangents should be parallel, right? Because the radii to the tangent points are both perpendicular to the tangent line, so if the circles have equal radius, the direction of the radii is the same, so the tangent lines must be parallel. Yes, that makes sense. So the two external tangent lines (above and below the line connecting centers) are parallel, and the two internal tangents intersect at the midpoint between the centers.

But in our problem, the belt is going around all three circles, so it's a closed loop, so for the three circles, the belt should consist of three straight segments, each between two adjacent circles (connecting the two circles that are not the one we're looking at? Wait, no, for three circles, each pair is adjacent, so between each pair of circles, there's a straight segment of the belt that's tangent to both circles, and then between each circle, the belt also wraps around a part of the circle. Wait, yes, that's the key: for each circle, the belt is tangent to it, but since there are three circles, the belt will have three straight segments (each outside a pair of circles) and three curved segments (each on the outside of a circle, between the two straight segments). Wait, let's confirm with the three circles: centers form an equilateral triangle, side length 20. The belt is a closed loop around all three circles, so if you imagine walking along the belt, you go straight from one tangent point on circle A to a tangent point on circle B, then straight from circle B to circle C, then straight from circle C back to circle A. But at each circle, instead of going straight, the belt curves around the circle? Wait, no, actually, for each circle, the portion of the belt that is tangent to the circle must be an arc, and the two straight segments meet the circle at tangent points, so the angle of the arc is equal to 360 degrees minus the angle between the two tangent segments at the point of tangency? Wait, maybe better to think about the angles at each circle.

Wait, let's take one circle, say the top one, center A. The belt is tangent to circle A at two points: one point where the belt comes from the left circle (circle B) and one point where it goes to the right circle (circle C). So at circle A, the two tangent lines to the belt (from the adjacent circles) form an angle, and the arc of the belt that is on the outside of circle A is the part of the circle that's not between those two tangent lines. Wait, yes! For a circle, if you have two tangent lines to the circle, the region between the two tangent lines and the circle is a sort of "wedge" of the circle, and the arc length corresponding to that wedge is the angle of the wedge times radius. But for the belt, which is going around the outside, the arc on circle A should be the part of the circle that's not covered by the two tangent segments? Wait, no, actually, when the belt is tight around three circles, for each circle, the belt is externally tangent to the circle, so the angle that the belt "turns" around the circle should be the angle between the two tangent segments at the circle's center.

Let me recall a general formula for the length of a belt around n circles: for two circles, it's 2r(π/2 + something?) Wait, no, for two circles, the length of the belt (if it's going around both externally) is equal to the sum of the lengths of the external tangent segments plus the arcs. Wait, for two circles, the belt would be two straight segments (wait, no, two circles, a belt around both: actually, the belt would have two straight segments connecting the two circles, and two arcs? Wait, maybe I need to stick to three circles because the problem says three circles.



## B3 · steps 73–150 · REPRESENTATION_SETUP · 3427 tokens

Wait, let's use the coordinate system for the three centers to make this precise. Let's place the three centers at the vertices of an equilateral triangle with side length 2r = 20 cm. Let's set center A at (0, 10√3), center B at (-10, 0), center C at (10, 0). Wait, why? Because in an equilateral triangle with side length s, the height is (s√3)/2, so for s=20, height is 10√3. So center A at top, centers B and C at the base, each 10 cm from the center of the base (since base length is 20, so half is 10), so coordinates: A(0, 10√3), B(-10, 0), C(10, 0). Let's verify distance AB: sqrt[(0 - (-10))² + (10√3 - 0)²] = sqrt[100 + 300] = sqrt[400] = 20, good. AC same, BC is 20, perfect.

Now, let's find the points of tangency for the belt. The belt is the outer tangent belt, so for each circle, the belt is tangent to it, and between each pair of adjacent circles, the belt has a straight tangent segment. Let's find the equation of the straight tangent segment between circle A and circle B first. Circle A: center (0, 10√3), radius 10; circle B: center (-10, 0), radius 10. We need the external tangent (not the one crossing between them, which would be internal tangent) that's part of the belt around all three circles.

First, recall that for two circles, the external tangent lines can be found by noting that the tangent points have radii perpendicular to the tangent line, so the radii to the tangent points are parallel. So let's denote a tangent point on circle A as P, on circle B as Q, so AP is perpendicular to PQ, BQ is perpendicular to PQ, so AP || BQ. Since both are radius 10, vectors AP and BQ are equal in length and direction (for external tangent, same direction; for internal tangent, opposite direction). So vector AP = vector BQ, so if we draw vector from A to P and from B to Q, they are the same, so the segment PQ should be equal to the segment connecting the centers in the direction parallel to PQ? Wait, maybe better to use the fact that the tangent segments between two circles have length equal to sqrt[(distance between centers)² - (r1 - r2)²] for external tangent, and sqrt[(distance between centers)² - (r1 + r2)²] for internal tangent. Wait, yes! That's a key formula I might have forgotten earlier.

For two circles, centers separated by d, radii r and R:

- Length of external tangent segment (not crossing the line segment joining centers) is sqrt[d² - (r - R)²]

- Length of internal tangent segment (crossing the line segment) is sqrt[d² - (r + R)²]

But in our case, all radii are equal, r = R = 10, so for external tangent (which is what we want for the belt around the outside, because internal tangent would cross between the circles, which isn't part of the outer belt), the length of the external tangent segment between two circles is sqrt[d² - 0] = d. Wait, hold on! If r = R, then (r - R) = 0, so external tangent length is d. But wait, let's check with our coordinate system. Circle A at (0, 10√3), radius 10; circle B at (-10, 0), radius 10. Let's compute the distance between centers: 20, as we had. Now, the external tangent above the line AB? Wait, in our coordinate system, the line AB goes from (-10,0) to (0,10√3), which is a diagonal, but maybe better to find the tangent segment that's part of the outer belt. Wait, actually, maybe the three straight segments of the belt are each equal in length, and we need to find that length. Wait, but if for two equal circles, external tangent length is d, then d = 20, so each straight segment is 20? But wait, let's test with the horizontal tangent above the base circles. Circle B at (-10,0), radius 10, so topmost point is (-10,10); circle C at (10,0), topmost point is (10,10). So the line y=10 is tangent to both circle B and circle C at (-10,10) and (10,10), right? Distance from center B (-10,0) to y=10 is 10, which equals radius, so yes, tangent; same for C. So the segment between (-10,10) and (10,10) is a straight segment of length 20, which is the distance between the centers (since centers are 20 apart horizontally, and the tangent points are 10 above each center, so the segment is horizontal, length 20). Wait, that's the lower external tangent? Wait, no, y=10 is above the x-axis, centers at y=0, so yes, that's the top tangent between the two lower circles? Wait, centers B and C are at (±10,0), so bottom is at y=-10, top at y=10 for each circle. So the line y=10 is tangent to both B and C at their top points, so that's a horizontal tangent segment of length 20 between them.

Now, what about the tangent segment between circle A and circle B? Circle A is at (0, 10√3) ≈ (0, 17.32), radius 10, so it goes from y ≈ 17.32 - 10 = 7.32 to y ≈ 17.32 + 10 = 27.32. Circle B is at (-10,0), radius 10, so from y=-10 to 10. The tangent segment between A and B that's part of the outer belt should be above the line AB, maybe? Wait, let's find the tangent point on A and B. Let's take the external tangent that doesn't go through the interior of the triangle ABC. So for centers A(0, h), B(-d, 0), C(d, 0), h = 10√3, d = 10, as before.

Vector from center B to center A is (10, h) = (10, 10√3). If we want the external tangent, the direction of the tangent segment should be such that the radii to the tangent points are parallel, as we said. So let's assume the tangent segment is above the line AB, so the radii from centers to tangent points are both pointing in the same direction (say, outward from the triangle ABC), so the vector from A to tangent point P is equal to the vector from B to tangent point Q, let's call this vector v. Then since P is on circle A: A + v = P, and |v| = 10, so v is a vector of length 10. Similarly, Q = B + v, and |Q - B| = |v| = 10, which checks out. Now, the vector PQ = Q - P = (B + v) - (A + v) = B - A, so PQ is equal to B - A, which has length |B - A| = 20. Wait, that's the same as the distance between centers! So does that mean that for two equal circles, the external tangent segment is equal to the distance between centers?

Wait, but in the horizontal case, circle B(-10,0), circle C(10,0), centers distance 20 apart, tangent segment y=10 from (-10,10) to (10,10), length 20, which matches. For circle A(0,10√3) and circle B(-10,0), let's compute the vector AB = B - A = (-10, -10√3), so length 20. If we take vector v = (a, b), |v| = 10, then P = A + v = (a, 10√3 + b), Q = B + v = (-10 + a, 0 + b). Now, the line PQ should be tangent to both circles, but wait, actually, since we constructed it so that AP and BQ are both equal to v and perpendicular to PQ (because if AP is perpendicular to PQ, then vector AP • vector PQ = 0). Wait, let's compute vector PQ = Q - P = (-10 + a - a, 0 + b - (10√3 + b)) = (-10, -10√3). Vector AP = P - A = (a, b), so dot product AP • PQ = (a)(-10) + (b)(-10√3) = -10(a + b√3). For AP to be perpendicular to PQ, this dot product must be zero, so a + b√3 = 0 ⇒ a = -b√3. But |v| = |AP| = sqrt(a² + b²) = 10, so substitute a = -b√3: sqrt(3b² + b²) = sqrt(4b²) = 2|b| = 10 ⇒ |b| = 5 ⇒ b = 5 or -5. Now, which one is external tangent? Let's take b = 5, then a = -5√3, so vector v = (-5√3, 5). Then point P = A + v = (0 - 5√3, 10√3 + 5), point Q = B + v = (-10 - 5√3, 0 + 5). Now, let's check if PQ is tangent to both circles, but maybe easier to check if the tangent point on circle A is P: the radius AP has length |v| = 10, correct, and direction is v, so the tangent line at P is perpendicular to v, so slope of AP is (5 - 10√3)/(-5√3) wait, no, slope of AP is (b)/(a) = 5/(-5√3) = -1/√3, so slope of tangent line at P is negative reciprocal, √3. Let's compute slope of PQ: Q - P = (-10, -10√3), so slope is (-10√3)/(-10) = √3, which matches, so yes, tangent line at P is perpendicular to AP, good. Similarly for Q.

Now, is this the external tangent? Let's see the position: circle A is at (0, ~17.32), tangent point P is at (-8.66, ~10 + 5) = (-8.66, 15), which is to the left and slightly down from A, and tangent point Q is at (-10 -8.66, 5) = (-18.66, 5), which is left and down from B. Wait, but the belt is supposed to go around all three circles, so the upper part of the belt should be above the top circle? Wait, no, the top circle is center A, so the belt around it should go above and below? Wait, maybe I need to think about the entire belt.

Wait, actually, for three circles, the belt that goes around all of them tightly (i.e., enclosing the triangle formed by the centers without crossing through the circles) will have, for each pair of adjacent circles, a straight segment that is the external tangent segment between them, and for each circle, an arc segment that is part of the belt wrapping around the circle. Now, here's the key: when the belt is tight around the three circles, the straight segments will be tangent to the circles, and the angle between the two tangent segments at each circle's center will determine how much arc length is on the circle.

Let's consider one circle, say the top one (center A). The belt touches circle A at two points: one point where the belt comes from the left circle (circle B), and one point where it goes to the right circle (circle C). Let's find the angle between the two radii to these tangent points. Since the two tangent segments (from B to A to C) are both tangent to circle A, the angle between the two tangent lines from a point to a circle is related to the angle subtended by the chord connecting the points of tangency.

Wait, in general, for a point outside a circle, the two tangent segments to the circle are equal in length, and the lines from the point to the center bisect the angle between the tangent segments. But in our case, the two tangent lines are the straight segments of the belt meeting at circle A's center? No, wait, the straight segments of the belt are tangent to the circles, so the straight segment from circle B to circle C is tangent to circle A? No, the straight segment between circle B and circle C is tangent to circle B and circle C, but does it also touch circle A? No, the belt is only tangent to each circle once (except maybe at the vertices, but for three circles, each circle is tangent to two adjacent circles, so the belt should be tangent to each circle at one point between the two straight segments? Wait, no, each circle is tangent to the belt at two points: one where the belt comes from the previous circle, and one where it goes to the next circle. Wait, let's take the base circles, centers B(-10,0) and C(10,0), radius 10. The belt around the bottom should have two straight segments: one between the left bottom circle (B) and the top circle (A), and one between the right bottom circle (C) and the top circle (A), and one between B and C. Wait, yes! That's the standard arrangement: three circles, one on top, two on the bottom, each touching the other two, and the belt goes around the outside, so it has three straight segments: one from the leftmost tangent point on the left bottom circle to the left tangent point on the top circle, then a straight segment from left tangent point on top circle to right tangent point on top circle? No, wait, no—three straight segments, each between two adjacent circles, and three arc segments, each on one circle, between the two tangent points.

Let's count the tangent points: for the belt to be a closed loop, it must have a number of tangent points equal to the number of circles, but for each circle, the belt is tangent to it at two points (one at the start of the belt segment for that circle, one at the end), so three circles would have six tangent points, but the straight segments connect tangent points between circles, so between circle 1 and circle 2: one straight segment, so two tangent points (one on each circle), between circle 2 and 3: two tangent points, between circle 3 and 1: two tangent points, so total six tangent points, which matches three circles each with two tangent points (two per circle, so six total, closed loop). Therefore, for each circle, the belt is tangent at two points, and the portion of the belt on that circle is the arc between those two points.



## B4 · steps 151–403 · REINTERPRETATION_OR_CHECKING · 13228 tokens

Now, for each circle, what's the central angle corresponding to the arc length of the belt on that circle? Let's take center A (top circle). The two tangent points on circle A are: one from the tangent segment between circle B and circle A, and one from the tangent segment between circle C and circle A. Let's denote:

- T_AB: the tangent point on circle A from the straight segment connecting circle A and circle B

- T_AC: the tangent point on circle A from the straight segment connecting circle A and circle C

Then the belt on circle A is the arc from T_AB to T_AC that is not between the tangent points on the other circles? Wait, no, for the belt going around the outside of the three circles, the arc on circle A should be the outer arc, which would be the longer arc or the shorter arc? Let's think about the triangle formed by the centers: ABC is equilateral with side 20. The angle at center A is 60 degrees (since it's equilateral). Now, the two radii to the tangent points T_AB and T_AC: let's see, if we consider the lines from center A to the tangent points on circle A, those radii should be perpendicular to the corresponding tangent segments (the straight segments between the circles).

Take the tangent segment between circle A and circle B (let's call this segment S_AB, tangent to circle A at T_AB and circle B at T_B). Since S_AB is tangent to circle A at T_AB, radius AT_AB is perpendicular to S_AB. Similarly, S_AB is tangent to circle B at T_B, so radius BT_B is perpendicular to S_AB. Therefore, AT_AB and BT_B are both perpendicular to S_AB, so they are parallel to each other. Similarly, for tangent segment S_AC between circle A and circle C, AT_AC and CT_AC are both perpendicular to S_AC, so parallel to each other.

Now, let's look at the angles at center A. The angle between AT_AB and AT_AC is the angle we need for the arc length on circle A. Let's consider the quadrilateral formed by centers A, B, T_B, T_AB. Wait, AT_AB and BT_B are both radii (length 10), both perpendicular to S_AB, so quadrilateral AT_AB T_B B has two right angles at T_AB and T_B, and two sides AT_AB = BT_B = 10, so this is a rectangle! Wait, yes! Because angles at T_AB and T_B are right angles, and sides AT_AB and BT_B are equal and parallel (both perpendicular to the same line), so yes, it's a rectangle. Therefore, the angle at center A in this rectangle is the angle between AT_AB and AB, but wait, in a rectangle, all angles are 90 degrees, but actually, the sides are AT_AB and AB? Wait, no: vertices A, T_AB, T_B, B connected in order: A to T_AB is radius, T_AB to T_B is the tangent segment S_AB, T_B to B is radius, B to A is the center-to-center segment. So angles at T_AB and T_B are right angles (since radii perpendicular to tangent), so yes, quadrilateral AT_AB T_B B is a rectangle. Therefore, angle at A is equal to angle at B: angle T_AB A B = 90 degrees? Wait, no, in a rectangle, adjacent angles are 90 degrees, but the angle at A is between sides A T_AB and A B. Wait, in quadrilateral AT_AB T_B B, sides: A-T_AB, T_AB-T_B, T_B-B, B-A. Angles at T_AB and T_B are 90 degrees (right angles), so the other angles (at A and B) must also be 90 degrees? Wait, no, sum of angles in quadrilateral is 360 degrees, so two right angles sum to 180, so the other two angles sum to 180, so if it's a rectangle, yes, all angles 90 degrees. Wait, but that would mean angle at A (between A-T_AB and A-B) is 90 degrees? But in our coordinate system, center A is at (0,10√3), center B at (-10,0), so the angle between vectors A-B and A-T_AB should be... Wait, maybe better to use vectors or coordinates.

Take specific coordinates: center A(0, 10√3), center B(-10, 0), radius 10. Tangent segment S_AB is external tangent to both circles, so as we tried earlier, let's take the tangent point on circle A: we had vector v = (-5√3, 5) gives point P = A + v = (-5√3, 10√3 + 5). Let's check the vector from A to P: (-5√3, 5), which has length sqrt(75 + 25) = sqrt(100) = 10, good, radius. Now, the vector from A to B is (-10, -10√3). Now, what's the angle between vectors AP and AB? Dot product: AP • AB = (-5√3)(-10) + (5)(-10√3) = 50√3 - 50√3 = 0. Oh! So the vectors AP and AB are perpendicular! That's why the quadrilateral was a rectangle: AP is perpendicular to AB (since dot product zero), and BT_B is also perpendicular to AB (since AB is the side of the rectangle), so yes, angle between AP and AB is 90 degrees.

Wait, that's a key insight. Let's verify with another point. Vector from A to B is (-10, -10√3), which has length 20, as we know. Vector AP is (-5√3, 5), length 10, and AP • AB = 0, so yes, perpendicular. Similarly, vector from B to T_B should be the same as vector from A to P, since the tangent segment is straight, so vector BT_B = AP = (-5√3, 5), so T_B = B + BT_B = (-10 -5√3, 0 + 5), which is the tangent point on circle B we had earlier. And vector BT_B • AB = (-5√3, 5) • (-10, -10√3) = 50√3 - 50√3 = 0, so BT_B is also perpendicular to AB, which makes sense for the rectangle.

So, for the tangent segment between circles A and B, the radius to the tangent point on A (AT_AB) is perpendicular to the center-to-center line AB. Similarly, the radius to the tangent point on B (BT_B) is perpendicular to AB, which we just saw. Therefore, the two radii to the tangent points on circle A and B (for the segment S_AB) are both perpendicular to AB, meaning they are parallel to each other (both perpendicular to same line), which we knew, but also, the angle between AT_AB and AB is 90 degrees? Wait, no, in the coordinate example, we saw that AP (which is AT_AB) was perpendicular to AB, so the angle between AT_AB and AB is 90 degrees.

But now, let's look at the full angle at center A. Center A is connected to centers B and C, which form an equilateral triangle with angle 60 degrees at A. Now, we have two radii from A: AT_AB (towards the tangent point on circle A from circle B) and AT_AC (towards the tangent point from circle C). What's the angle between AT_AB and AB? We just saw it's 90 degrees, but is it on the same side or opposite?

Wait, in the coordinate system, center A is at (0, 10√3), center B is at (-10, 0), so the vector AB is from A to B: (-10, -10√3), which is pointing down and to the left. The tangent point T_AB on circle A is at (-5√3, 10√3 + 5) ≈ (-8.66, 15), which is to the left and slightly down from A (since 15 < 17.32), so the vector from A to T_AB is (-8.66, -2.32), which is left and down, matching the direction of AB (which is left and down). Wait, but earlier we saw AP • AB = 0, so AP is perpendicular to AB. Let's compute the slope of AB: from (0,17.32) to (-10,0), slope is (0 - 17.32)/(-10 - 0) = 17.32/10 ≈ 1.732, which is √3, so angle of AB with positive x-axis is 180° - 60° = 120° (since tanθ = √3, θ = 60°, but in second quadrant, 180-60=120°). Now, slope of AP: from (0,17.32) to (-8.66,15), slope is (15 - 17.32)/(-8.66 - 0) ≈ (-2.32)/(-8.66) ≈ 0.268, which is tan(15°), so angle ≈ 15° from positive x-axis, but wait, vector AP is (-8.66, -2.32), so direction is 180° + 15° = 195°? Wait, maybe better to compute the angle between vectors AB and AP.

Vector AB = B - A = (-10, -10√3) = 10(-1, -√3)

Vector AP = P - A = (-5√3, 5) = 5(-√3, 1)

Now, the angle φ between vectors AB and AP is given by cosφ = (AB • AP)/(|AB||AP|) = [(-10)(-5√3) + (-10√3)(5)] / [20 * 10] = [50√3 - 50√3] / 200 = 0, so φ = 90°, as we calculated before! So the angle between AB and AP is 90°, meaning AP is perpendicular to AB.

Similarly, let's find the angle between AC and AP, where AC is the vector from A to C (C is (10,0), so AC = C - A = (10, -10√3) = 10(1, -√3)). Vector AP = (-5√3, 5) = 5(-√3, 1). Let's compute the angle between AC and AP.

AC • AP = (10)(-5√3) + (-10√3)(5) = -50√3 - 50√3 = -100√3

|AC| = 20, |AP| = 10, so cosθ = (-100√3)/(20*10) = -√3/2 ⇒ θ = 150°

So the angle between AC and AP is 150°.

Now, let's look at the tangent point on circle A from circle C, which we can call T_AC. Similarly, by symmetry, the vector from A to T_AC should be perpendicular to AC, right? Because the tangent segment S_AC between A and C should have radius AT_AC perpendicular to S_AC, and S_AC is tangent to circle C, so CT_AC perpendicular to S_AC, so AT_AC || CT_AC, and for equal radii, similar to above, the angle between AC and AT_AC should be 90°. Let's check with coordinates: vector AC = (10, -10√3), so perpendicular vectors have dot product zero, so if AT_AC = (a, b), then 10a - 10√3 b = 0 ⇒ a = √3 b. Length AT_AC = 10, so sqrt(a² + b²) = 10 ⇒ sqrt(3b² + b²) = 2|b| = 10 ⇒ |b| = 5, so b=5, a=5√3 or b=-5, a=-5√3. Now, the direction: for the outer belt, we want the tangent points to be "outward" from the triangle ABC, so for circle A, the tangent points from B and C should be to the left and right from the center? Wait, vector AC is from A to C (right and down), so perpendicular vectors: (5√3, 5) is right and up from A, ( -5√3, -5) is left and down from A. But circle A is the top circle, so the outward tangent points for the belt should be to the left and right, not up or down. Wait, vector (5√3, 5) from A is to the right and up, which would be inside the triangle? Maybe we need the direction that's on the side opposite to the triangle's interior.

Wait, let's do the same calculation as for AP: we found for segment S_AB (between A and B), the tangent point T_AB on A is such that AP is perpendicular to AB, and we had vector AP = (-5√3, 5), which is a vector of length 10, perpendicular to AB. For segment S_AC (between A and C), let's find the vector AT_AC such that it's perpendicular to AC (since AT_AC is perpendicular to the tangent segment S_AC, just like AP is perpendicular to S_AB, and S_AB is parallel to S_AC? Wait, no, S_AB and S_AC are different segments, but for each segment, the radius to the tangent point is perpendicular to the segment.

Wait, actually, let's use the fact that for the entire belt, the straight segments form a "triangle" around the centers, and the angles at each center for the radii are related to the angle of the triangle.

Wait, here's a standard approach for three equal circles with a belt around them:

1. The centers form an equilateral triangle with side length 2r (since each pair is tangent, distance between centers is r + r = 2r).

2. The belt consists of three straight segments, each connecting a tangent point on one circle to a tangent point on an adjacent circle, and three arc segments, one on each circle, between the two tangent points for that circle.

3. For each circle, the angle of the arc (in radians) is equal to 360° minus the sum of the angles between the center-to-center lines and the radii to the tangent points.

Wait, we know that for each pair of circles, the straight segment is external tangent, so for two circles, the angle between the center-to-center line and the radius to the tangent point is 90°, as we saw from the dot product (since the radius is perpendicular to the tangent segment, and the tangent segment is parallel to the direction from one center to the other? Wait, no, in the rectangle example, we had the two radii perpendicular to the tangent segment, and the center-to-center line was the diagonal of the rectangle, so the angle between the radius and the center-to-center line is 90°.

Wait, let's go back to the rectangle: for two circles, centers A, B, distance AB = d. External tangent segment S, tangent to A at P, B at Q. Then AP ⊥ S, BQ ⊥ S, so AP || BQ, and AP = BQ = r. Therefore, the quadrilateral APQB has two right angles at P and Q, so it's a rectangle, hence AB is the diagonal of the rectangle, so the angle between AB and AP is θ, where cosθ = AP / AB = r / d, and sinθ = PQ / AB = (length of tangent segment)/d. Wait, yes! In the rectangle, sides AP = r, PQ = length of tangent segment, AB = d, so by Pythagoras: r² + (PQ)² = d² ⇒ PQ = sqrt(d² - r²). But in our case, r = r = 10, d = 20, so PQ = sqrt(400 - 100) = sqrt(300) = 10√3? Wait, but earlier in the horizontal case, for circles B and C, centers 20 apart, horizontal tangent segment was length 20, but wait, in that case, the tangent segment was horizontal, centers were on the x-axis, so the line connecting centers is horizontal, and the radii to the tangent points were vertical (upwards), so the rectangle was actually a square? Wait, no, centers at (-10,0) and (10,0), radius 10, so the tangent point on B is (-10,10), on C is (10,10), so PQ is from (-10,10) to (10,10), length 20. The vector AP (from A to P) is (-10,10), but wait, no: center A is the center of the circle, so radius to tangent point is from center to tangent point, so for circle B at (-10,0), tangent point on B is (-10,10), so radius is vector (0,10), which is vertical, length 10. Similarly for circle C, radius vector (0,10), vertical. Then the center-to-center line is from B to C: (20,0), horizontal. Now, quadrilateral formed by centers B, C, P (tangent on B), Q (tangent on C): B(-10,0), C(10,0), P(-10,10), Q(10,10). This is a rectangle with sides 20 (BC) and 10 (PQ), so yes, a rectangle, so the angle between BC (the diagonal?) Wait, no, the sides of the rectangle are BP (vertical, length 10) and PQ (horizontal, length 20), so the diagonal is BQ? Wait, B to Q is from (-10,0) to (10,10), length sqrt(400 + 100) = sqrt(500) = 10√5, not helpful.

Wait, maybe my earlier rectangle idea was confused: the two radii (from centers to tangent points) are both perpendicular to the tangent segment, so the angle between the two radii is equal to the angle between the two center-to-center lines? No, for two circles, the two tangent segments form a trapezoid with the two radii, but for equal radii, the trapezoid is a rectangle, so the angles at the centers are 90°? Wait, no, the radii are the two legs of the right trapezoid, which are equal in length for equal circles, so it's a rectangle, meaning the angle between the radius and the center-to-center line is not 90°, but rather the angle between the center-to-center line and the tangent segment is 90°? Wait, let's take the horizontal tangent segment between B and C: the tangent segment is horizontal, so its slope is 0, so the radii to the tangent points must be vertical (since perpendicular to horizontal), which is what we have: radii are vertical, length 10, centers are 20 apart horizontally, so the center-to-center line is horizontal, and the radii are vertical, so the angle between the center-to-center line (horizontal) and the radius (vertical) is 90°. Ah! There we go. For the external tangent segment that's horizontal between B and C (which are on the x-axis), the tangent segment is horizontal, so the radii to the tangent points are vertical (perpendicular to horizontal), hence the angle between the center-to-center line (which is horizontal) and the radius (vertical) is 90°.

Now, take another external tangent segment, say between A and B. Circle A is at top, circle B at left base. Let's find the tangent segment that's part of the outer belt, which should be the one not crossing the triangle ABC. So, for circles A and B, centers separated by 20, radii 10 each. The external tangent segment that's "above" the line AB (away from the center C) should be the one we want. Wait, in the horizontal case for B and C, the tangent segment was above the x-axis (since centers at y=0, radii 10, tangent at y=10). For circles A and B, centers at (0,10√3) and (-10,0), let's find the external tangent segment that's above the line AB (which is going from (-10,0) to (0,10√3), slope √3, so angle 60° from x-axis, so above the line AB would be the direction where the tangent segment is on the side opposite to center C, which is at (10,0), so the triangle ABC is equilateral, so all internal angles 60°, so the "outer" side of the belt would be away from the triangle, so for each pair of circles, the tangent segment is outside the triangle formed by all three centers.

Now, for two circles, the angle between the two centers and the tangent points: for external tangent, the angle between the center-to-center line and the radius to the tangent point is equal to (180° - θ)/2 or something? Wait, maybe use the fact that for the belt around the three circles, the total angle that the belt "turns" around the centers should correspond to the angles of the triangle.

Wait, here's a better method I remember for belt lengths around multiple circles:

- For a single circle, belt length is circumference, 2πr.

- For two circles, belt length (external) is 2*sqrt(d² - (r1 - r2)²) + (r1 + r2)π (wait, no, for two circles, the belt has two straight segments (external tangents) and two arcs (each arc is the rest of the circle). Wait, for two circles, the angle between the two tangent segments at the circle is 180° - 2θ, where θ is the angle between the center-to-center line and the radius, but maybe let's do two circles first to verify.

Wait, maybe stick to three circles. The key is that when you have a closed belt around n circles, the total length is equal to the length of the tangent segments between each pair of circles plus the sum of the arc lengths on each circle between the tangent points.

For three equal circles, centers form equilateral triangle with side 2r. Between each pair of circles, there is one straight tangent segment (external, since internal would cross the triangle), and for each circle, two tangent points (one from each adjacent circle), so the arc length on each circle is the total circumference minus the arcs corresponding to the angles between the two tangent segments at the circle.

Wait, let's consider the angle at each center for the two tangent lines to the circle. For a given circle, the two tangent lines (from the adjacent circles) form a certain angle, say α, and the arc length on the circle that is part of the belt is r*(2π - α), because the belt is on the outside, so it's the major arc if α is the minor angle.

Yes! That makes sense. For example, if the two tangent lines were perpendicular to each other (α = 90°), then the arc length would be 2πr - πr/2 = 3πr/2, but wait, no—if the angle between the two tangent lines is α, then the angle between the two radii to the tangent points is also α (since radii are perpendicular to tangent lines, so the angle between radii is equal to the angle between the tangent lines).

Wait, yes! If two lines are tangent to a circle at points P and Q, then the angle between the tangent lines is equal to the angle between the radii OP and OQ. Because OP is perpendicular to tangent at P, OQ is perpendicular to tangent at Q, so the angle between OP and OQ is equal to the angle between the tangents (since they're both angles between perpendiculars).

So, for circle with center O, two tangent lines intersecting at some point, the angle between the tangent lines is equal to the central angle subtended by the chord PQ (the points of tangency).

But in our case, the two tangent lines are not intersecting at a single point outside the circles, but rather the tangent lines are from two different circles: the tangent line to circle A from circle B and the tangent line to circle A from circle C. So for circle A, the two tangent lines are the straight segments S_AB (from B to A to C) and S_AC (from A to C to B)? Wait, no—S_AB is the straight segment between circle B and circle A, which is tangent to both B and A, and S_AC is the straight segment between circle A and circle C, tangent to both A and C. Therefore, for circle A, the two tangent lines to the belt are S_AB and S_AC, which are two straight lines, each tangent to circle A at one point (T_AB and T_AC), and the two tangent lines intersect at the vertex of the belt? Wait, no—the belt is a closed loop, so the two tangent segments S_AB and S_AC meet at the tangent point on circle A, but actually, no: the belt is a continuous curve, so at each circle, the belt has a straight segment approaching the circle from one side, then curves along the circle to the next straight segment. Wait, no, for the belt around the outside of three circles, the path is: straight from tangent point on circle 1 to tangent point on circle 2 (this is the S_12 segment), then straight from tangent point on circle 2 to tangent point on circle 3 (S_23), then straight from tangent point on circle 3 to tangent point on circle 1 (S_31), and for each circle, between the two tangent points (e.g., on circle 1, between tangent point of S_31 and tangent point of S_12), there is an arc segment.

Yes! That's the key: the belt is composed of three straight segments (S_12, S_23, S_31) connecting the tangent points on the circles, and for each circle, an arc segment (A_1, A_2, A_3) connecting the two tangent points on that circle. Therefore, for circle 1, arc A_1 is the arc from tangent point of S_31 to tangent point of S_12, and this arc is part of the belt. The same for the other circles.

Now, to find the arc length on each circle, we need to find the central angle corresponding to that arc. As established, for circle 1, the two tangent points are where the belt is tangent to the circle, and the two straight segments S_31 and S_12 are tangent to the circle at those points, so the radii to those tangent points are perpendicular to the straight segments. Therefore, if we consider the center of circle 1 (O_1), the radii to the tangent points (say, O_1T_12 and O_1T_31) are both perpendicular to the straight segments S_12 and S_31, respectively.

Let’s denote the angle at O_1 between the two radii O_1T_12 and O_1T_31 as φ_1, which is the central angle corresponding to arc A_1. Then the arc length A_1 = r * φ_1 (in radians). Similarly, φ_2 and φ_3 for the other circles.

Now, let's find φ_1. Consider the centers O_1, O_2, O_3 forming triangle O_1O_2O_3. For circle 1, the straight segment S_12 is tangent to O_2 and O_1, so O_1T_12 ⊥ S_12 and O_2T_12 ⊥ S_12, meaning O_1T_12 || O_2T_12. Similarly, for segment S_13, O_1T_13 ⊥ S_13 and O_3T_13 ⊥ S_13, so O_1T_13 || O_3T_13.

Now, consider the lines O_1O_2 and O_1O_3. The angle between O_1O_2 and O_1T_12 is 90°, because O_1T_12 is perpendicular to S_12, and S_12 is tangent to O_2, so O_2T_12 is perpendicular to S_12, hence O_1T_12 and O_2T_12 are parallel, so the angle between O_1O_2 and O_1T_12 is equal to the angle between O_1O_2 and O_2T_12, which is the angle between the center-to-center line and the radius, which is 90° due to the rectangle formed by the centers and tangent points.

Wait, let's use the triangle formed by the centers. For circle 1, center O_1, we have two radii O_1T_12 and O_1T_13, each perpendicular to the respective straight segments. The straight segments S_12 and S_13 meet at the tangent point on circle 1, so the angle between S_12 and S_13 at circle 1 is the same as the angle between the tangent segments at the circle, which we need to relate to the triangle O_1O_2O_3.

Wait, here's a standard result: for three circles of equal radius, the total length of the belt (external) is equal to the perimeter of the equilateral triangle formed by the centers plus the total length of the arcs on the circles.

Wait, let's think about the straight segments first. Each straight segment is the external tangent between two adjacent circles. For two circles of radius r, centers separated by d = 2r (since they're tangent), the length of the external tangent segment is, as we calculated earlier with the formula: sqrt(d² - (r - r)²) = sqrt((2r)² - 0) = 2r. Wait, but earlier in the horizontal case for circles B and C (d=20, r=10), the external tangent segment was length 20, which is 2r, so that checks out! For the horizontal tangent between B and C, which are centers 20 apart, the straight segment length was 20, which is 2r.

But wait, is the external tangent segment length 2r for two circles of radius r, centers separated by 2r? Let's confirm with another pair: circles A and B, centers 20 apart, radius 10 each. The external tangent segment: if we consider the two radii to the tangent points, they are parallel (both perpendicular to the tangent segment), so the distance between the centers projected along the direction of the radii is zero (since they're equal), so the straight segment length should be equal to the distance between centers? Wait, yes, in the horizontal case, the centers were horizontally aligned, radii vertical, so the tangent segment was horizontal, length equal to center distance. In the diagonal case, like A and B, the tangent segment should also have length equal to center distance, because the radii are parallel, so the straight segment length is equal to the center distance.

Wait, let's prove it generally for two circles, radii r, centers separated by d, external tangent length L. Since radii are parallel (both perpendicular to tangent segment), the line connecting centers and the tangent segment form a right trapezoid with two equal sides (radii), so the length of the tangent segment is equal to the length of the side parallel to the tangent segment, which in this case, since the radii are equal, the trapezoid is a rectangle, so L = d. Wait, no: in the right trapezoid with two right angles, one side length r (radius), one side length L (tangent segment), hypotenuse d (center distance), so by Pythagoras: r² + L² = d² ⇒ L = sqrt(d² - r²). But wait, if the radii are equal, then (r - r) = 0, so the internal tangent length would be sqrt(d² - (2r)²), but external tangent is sqrt(d² - 0) = d.

Wait, yes! This is the key formula I messed up earlier:

- External tangent (not crossing between the circles): length = sqrt(d² - (r1 - r2)²)

- Internal tangent (crossing between the circles): length = sqrt(d² - (r1 + r2)²)

Yes! That's correct. For equal radii, r1 = r2 = r, so external tangent length = sqrt(d² - 0) = d, internal tangent length = sqrt(d² - (2r)²). But in our case, for two circles, d = 2r (since they're tangent), so external tangent length = sqrt(4r² - 0) = 2r, which matches our horizontal case (d=20, r=10, external tangent length=20=2r). Internal tangent length would be sqrt(4r² - 4r²)=0, which makes sense because when circles are tangent, the internal tangent would coincide at the point of tangency.

Great, so for two adjacent circles in our problem, each pair is tangent, so d = 2r = 20, so external tangent segment length = 2r = 20 cm. Wait, but hold on—there are three straight segments, each between two adjacent circles, so total straight segment length is 3 * 2r = 3 * 20 = 60 cm? Wait, but let's check with the horizontal case between B and C: they're adjacent, external tangent segment length=20, which is correct. What about the segment between A and B: is the external tangent segment length also 20? Let's compute it using the formula: d=20, r1=r2=10, so sqrt(20² - 0)=20, yes, so each straight segment is 20 cm, so three segments total 60 cm.

Now, the arc segments: for each circle, what's the length of the arc that is part of the belt? The belt goes around the outside of all three circles, so for each circle, the arc on the belt is the part of the circle that's not between the two straight segments (i.e., the arc that's "outside" the triangle formed by the centers).

To find the arc length, we need the central angle corresponding to that arc. As we said earlier, the two straight segments meet the circle at two points, and the radii to those points are perpendicular to the straight segments. Let's consider the angles formed by the radii and the center-to-center lines.

Take circle A (top circle), centers B and C below it. The straight segment from B to A is tangent to circle A at point T_AB, and the straight segment from C to A is tangent to circle A at point T_AC. The radius AT_AB is perpendicular to the straight segment S_AB, and radius AT_AC is perpendicular to straight segment S_AC.

Now, consider the triangle formed by centers A, B, C. It's equilateral with all angles 60°. Let's look at the angles at center A. We know that the angle between AB and AC is 60°, because it's an equilateral triangle.

Now, what's the angle between AT_AB and AB? Since AT_AB is perpendicular to S_AB, and S_AB is tangent to circle B, let's look at the triangle formed by centers A, B, and the tangent point T_AB. Wait, we already did this with coordinates earlier and found that AT_AB is perpendicular to AB, but let's use vectors or angles properly.

Consider the line AB: from center A to center B. The straight segment S_AB is tangent to both circles, so the radius AT_AB is perpendicular to S_AB. Now, the direction of S_AB: since it's a tangent, it's parallel to the line that's tangent to both circles, so the angle between AB and S_AB can be found, but maybe instead, consider the angle between AB and the direction of the radius.

Wait, here's a better way: for each circle, the two radii to the tangent points are each at some angle to the center-to-center lines. Let's consider the external tangent between circle A and circle B: the angle between the center-to-center line AB and the radius to the tangent point (say, AT_AB) is equal to the angle that the radius makes with the direction of the tangent segment.

But since we know that the two radii to the tangent points for a circle are parallel to the radii of the adjacent circles (because they're both perpendicular to the tangent segment), and the centers form an equilateral triangle, let's think about the angles between the center-to-center lines and the radii.

Wait, let's use the fact that for the belt, the total angle "turned" by the belt as it goes around the three circles should be 360°, but actually, the sum of the angles at each center for the radii (the angles between the two radii to the tangent points) plus the angles of the triangle should relate to a full circle.

Wait, consider the triangle formed by the centers: O_A O_B O_C, equilateral, each angle 60°. Now, for each circle, say O_A, we have two radii: O_A T_AB (to tangent point on A from B) and O_A T_AC (to tangent point on A from C). The vectors O_A T_AB and O_A T_AC are both perpendicular to the respective tangent segments.

Now, the tangent segment from A to B (S_AB) is perpendicular to O_A T_AB and perpendicular to O_B T_AB (since O_B T_AB is radius to tangent point on B). Therefore, O_A T_AB is parallel to O_B T_AB (both perpendicular to S_AB), so the angle between O_A O_B and O_B T_AB is equal to the angle between O_A O_B and O_A T_AB (since they're parallel).

Let's denote θ as the angle between O_A O_B and O_B T_AB. Since O_B T_AB is a radius (length r=10) and O_A O_B is the center-to-center distance (length 2r=20), in the triangle O_A O_B T_AB, we have O_A O_B = 2r, O_B T_AB = r, and O_A T_AB = r (radii). Wait, triangle O_A O_B T_AB: sides O_A O_B = 20, O_B T_AB = 10, O_A T_AB = 10. Oh! This is an isoceles triangle with two sides equal to 10, one side equal to 20? Wait, no: O_A T_AB = r = 10, O_B T_AB = r = 10, so it's an isoceles triangle with O_A T_AB = O_B T_AB = 10, base O_A O_B = 20. But in a triangle, the sum of two sides must be greater than the third side, but 10 + 10 = 20, which is equal to the third side, so the triangle is degenerate! Wait, that means the three points O_A, O_B, T_AB are colinear!

Oh my goodness, that's the key! If two circles are tangent, the point of tangency lies on the line connecting the centers. But in our case, the tangent segment S_AB is tangent to both circles, but the point of tangency for the belt isn't the point where the circles are tangent to each other, it's a different point.

Wait, yes! The circles are tangent to each other at a single point (let's call it P_AB), so the line O_A O_B passes through P_AB, and O_A P_AB = O_B P_AB = r = 10, so O_A O_B = 20 = O_A P_AB + O_B P_AB, so colinear.

But the belt's tangent segment S_AB is a different tangent line that's not at the point of tangency P_AB, but a different point where the belt touches circle A and circle B. Therefore, the tangent segment S_AB is a common external tangent, not the one at the point of tangency between the circles.

Therefore, triangle O_A O_B T_AB is not degenerate, but a triangle with sides:

- O_A T_AB = r = 10 (radius of circle A to tangent point T_AB)

- O_B T_AB = r = 10 (radius of circle B to tangent point T_AB)

- O_A O_B = 2r = 20 (distance between centers)

Wait, but again, 10 + 10 = 20, so it's degenerate. Wait, no! Wait, the radius to the tangent point is perpendicular to the tangent segment, so in triangle O_A T_AB T_B, where T_B is the tangent point on circle B for segment S_AB, we have:

- O_A T_AB ⊥ S_AB (radius ⊥ tangent)

- O_B T_B ⊥ S_AB (radius ⊥ tangent)

Therefore, O_A T_AB || O_B T_B (both perpendicular to same line), and both have length r = 10.

Thus, quadrilateral O_A T_AB T_B O_B has two right angles at T_AB and T_B, so it's a rectangle.

Therefore, O_A O_B is the diagonal of the rectangle, so the length of O_A O_B = sqrt( (O_A T_AB)² + (T_AB T_B)² ) = sqrt( r² + (length of tangent segment)² )

Wait, yes! In a rectangle, the diagonal squared is equal to the sum of the squares of the two adjacent sides. Here, adjacent sides are the radius (r) and the length of the tangent segment (L), so:

d² = r² + L² ⇒ L = sqrt(d² - r²)

But in our case, d = 2r (since circles are tangent), so L = sqrt(4r² - r²) = sqrt(3r²) = r√3

Ah! Here's the mistake I made earlier: I forgot that the radii are perpendicular to the tangent segment, so the triangle formed by the centers and the tangent points is a right triangle with legs r and L, hypotenuse d.

Wait, yes! Let's take the horizontal example: circles B and C, centers 20 apart, radius 10 each. The topmost tangent point on B is (-10,10), on C is (10,10), so tangent segment length is 20. The distance from B to the tangent point is vertical, length 10 (radius), so the horizontal distance between the tangent points is 20, which is the length of the tangent segment. Wait, but the horizontal distance is 20, which is the center distance, and the vertical distance (radius) is 10, so d = 20, r = 10, L = 20. But according to the right triangle: if you go from center B to tangent point T_B, that's vertical up, length r = 10, then from T_B to tangent point T_C is horizontal, length L = 20, then from T_C to center C is vertical down, length r = 10. So the line from B to C is the diagonal of the rectangle formed by B, T_B, T_C, C, which has sides r = 10 and L = 20, so diagonal BC = sqrt(10² + 20²) = sqrt(500) = 10√5 ≈ 22.36, but we know BC = 20. Wait, no! I mixed up the rectangle.

Wait, center B(-10,0), tangent point T_B(-10,10) [top of circle B], center C(10,0), tangent point T_C(10,10) [top of circle C]. Then the rectangle is B(-10,0), T_B(-10,10), T_C(10,10), C(10,0). Yes! This is a rectangle with width BC = 20 (from x=-10 to x=10) and height BT_B = 10 (from y=0 to y=10). Therefore, the diagonal of the rectangle is BT_C? Wait, no, the diagonal of the rectangle is from B to T_C: distance sqrt(20² + 10²) = sqrt(500), but that's not the center-to-center distance. The center-to-center distance is BC = 20, which is the length of the rectangle's width, which is one side of the rectangle.

Ah! I see now: in this rectangle, BC is a side (length d = 20), BT_B is another side (length r = 10), and the tangent segment is T_B T_C, which is equal to BC in length? Wait, no, T_B T_C is from (-10,10) to (10,10), length 20, which is equal to BC (from (-10,0) to (10,0), length 20). So T_B T_C is parallel and equal to BC, making the figure a parallelogram, and since angles at T_B and T_C are right angles, it's a rectangle, with sides BC = 20 and BT_B = 10.

But why is the tangent segment length equal to BC? Because in this case, the tangent segment is horizontal, and the radii are vertical, so the tangent segment is equal and parallel to the line connecting the centers, which makes sense for equal radii.

Wait, let's use the correct right triangle: for two circles with centers O1, O2, radii r1, r2, the length of the external tangent segment is L = sqrt(d² - (r1 - r2)²), as per standard formula. Let's verify this formula with the horizontal case: O1(-10,0), O2(10,0), r1 = r2 = 10, so L = sqrt(20² - 0) = 20, which matches the tangent segment length (20). For the diagonal case, O1(0,10√3), O2(-10,0), d = 20, r1 = r2 = 10, so L = sqrt(400 - 0) = 20, so the tangent segment length should also be 20. Let's compute the tangent segment length between circle A and circle B using the formula.

Coordinates: O1(0, 10√3), O2(-10, 0), r1 = r2 = 10.

External tangent lines: we can use the formula for distance from center to line. Let the tangent line be y = mx + c. Distance from O1 to line: |10√3 - m*0 - c| / sqrt(m² + 1) = |10√3 - c| / sqrt(m² + 1) = 10 ⇒ (10√3 - c)² = 100(m² + 1)

Distance from O2 to line: |0 - m*(-10) - c| / sqrt(m² + 1) = |10m - c| / sqrt(m² + 1) = 10 ⇒ (10m - c)² = 100(m² + 1)

Set equal: (10√3 - c)² = (10m - c)² ⇒ 100*3 - 20√3 c + c² = 100m² - 20m c + c² ⇒ 300 - 20√3 c = 100m² - 20m c ⇒ 300 - 100m² = 20c(√3 - m) ⇒ 10(30 - 10m²) = 20c(√3 - m) ⇒ 30 - 10m² = 2c(√3 - m) ⇒ c = (30 - 10m²)/(2(√3 - m)) = 5(3 - m²)/(2(√3 - m))

Now, let's assume the external tangent is the one above the line O1O2 (the triangle is above the base, so the belt is outside, so upper external tangent), so let's take m such that the tangent line is above. Let's solve for c:

From (10m - c)² = (10√3 - c)², we had two cases: either 10m - c = 10√3 - c ⇒ m = √3, or 10m - c = c - 10√3 ⇒ 10m + 10√3 = 2c ⇒ c = 5m + 5√3.

Case 1: m = √3, then c = 5*√3 + 5√3 = 10√3. Then the line is y = √3 x + 10√3. Let's check distance from O1(0,10√3) to line: |10√3 - 0 - 10√3| / sqrt(3 + 1) = 0 / 2 = 0, which is less than radius, so the line passes through O1, not tangent.

Case 2: c = 5m + 5√3, now plug back into (10m - c)² = 100(m² + 1):

10m - c = 10m - 5m - 5√3 = 5m - 5√3

So (5m - 5√3)² = 100(m² + 1) ⇒ 25(m - √3)² = 100(m² + 1) ⇒ (m - √3)² = 4(m² + 1) ⇒ m² - 2√3 m + 3 = 4m² + 4 ⇒ 0 = 3m² + 2√3 m + 1 ⇒ 3m² + 2√3 m + 1 = 0 ⇒ discriminant = 12 - 12 = 0 ⇒ m = (-2√3)/6 = -√3/3

Ah, so m = -√3/3, then c = 5*(-√3/3) + 5√3 = (-5√3/3) + 15√3/3 = 10√3/3

So the external tangent line is y = (-√3/3)x + 10√3/3

Now, let's find the tangent points on circle A and circle B.

Circle A: x² + (y - 10√3)² = 100

Substitute y = (-√3/3)x + 10√3/3 into circle A's equation:

x² + [ (-√3/3 x + 10√3/3 - 10√3) ]² = 100

Simplify the y-term: (-√3/3 x) + (10√3/3 - 30√3/3) = (-√3/3 x) - 20√3/3 = -√3/3 (x + 20)

So equation becomes:

x² + [ -√3/3 (x + 20) ]² = 100 ⇒ x² + (3/9)(x + 20)² = 100 ⇒ x² + (1/3)(x² + 40x + 400) = 100 ⇒ multiply by 3: 3x² + x² + 40x + 400 = 300 ⇒ 4x² + 40x + 100 = 0 ⇒ x² + 10x + 25 = 0 ⇒ (x + 5)² = 0 ⇒ x = -5

So tangent point on circle A is at x = -5, y = (-√3/3)(-5) + 10√3/3 = (5√3/3 + 10√3/3) = 15√3/3 = 5√3

So point T_AB = (-5, 5√3)

Now, check distance from center A(0,10√3) to T_AB: sqrt( (-5 - 0)² + (5√3 - 10√3)² ) = sqrt(25 + ( -5√3 )² ) = sqrt(25 + 75) = sqrt(100) = 10, correct, radius.

Now, tangent point on circle B: center B(-10,0), circle B equation: (x + 10)² + y² = 100

Substitute y = (-√3/3)x + 10√3/3 into circle B's equation:

(x + 10)² + [ (-√3/3 x + 10√3/3) ]² = 100

Simplify y-term: same as before, -√3/3 (x - 10), wait:

Wait, (-√3/3 x + 10√3/3) = (-√3/3)(x - 10), yes, so y = -√3/3 (x - 10)

Then y² = (3/9)(x - 10)² = (1/3)(x - 10)²

(x + 10)² + (1/3)(x - 10)² = 100

Multiply by 3: 3(x + 10)² + (x - 10)² = 300

Expand: 3(x² + 20x + 100) + x² - 20x + 100 = 300 ⇒ 3x² + 60x + 300 + x² - 20x + 100 = 300 ⇒ 4x² + 40x + 400 = 300 ⇒ 4x² + 40x + 100 = 0 ⇒ same as before, x² + 10x + 25 = 0 ⇒ x = -5

So tangent point on circle B is at x = -5, y = (-√3/3)(-5) + 10√3/3 = 15√3/3 = 5√3, same y as on circle A!

Wait, so T_AB = (-5, 5√3) and T_B = (-5, 5√3), which is the same point? No, that can't be—wait, no, for circle B, x = -5, y = 5√3, so T_B = (-5, 5√3), and for circle A, also x = -5, y = 5√3. Wait, but that's the same point, which means the tangent line is the common tangent at the point where the circles are tangent? But circle A and circle B are not tangent to each other; they're tangent to circle C? Wait, no, in our coordinate system, circle A is at (0,10√3), circle B at (-10,0), circle C at (10,0), so distance AB = 20, AC = 20, BC = 20, so all pairs are tangent! Wait, yes! Three circles, each pair tangent, so all three circles are mutually tangent, so the tangent point between A and B is on the line AB, 10 units from A and B, so at ( (-10 + 0)/2, (0 + 10√3)/2 )? Wait, no, line AB from (-10,0) to (0,10√3), parametric form: x = -10 + 10t, y = 0 + 10√3 t, t ∈ [0,1]. Point at t=0.5: x=-5, y=5√3, which is the midpoint of AB. But distance from A to this point: sqrt( (0 - (-5))² + (10√3 - 5√3)² ) = sqrt(25 + 75) = 10, which is radius, so yes, the point (-5, 5√3) is the point of tangency between circles A and B! But wait, we're trying to find a tangent segment for the belt, which should be a different tangent, not the one at the point of tangency between the circles.

Wait, now I see the confusion: the problem states "a belt is drawn tightly around three circles of radius 10 cm each". If the three circles are mutually tangent, the "belt" that goes around them tightly without crossing through the circles should be the one that goes around the outside, so it's not the inner belt that goes around the triangle formed by the circles, but the outer belt that encloses all three circles.

For three mutually tangent circles, the outer belt will have three straight segments, each tangent to two adjacent circles (not at their point of tangency), and three curved segments, one on each circle, between the two tangent points.

Let's find the tangent segment between circle A and circle B, not at the point of tangency. We found the external tangent line with equation y = (-√3/3)x + 10√3/3, and it's tangent to circle A at (-5, 5√3), but wait, (-5, 5√3) is the point of tangency between A and B, so that's the common tangent at the point of contact between A and B. But the belt is supposed to be tight around all three circles, so it shouldn't go through the area between the circles, so we need the other external tangent, the one that doesn't cross the line segment AB.

Wait, earlier when we solved for the tangent lines, we had two cases: m = √3 (which gave the line through O1) and m = -√3/3. What about the other solution? When we had (10√3 - c)² = (10m - c)², we had two solutions, but maybe we missed the internal tangent.

Internal tangent: for two circles, internal tangent length is sqrt(d² - (r1 + r2)²), but for d = 2r, this is sqrt(4r² - 4r²) = 0, so no internal tangent, which makes sense—when circles are tangent, the internal tangent is the point of tangency.

Wait, no, for two circles, there are two external tangents (not crossing between them) and two internal tangents (crossing between them). For equal radii, the two external tangents are parallel, and the two internal tangents intersect at the midpoint of the center line.

Let's find the internal tangent between circles A and B. The internal tangent would have the radii to the tangent points pointing in opposite directions, so the triangle O_A O_B T_AB is not a rectangle, but a triangle with sides r, r, d (since d = 2r, it's isoceles with two sides 10, base 20, which is degenerate as we saw, so actually, the internal tangent for equal radii is just the line connecting the centers, but the point of tangency is on that line).



## B5 · steps 404–553 · INTERMEDIATE_COMPUTATION · 7846 tokens

Wait, I think I need to step back and look for a standard solution for three equal circles with a belt around them.

Upon recalling, for three circles of radius r, mutually tangent, the belt length (external) is equal to the perimeter of the equilateral triangle formed by the centers plus the total length of the arcs on the circles that are covered by the belt.

The perimeter of the triangle formed by the centers: each side is 2r, so perimeter = 3*2r = 6r.

Now, for each circle, how much of the circumference is covered by the belt? When you draw a belt around three mutually tangent circles, each circle is "pushed" by the belt, and the angle of the arc not covered by the belt (the part facing the center of the triangle) is equal to the angle of the triangle at that vertex.

In the equilateral triangle of centers, each angle is 60°. Now, consider one circle; the belt wraps around the circle, and the angle between the two tangent segments (from the adjacent circles) at the circle's center is equal to 180° - 60° = 120°, because the tangent segments form a straight line with the radius? Wait, let's use the right angles.

As established earlier, for each circle, the two radii to the tangent points are perpendicular to the straight segments. Let's consider the angles at the center of the circle.

Take circle A, centers B and C. The straight segment from B to A (S_AB) is tangent to circle A at T_AB, so radius AT_AB ⊥ S_AB. Similarly, straight segment from C to A (S_AC) is tangent to circle A at T_AC, so radius AT_AC ⊥ S_AC.

The angle between S_AB and S_AC at the belt's intersection with circle A is equal to the angle of the triangle formed by the centers? Wait, at circle A, the belt has a "corner" where the two straight segments meet, but actually, the straight segments S_AB and S_AC meet at the tangent point on circle A, so the angle between S_AB and S_AC at the tangent point on circle A is equal to the angle between the two tangent segments.

Wait, here's a better way using the direction of the radii:

- The radius AT_AB is perpendicular to S_AB, so the direction of AT_AB is 90° from the direction of S_AB.

- Similarly, AT_AC is perpendicular to S_AC.

- Now, the direction of S_AB can be related to the direction of AB (the center-to-center line).

- In the rectangle formed by the centers and tangent points (for two circles), the angle between the center-to-center line and the radius is 90°, but wait, no—if we have two circles, centers O1, O2, radii r, tangent segment S at T1 (on O1) and T2 (on O2), then O1T1 ⊥ S, O2T2 ⊥ S, so O1T1 || O2T2.

- The angle between O1O2 and O1T1 is equal to the angle between O1O2 and O2T2.

- In the triangle formed by O1, O2, T1, T2, which is a rectangle, the angle between O1O2 and O1T1 is equal to 90° minus the angle of the triangle.

Wait, no—since it's a rectangle, O1O2 is the diagonal, so the angle between O1O2 and O1T1 is equal to the angle between the diagonal and one side of the rectangle, which is θ, where sinθ = opposite/hypotenuse = (length of tangent segment)/d, cosθ = adjacent/hypotenuse = r/d.

But for our problem, with three circles, let's consider the three straight segments:

Each straight segment is the external tangent between two adjacent circles, so for each pair, the straight segment length is L = sqrt(d² - (r - r)²) = sqrt((2r)² - 0) = 2r, but wait, we know that for two circles with radii r, centers distance d apart, external tangent length is sqrt(d² - (r - r)²) = d when r1 = r2.

But in reality, for two circles with radius r, centers distance 2r apart, the external tangent length (not the one at the point of tangency) is actually not d, but let's compute it with the rectangle:

The two radii to the tangent points are both length r, parallel to each other, so the distance between the centers along the direction perpendicular to the tangent segment is r - r = 0 (since radii are equal), and along the direction parallel to the tangent segment is the tangent segment length L.

Wait, no—the distance between the centers projected onto the direction perpendicular to the tangent segment is equal to |r1 - r2|, so for equal radii, it's 0, hence the tangent segment length is equal to the distance between centers, which is 2r.

Yes! The formula for the length of the external tangent between two circles is sqrt(d² - (r1 - r2)²). For equal radii, this is sqrt(d² - 0) = d. For two circles each of radius r, tangent to each other, d = 2r, so external tangent length = 2r.

Wait, but if d = 2r, and we have two circles, the external tangent length is 2r, which makes sense because the tangent segment is equal and parallel to the center line.

Now, for the arc length on each circle: when the belt goes around the three circles, for each circle, the part of the belt that is on the circle is an arc, and the angle of this arc can be found by considering the angles between the radii to the tangent points.

Since the three centers form an equilateral triangle, each angle is 60°. Now, at each circle, the two radii to the tangent points are each perpendicular to the straight segments. The straight segments form a triangle with the center-to-center lines, and the angles between the radii can be found by subtracting the angles from the triangle's angle.

Wait, here's a geometric argument:

Consider the three centers O_A, O_B, O_C forming an equilateral triangle with side length 2r. The belt is tangent to each circle at two points, forming three straight segments S_AB, S_BC, S_CA.

For each circle, say O_A, the two tangent points T_AB (on S_AB) and T_AC (on S_AC) form an arc. The key is to find the angle subtended by arc T_AB T_AC at O_A.

Since the straight segments S_AB and S_AC are tangent to the circle at T_AB and T_AC, the radii O_A T_AB and O_A T_AC are perpendicular to S_AB and S_AC, respectively.

Now, consider the quadrilateral formed by O_A, O_B, T_B, T_AB (where T_B is the tangent point on O_B for S_AB). As established, O_A T_AB ⊥ S_AB and O_B T_B ⊥ S_AB, so O_A T_AB || O_B T_B. Therefore, angle O_A T_AB O_B is equal to angle O_B T_B O_A (corresponding angles).

The angle at O_B in quadrilateral O_A O_B T_B T_AB is the angle between O_B O_A and O_B T_B. Since O_B T_B is a radius, and O_B O_A is the center-to-center line, which has length 2r.

Wait, maybe look at the triangle O_A O_B O_C. For circle A, the angle between O_A O_B and O_A O_C is 60°. Now, the angle between O_A T_AB and O_A O_B: since O_A T_AB is perpendicular to S_AB, and S_AB is the straight segment, which is parallel to... Wait, in the triangle formed by the centers, the angle at O_A is 60°, and the two radii O_A T_AB and O_A T_AC form an angle that is equal to 180° - 60° = 120°.

Wait, let's use the fact that the sum of all the angles between the radii for the arcs should relate to the total circle.

Consider the triangle formed by the three centers: ABC. For each circle, the belt "turns" around the circle, and the angle of the arc is 360° minus the angle at the center of the triangle.

Wait, another approach: the total length of the belt is equal to the sum of the lengths of the straight segments plus the sum of the arc lengths.

We already know there are three straight segments, each between two adjacent circles. Let's find their length using the standard external tangent formula.

For two circles of radius r, centers separated by d = 2r (since they're mutually tangent), the external tangent length is L = sqrt(d² - (r - r)²) = sqrt(4r² - 0) = 2r. But wait, let's take a step back with coordinates where the belt is clearly drawn.

Wait, suppose we have three circles, centers at (0, 0), (2r, 0), (r, r√3), which is an equilateral triangle with side 2r.

The top circle is at (r, r√3), radius r, so its center is at height r√3, which is (r√3)/r = √3 times the radius, which makes sense for an equilateral triangle with side 2r: height is (2r)(√3)/2 = r√3, correct.

Now, the belt should go around the outside, so it will have a straight segment on the top side (between the left and right bottom circles) and two straight segments on the sides connecting to the top circle.

Wait, let's find the straight segment between the left bottom circle (center (-r, 0), radius r) and the right bottom circle (center (r, 0), radius r), so centers 2r apart, horizontal line. The top tangent segment for the belt between these two circles should be above the x-axis. The tangent points on the bottom circles will be at (±r, r), so the tangent segment is from (-r, r) to (r, r), length 2r, which matches our earlier calculation.

Now, the straight segment between the left bottom circle (center (-r, 0), radius r) and the top circle (center (r, r√3), radius r). Let's find the external tangent segment between them.

Centers: O1(-r, 0), O2(r, r√3), d = distance = sqrt( (2r)² + (r√3)² ) = sqrt(4r² + 3r²) = sqrt(7r²) = r√7, but wait, no—our centers are (0,0), (2r,0), (r, r√3), so distance between (0,0) and (2r,0) is 2r, between (0,0) and (r, r√3) is 2r, between (2r,0) and (r, r√3) is 2r, so d = 2r for all pairs.

Center O1(0,0), O2(2r,0), O3(r, r√3).

Straight segment between O1 and O2: centers on x-axis, 2r apart, radius r each. The top external tangent is at y = r, tangent points (0, r) and (2r, r), length 2r, correct.

Straight segment between O1 and O3: centers at (0,0) and (r, r√3), distance 2r. Let's find the external tangent segment that's part of the belt (above the line O1O3).

Using the formula for external tangent length: L = sqrt(d² - (r - r)²) = sqrt(4r² - 0) = 2r.

Now, what's the angle of the arc on circle O1 between the two tangent points?

Circle O1 (0,0) has two tangent points: one from the straight segment to O2 (which is at (0, r) for the top segment), and one from the straight segment to O3 (let's find it).

Tangent point on O1 from O3: let's denote it as P, so OP ⊥ tangent segment S.

Tangent segment S is tangent to O1 and O3, so P is on O1's circle, so OP = r, and Q is on O3's circle, O3Q = r, O1Q ⊥ S, OP ⊥ S, so OP || O3Q.

Therefore, quadrilateral O1PQS has two right angles at P and Q, so it's a rectangle, so O1O3 is the diagonal of the rectangle, so length O1O3 = sqrt(OP² + PQ²) = sqrt(r² + L²) ⇒ L = sqrt(d² - r²) = sqrt(4r² - r²) = r√3.

Ah! Here's the correct formula for the external tangent length when the radii are equal: L = sqrt(d² - r²), where d is the distance between centers.

Wait, in the horizontal case: centers (0,0) and (2r,0), distance d = 2r, so L = sqrt(4r² - r²) = r√3. But earlier, we thought the tangent segment was 2r, but that was the horizontal tangent between the two circles, which is actually the internal tangent? No, wait, for centers (0,0) and (2r,0), radius r each:

- The line y = r is tangent to both circles at (0,r) and (2r,r), distance from center to line is r, which is radius, so it's an external tangent.

- The length of this tangent segment is sqrt( (2r - 0)² + (r - r)² ) = 2r, but according to the formula L = sqrt(d² - (r - r)²) = 2r, which matches, but wait, how does this relate to the rectangle?

In the rectangle formed by O1(0,0), P(0,r), Q(2r,r), O3(2r,0), we have sides OP = r, PQ = 2r, O3Q = r, so it's a rectangle with sides r and 2r, diagonal O1O3 = sqrt(r² + (2r)²) = r√5, but O1O3 is 2r, so this isn't a rectangle. Wait, no—the rectangle should have sides equal to the radii and the tangent segment length.

Wait, let's define the external tangent segment between two circles:

- It is a line segment that is tangent to both circles, not crossing between them.

- For circles with radii r1, r2, the length L of the external tangent is sqrt(d² - (r1 - r2)²), where d is the distance between centers.

Yes, this is a standard formula. Let's verify with a simple case:

- Two circles, same radius r, centers 2r apart: d = 2r, so L = sqrt(4r² - 0) = 2r. For example, centers at (0,0) and (2r,0), radius r: the external tangents are the two lines y = r and y = -r, each tangent at (0,r), (2r,r) and (0,-r), (2r,-r), so length of each tangent segment is 2r, correct.

- Two circles, radius r, centers 3r apart: L = sqrt(9r² - 0) = 3r. Centers at (0,0) and (3r,0), radius r: tangent segment y = r, from (0,r) to (3r,r), length 3r, correct.

- Two circles, radii r and R, centers 2r apart, external tangent: L = sqrt(4r² - (r - R)²). If R = 2r, d = 2r, L = sqrt(4r² - r²) = r√3, which makes sense.

Okay, so the formula is correct: L = sqrt(d² - (r1 - r2)²) for external tangent length.

In our problem, all three circles have radius r = 10 cm, so r1 = r2 = r. The distance between centers of any two circles is equal to r + r = 2r = 20 cm (since they are mutually tangent).

Therefore, the length of each straight segment of the belt (external tangent between two adjacent circles) is L = sqrt( (2r)² - (r - r)² ) = sqrt(4r²) = 2r = 20 cm.

Wait, but in the horizontal case, we had two circles with centers 2r apart, radius r each, the external tangent segment length was 2r, which matches this formula. So for each pair of circles, the straight segment between them is 2r = 20 cm.

Now, how many straight segments are there? Three straight segments, connecting each pair of adjacent circles (since it's a closed loop around three circles), so total straight segment length is 3 * 20 = 60 cm.

Now, the arc segments: for each circle, there is an arc length that is part of the belt. How much of the circle is covered by the belt?

For a single circle, the belt is tangent to it at two points, and the arc between those two points is the part of the belt that wraps around the circle. To find the central angle corresponding to this arc, consider the angle between the two radii to the tangent points.

For circle A, the two tangent points are on the straight segments connecting to circles B and C. Since the radii to the tangent points are perpendicular to the straight segments, the angle between the two radii is equal to the angle between the two straight segments.

The two straight segments meeting at circle A are S_AB (tangent to A and B) and S_AC (tangent to A and C). The angle between S_AB and S_AC at the tangent point on circle A is equal to the angle of the triangle formed by the centers.

Wait, no—consider the directions of the straight segments. The straight segment S_AB is tangent to circle A at T_AB, so the direction of S_AB is perpendicular to the radius AT_AB. Similarly, S_AC is perpendicular to AT_AC.

Therefore, the angle between S_AB and S_AC is equal to 180° - the angle between AT_AB and AT_AC.

Now, what is the angle between S_AB and S_AC? Let's consider the triangle formed by the centers O_A, O_B, O_C. It's equilateral, so each angle is 60°. The straight segments S_AB and S_AC are external tangents to the circles, so the angle between S_AB and S_AC can be found by considering the angles of the tangent lines.

For two circles, the angle between the external tangent segments is related to the angle between the centers.

Wait, here's a better way: for each circle, the two radii to the tangent points form an angle that is equal to 360° minus the sum of the angles between the center-to-center lines.

Wait, let's use the fact that for the belt to be tight, the path of the belt should "turn" such that the total angle turned is 360°, but since it's going around three circles, the sum of the angles of the arcs should correspond to the total angle around the center of the belt.

Wait, another method: draw the lines from each center to the points where the belt is tangent to the circle. For each circle, these lines (the radii to the tangent points) are perpendicular to the corresponding straight segments.

Now, consider the three radii vectors: for circle A, r_A1 and r_A2 (to tangent points from B and C), for circle B, r_B1 and r_B2 (to tangent points from A and C), etc.

Now, consider the polygon formed by the outer vertices of the tangent segments and the centers. Wait, maybe consider the triangle formed by the three points of tangency on the circles, but it's messy.

Wait, let's take a specific example with r = 1, so we can compute numerically.

Centers at (0,0), (2,0), (1,√3). Circles of radius 1.

Straight segment between (0,0) and (2,0) (bottom left and bottom right): external tangent at y=1, tangent points (0,1) and (2,1), length 2.

Straight segment between (0,0) and (1,√3): centers 2 apart, radius 1 each, external tangent length L = sqrt(4 - 0) = 2.

Wait, let's find the tangent points for the top circle.

Top circle center (1,√3), radius 1.

Let's find the tangent segment between (0,0) and (1,√3), which should be the left tangent segment.

The external tangent will be the one that doesn't cross the triangle.

Using the formula, the direction of the tangent line can be found by the fact that it's parallel to the vector from (0,0) to (1,√3) rotated by 90°, but for equal radii, the tangent line is parallel to the line connecting the centers if the radii are equal? No, in the horizontal case, the tangent line was horizontal, centers horizontal, but the radii were vertical.

Wait, for centers (0,0) and (1,√3), the vector between them is (1,√3), length 2.

The external tangent lines will be such that the radii to the tangent points are perpendicular to the tangent line, and parallel to each other.

Let the tangent line have slope m, so equation y = mx + c.

Distance from (0,0) to line: |c| / sqrt(m² + 1) = 1 ⇒ c² = m² + 1.

Distance from (1,√3) to line: |m + √3 - c| / sqrt(m² + 1) = 1 ⇒ (m + √3 - c)² = m² + 1.

Expand the second equation: m² + 2m√3 + 3 - 2mc - 2√3 c + c² = m² + 1 ⇒ 2m√3 + 3 - 2c(m + √3) + c² = 1.

But c² = m² + 1, so substitute:

2m√3 + 3 - 2c(m + √3) + m² + 1 = 1 ⇒ 2m√3 + m² + 3 - 2c(m + √3) = 0 ⇒ 2c(m + √3) = m² + 2m√3 + 3 = (m + √3)².

Therefore, 2c = m + √3 (assuming m + √3 ≠ 0, otherwise we get c = 0, which is the x-axis, not tangent).

So c = (m + √3)/2.

But c² = m² + 1, so:

(m + √3)² / 4 = m² + 1 ⇒ m² + 2m√3 + 3 = 4m² + 4 ⇒ 3m² - 2m√3 + 1 = 0 ⇒ discriminant = 12 - 12 = 0 ⇒ m = (2√3)/6 = √3/3.

So the tangent line is y = (√3/3)x + ( (√3/3) + √3 )/2 = (√3/3)x + (4√3/3)/2 = (√3/3)x + 2√3/3.

Now, find the tangent point on circle (0,0): substitute into x² + y² = 1:

x² + ( (√3/3)x + 2√3/3 )² = 1 ⇒ x² + (3/9)x² + (4*3/9)x + 12/9 = 1 ⇒ x² + (1/3)x² + (4/3)x + 4/3 = 1 ⇒ (4/3)x² + (4/3)x + 1/3 = 0 ⇒ 4x² + 4x + 1 = 0 ⇒ (2x + 1)² = 0 ⇒ x = -1/2.

So y = (√3/3)(-1/2) + 2√3/3 = (-√3/6 + 4√3/6) = 3√3/6 = √3/2.

Thus, tangent point on circle (0,0) is (-1/2, √3/2), which is 60° from the positive x-axis, as expected (since (x, y) = (cos 60°, sin 60°) = (1/2, √3/2), but we have (-1/2, √3/2), which is 120°).

Similarly, find tangent point on circle (1,√3): (x - 1)² + (y - √3)² = 1.

Substitute y = (√3/3)x + 2√3/3:

(x - 1)² + ( (√3/3)x + 2√3/3 - 3√3/3 )² = 1 ⇒ (x - 1)² + ( (√3/3)x - √3/3 )² = 1 ⇒ (x - 1)² + (3/9)(x - 1)² = 1 ⇒ (x - 1)² + (1/3)(x - 1)² = 1 ⇒ (4/3)(x - 1)² = 1 ⇒ (x - 1)² = 3/4 ⇒ x - 1 = ±√3/2 ⇒ x = 1 ± √3/2.

Take the other tangent point (not the one for the bottom), but since we want the external tangent for the belt (the one on the side away from the center), let's take x = 1 - √3/2 (left side).

y = (√3/3)(1 - √3/2) + 2√3/3 = √3/3 - (3/6) + 2√3/3 = √3/3 + √3/3 - 1/2 = 2√3/3 - 1/2.

Wait, but maybe better to use the fact that the tangent point on circle (1,√3) is (1 + cos θ, √3 + sin θ), and the tangent line has slope √3/3, so the radius to the tangent point has slope -√3 (negative reciprocal), so (y - √3) / (x - 1) = -√3 ⇒ y = -√3 x + √3 + √3 = -√3 x + 2√3.

Substitute into tangent line equation y = (√3/3)x + 2√3/3:

-√3 x + 2√3 = (√3/3)x + 2√3/3 ⇒ multiply both sides by 3/√3: -3x + 6 = x + 2 ⇒ -4x = -4 ⇒ x = 1.

Then y = -√3 + 2√3 = √3.

Wait, that's the center of the top circle, which can't be. I'm making a mistake here.

Wait, we know the radius to the tangent point is perpendicular to the tangent line, so slope of radius is negative reciprocal of tangent line slope. Tangent line slope m = √3/3, so radius slope = -√3.

For circle (0,0), radius to tangent point has slope -√3, so tangent point is (cos θ, sin θ) where tan θ = -√3 ⇒ θ = 120° (since it's the left side), so (cos 120°, sin 120°) = (-1/2, √3/2), which matches our earlier calculation.

For circle (1,√3), the radius to the tangent point must also have slope -√3 (since both radii are perpendicular to the same tangent line), so the vector from (1,√3) to the tangent point is (k, -√3 k) for some k, and length 1: k² + (3k²) = 1 ⇒ 4k² = 1 ⇒ k = ±1/2.

Take k = 1/2: tangent point = (1 + 1/2, √3 - √3/2) = (3/2, √3/2)

Take k = -1/2: tangent point = (1 - 1/2, √3 + √3/2) = (1/2, 3√3/2)

Now, check if these points are on the tangent line y = (√3/3)x + 2√3/3.

For (3/2, √3/2): RHS = (√3/3)(3/2) + 2√3/3 = √3/2 + 2√3/3 = (3√3 + 4√3)/6 = 7√3/6 ≈ 2.02, LHS = √3/2 ≈ 0.866, not equal.

For (1/2, 3√3/2): RHS = (√3/3)(1/2) + 2√3/3 = √3/6 + 4√3/6 = 5√3/6 ≈ 1.44, LHS = 3√3/2 ≈ 2.598, not equal.

Wait, no—slope of radius is negative reciprocal of tangent line slope, so tangent line slope m, radius slope is -1/m. Tangent line slope m = √3/3, so radius slope = -√3, correct.

So for circle (0,0), radius slope -√3, so direction vector (1, -√3), but length should be 1, so unit vector (1/2, -√3/2), so tangent point = (1/2, -√3/2), but that's in the bottom left quadrant.

Wait, no—unit vector in direction of radius is (cos φ, sin φ), and slope = sin φ / cos φ = tan φ = -√3, so φ = 120° or 300°, so cos φ = -1/2, sin φ = √3/2 (120°), so tangent point = (-1/2, √3/2), which is in the upper left quadrant, correct.

For circle (1,√3), radius slope = -√3, so the direction vector from center to tangent point has slope -√3, so (x - 1, y - √3) = (t, -√3 t) for some t, length 1: t² + 3t² = 1 ⇒ t = ±1/2.

So tangent point = (1 ± 1/2, √3 ∓ √3/2) = (3/2, √3/2) or (1/2, 3√3/2).

Now, check which one is on the tangent line.

Tangent line equation: we had from the distance formula, but let's use the fact that the tangent line should pass through the tangent point.

For tangent point (3/2, √3/2) on circle (0,0): line from (0,0) to (3/2, √3/2) has slope (√3/2)/(3/2) = √3/3, which is the same as the tangent line slope? No, the radius to the tangent point should be perpendicular to the tangent line, so if the radius has slope √3/3, then the tangent line slope should be -3/√3 = -√3.

Ah! Here's the mistake: the slope of the radius is equal to the slope of the line from the center to the tangent point, and the slope of the tangent line is perpendicular to that, so slope of tangent line = -1 / (slope of radius).

We found slope of tangent line m = √3/3, so slope of radius should be -√3, which is correct.

So slope of radius = -√3, so for circle (0,0), radius slope = -√3 ⇒ (y - 0)/(x - 0) = -√3 ⇒ y = -√3 x.

Tangent point on circle (0,0) is intersection of y = -√3 x and x² + y² = 1 ⇒ x² + 3x² = 1 ⇒ 4x² = 1 ⇒ x = ±1/2.

Take x = -1/2, y = √3/2 (upper left), which has slope (√3/2)/(-1/2) = -√3, correct.

For circle (1,√3), radius slope = -√3 ⇒ (y - √3)/(x - 1) = -√3 ⇒ y = -√3(x - 1) + √3 = -√3 x + 2√3.

Intersection with circle (x - 1)² + (y - √3)² = 1: substitute y = -√3 x + 2√3:

(x - 1)² + (-√3 x + 2√3 - √3)² = 1 ⇒ (x - 1)² + (-√3 x + √3)² = 1 ⇒ (x - 1)² + 3(x - 1)² = 1 ⇒ 4(x - 1)² = 1 ⇒ (x - 1)² = 1/4 ⇒ x = 1 ± 1/2 ⇒ x = 3/2 or 1/2.

Take x = 1/2 (left side, away from the center of the triangle), then y = -√3(1/2) + 2√3 = 3√3/2.

So tangent point on circle (1,√3) is (1/2, 3√3/2).

Now, check if these two tangent points (on circles (0,0) and (1,√3)) are on the same tangent line.

Line through (-1/2, √3/2) and (1/2, 3√3/2): slope = (3√3/2 - √3/2)/(1/2 - (-1/2)) = (2√3/2)/(1) = √3.

Wait, but earlier we calculated slope m = √3/3, but here the slope is √3. Which one is correct?

Ah, no—we found the tangent line by solving for the distance, but let's use the correct method for external tangent.

For two circles, centers O1, O2, radii r1, r2, the external tangent lines can be found by moving from O1 in the direction of O2 by r1, and from O2 in the direction of O1 by r2, then the line connecting those points is the external tangent.

Wait, for equal radii, the external tangent lines are parallel to the line connecting the centers if the radii are equal? No, they are parallel to each other, but not necessarily to the center line.



## B6 · steps 554–718 · DERIVED_RELATIONS · 6830 tokens

Wait, let's use the fact that for three circles of radius r, mutually tangent, the belt length is given by 6r + 2πr.

Wait, no, let's think about the angles for the arcs.

At each circle, the two tangent lines meet the circle at two points, and the angle between the two tangent lines is equal to the angle of the triangle at that vertex.

In the equilateral triangle, each angle is 60°, so the angle between the two tangent lines at the circle is 60°.

Wait, no—actually, for the belt, the angle between the two tangent segments at the circle is equal to 180° minus the angle of the triangle.

Wait, here's a concrete way:

Draw the three centers as vertices of an equilateral triangle. For each circle, draw the two radii to the tangent points. Since the radii are perpendicular to the tangent segments, the angle between the two radii is equal to the angle between the two tangent segments.

Now, the three tangent segments form a triangle similar to the triangle formed by the centers, because the radii are parallel to each other.

Wait, the distance between the centers is 2r, and the distance between the tangent points is the length of the tangent segment, which we know from the rectangle formula is L = sqrt( (2r)² - r² ) = r√3 (wait, earlier we had for two circles with centers distance d, radii r, external tangent length sqrt(d² - (r - r)²) = d, but if d = 2r, then L = 2r, which is a square).

Wait, I think I need to look for the angle of the arc.

For each circle, the belt wraps around a portion of the circle, and the amount of the circle that's covered is 360° minus the angle that's facing the center of the triangle.

In the equilateral triangle, each internal angle is 60°, so the angle at each vertex facing the triangle is 60°.

Now, consider the tangent segments: at each circle, the two tangent segments are "outside" the triangle, so the angle between the tangent segments at the circle is equal to 180° minus the internal angle of the triangle? Wait, for a triangle, the sum of the external angles is 360°, but this is a different angle.

Wait, let's consider the triangle formed by the three tangent points on the circles. For three mutually tangent circles, the triangle formed by the tangent points is also equilateral, and the belt forms a triangle around it with the arcs.

Wait, here's a breakthrough: when you have a belt around three circles, the length of the belt is equal to the perimeter of the triangle formed by the centers plus the length of the arcs that are not covered by the triangle.

For each circle, the part of the circle not covered by the triangle is an arc, and the central angle for this arc is equal to 360° minus the angle of the triangle at that vertex.

Wait, no—actually, the angle subtended by the arc on the circle is equal to 60° (the angle of the triangle), so the arc length is (60°/360°)*2πr = (1/6)*2πr = πr/3.

Wait, no—let's count the angles. Suppose we go around the belt: at each circle, the belt turns by an angle, and the total turn should be 360°.

For the belt, as it goes around the three circles, at each circle, the direction of the belt changes by 180° - θ, where θ is the angle between the radii to the tangent points.

Wait, no—if you walk along the belt, at each tangent point, the direction changes by the angle of the tangent, but maybe think about the angle between the two straight segments meeting at a circle.

For example, at circle A, the straight segment S_AB and S_AC meet at the tangent point on A, and the angle between S_AB and S_AC is equal to the angle of the triangle formed by the centers.

Wait, let's take the horizontal bottom circle: centers B and C at (-10,0) and (10,0), radius 10. The tangent segment between them is the top tangent segment, from (-10,10) to (10,10), which is horizontal. Now, the belt goes up to the top circle A at (0, 10√3). The left tangent segment from A to B should be a line that connects (-10,10) to some point on A.

Wait, circle A has center (0, 10√3), radius 10, so it goes from y = 10√3 - 10 ≈ 17.32 - 10 = 7.32 to y = 10√3 + 10 ≈ 27.32.

The left tangent segment from B(-10,0) to A(0,10√3): we found the tangent point on A was (-5, 5√3) earlier, which is at y = 5*1.732 ≈ 8.66, which is between 7.32 and 27.32, correct.

The tangent point on B for the left segment is at (-5, 5√3) as well? No, for circle B, center (-10,0), radius 10, tangent point at (-5, 5√3): distance from B to point is sqrt( (-5 + 10)^2 + (5√3 - 0)^2 ) = sqrt(25 + 75) = 10, correct.

So the left tangent segment is from (-5, 5√3) on B to (-5, 5√3) on A? No, that's the same point, which is the point of tangency between A and B.

Ah! Here's the key realization: when the three circles are mutually tangent, the belt around them that is tight does not cross the regions between the circles, so the belt is composed of three straight segments, each tangent to two adjacent circles (not at their point of tangency), and three curved segments, one on each circle, between the tangent points.

For three circles of radius r, centers at vertices of equilateral triangle with side 2r, the length of each straight segment is 2r (for equal radii, external tangent length is distance between centers, which is 2r).

Now, the arc on each circle: the central angle for the arc is equal to 360° minus the angle of the triangle formed by the centers at that vertex.

Wait, no—consider the angle between the two radii to the tangent points. For circle A, the two radii to the tangent points from B and C are each perpendicular to the straight segments. The straight segments form a triangle with the centers, and the angle between the straight segments can be found by the fact that the triangle formed by the centers has angles 60°.

In the equilateral triangle of centers, each angle is 60°. The angle between the two straight segments (tangent segments) is equal to the supplement of the 60° angle, because the radii are perpendicular to the segments.

Wait, let's use the direction vectors. The vector from center A to center B is AB, and the vector from center A to center C is AC. The angle between AB and AC is 60°.

The radius to the tangent point on B for segment AB is perpendicular to AB (since the radius is perpendicular to the tangent segment), so the angle between the radius and AB is 90°.

Similarly, the radius to the tangent point on C for segment AC is perpendicular to AC, so the angle between the radius and AC is 90°.

Therefore, the angle between the two radii (at A) is equal to the angle between the center-to-center vectors minus the angles of 90° from each, but since the radii are on the opposite side of the center-to-center lines, the angle between the radii is equal to the angle of the triangle plus the two 90° angles? No.

Wait, if you have two lines (AB and AC) meeting at A at 60°, and from A, you draw two lines (radii) that are each 90° from AB and AC respectively, then the angle between the two radii is equal to 360° - 60° - 90° - 90° = 120°.

Yes! That makes sense. At point A, the two center-to-center lines AB and AC form a 60° angle. From each center-to-center line, the radius is drawn perpendicular to the tangent segment, which is 90° from the center-to-center line. Since the belt is on the outside, the radii are drawn on the side opposite to the triangle, so the angle between the two radii is 360° minus the angle between the center-to-center lines minus the two 90° angles (one on each side).

Wait, in terms of the directions:

- AB is a line from A to B.

- The tangent segment S_AB is tangent to circle A at T_AB, so AT_AB is perpendicular to S_AB.

- S_AB is also tangent to circle B, so BT_AB is perpendicular to S_AB.

- Therefore, AT_AB is parallel to BT_AB, as both are perpendicular to S_AB.

- The angle between AB and AT_AB is equal to the angle between AB and BT_AB, because of the rectangle formed by A, B, T_AB, and the point where the radii meet (but actually, it's a rectangle, so the angles are 90°).

Wait, in the rectangle O_A T_AB T_B O_B, the angles at T_AB and T_B are 90°, so the angles at O_A and O_B are also 90°. Therefore, the angle between O_A O_B and O_A T_AB is 90°.

Similarly, the angle between O_A O_C and O_A T_AC is 90°.

Now, the angle between O_A O_B and O_A O_C is 60° (the angle at A in the equilateral triangle).

Therefore, the angle between O_A T_AB and O_A T_AC is equal to 360° - (90° + 90° + 60°) = 120°.

Yes! That's it.

Let's visualize it:

- At center A, the two center-to-center lines to B and C form a 60° angle between them.

- The radius to the tangent point from B (AT_AB) forms a 90° angle with the center-to-center line AB.

- Similarly, the radius to the tangent point from C (AT_AC) forms a 90° angle with the center-to-center line AC.

- Since the belt is outside the triangle, the radii AT_AB and AT_AC are on the "outside" of the 60° angle between AB and AC.

- Therefore, the angle between the radii AT_AB and AT_AC is the angle that is on the outside of the 60° angle plus the two 90° angles.

- The total angle around point A is 360°, so the angle between the radii is 360° - (60° + 90° + 90°) = 120°.

Yes, that makes sense: the two radii are perpendicular to the straight segments, which are part of the belt, so the angle between the radii is the angle we need for the arc length.

Since the belt is going around the outside, the arc on the circle is the arc that is opposite to the angle between the radii, which is the minor arc or major arc? Wait, the central angle we calculated (120°) is the angle between the two radii to the tangent points, and the arc on the belt is the one that is "bent" by the belt, which should be the arc corresponding to this central angle.

Wait, no—actually, the belt is the outer path, so for each circle, the arc that is part of the belt is the one that is not facing towards the center of the triangle, so it's the major arc if the central angle is the minor arc.

Wait, the central angle between the two radii is 120°, which is less than 180°, so it's the minor arc. But the belt is going around the outside, so it should be the major arc, right?

Wait, let's think of a simple case: two circles, radius r, centers distance 2r apart. The belt around them: the straight segments are the two external tangents, each of length 2r (wait, no, for two circles, the belt has two straight segments and two arcs, but for two circles, the belt length is 2*2r + πr + πr = 4r + 2πr? No, for two circles, the length of the external belt is 2*sqrt(d² - 0) + (r + r)π = 2d + 2πr, but for d = 2r, that's 4r + 2πr.

Wait, no—for two circles of radius r, centers distance d apart, the external belt length is 2*L + (2πr - 2*αr), where α is the angle of the triangle.

But for three circles, each circle has a central angle for the arc that is 120°, so the arc length per circle is (120°/360°)*2πr = (1/3)*2πr = (2πr)/3.

Wait, 120° is 1/3 of 360°, so arc length per circle is 2πr/3.

Then total arc length for three circles is 3*(2πr/3) = 2πr.

Wait, but let's verify the central angle.

At each circle, the angle between the two radii to the tangent points is 120°, so the arc on the belt is the major arc or minor arc?

If the central angle is 120°, the minor arc is 120°, major arc is 240°.

Now, when the belt goes around the outside, it should not cover the part of the circle that's facing towards the center of the triangle. The angle facing the center is the angle between the two radii to the tangent points, which we calculated as 120°, so the arc on the belt is the remaining part of the circle, which is 360° - 120° = 240°.

Ah! That's the key. The angle between the two radii to the tangent points is the angle of the "notches" of the belt on the circle, so the arc on the belt is the complement of that angle.

Let's confirm with the equilateral triangle:

- The internal angle at each vertex of the triangle (between the two sides) is 60°.

- This internal angle is the angle between the two center-to-center lines, which is also the angle facing the center of the triangle.

- The radii to the tangent points are perpendicular to the straight segments, so the angle between the radii is the angle that the belt uses, which is 360° - (internal angle + two right angles) = 360° - (60° + 90° + 90°) = 120°.

- But wait, the arc on the belt is the part that's not facing the center, so it should be the angle that is not covered by the "gap" towards the center.

- The gap towards the center is the angle between the two radii, which is 120°, so the arc on the belt is 360° - 120° = 240°.

Yes, that makes sense. For example, if you have a circle and a triangle inside it, the belt wraps around the outside, so the arc length is the circumference minus the arc that's covered by the triangle.

In this case, the triangle formed by the centers is equilateral, and the angle at each center facing the triangle is 60°, but wait, no—the angle between the two radii is 120°, so the arc facing the triangle is 120°, hence the belt arc is 240°.

Let's take a step back with the coordinate example where we have two circles and a triangle.

Centers at A(0, 0), B(20, 0), C(10, 10√3). Circle A: radius 10, circle B: radius 10, circle C: radius 10.

The tangent segment between A and B: let's find the two tangent points.

Using the formula, the external tangent segment length L = sqrt(d² - (r - r)²) = 20.

For circle A, the two tangent points for the belt: one from A to B, one from A to C.

The angle between the two radii to these tangent points: let's calculate the angle between the vectors.

The vector from A to B is (20, 0), vector from A to C is (10, 10√3).

The angle between AB and AC is 60°, as it's an equilateral triangle.

The radius to the tangent point on A from B is perpendicular to the tangent segment, and the tangent segment is the external tangent, so the angle between AB and the radius to the tangent point is 90°.

Similarly for AC.

Since the belt is outside the triangle, the radii are on the side opposite to the triangle, so the angle between the two radii is 60° (internal angle of the triangle) + 90° (from AB) + 90° (from AC) = 240°? No, that's more than 360°.

Wait, using the right triangle formed by the centers and tangent points:

For circles A and B, centers 20 apart, radius 10 each. The external tangent segment is length L = 20 (from formula).

The radius to the tangent point on A is perpendicular to the tangent segment, so the angle between the center-to-center line AB and the radius to the tangent point is 90°? Wait, no—in the rectangle O_A T_AB T_B O_B, the angles are 90°, so the angle between O_A O_B and O_A T_AB is 90°.

Similarly, for circles A and C, the angle between O_A O_C and O_A T_AC is 90°.

Now, the angle between O_A O_B and O_A O_C is 60°.

Therefore, the angle between O_A T_AB and O_A T_AC is equal to 360° - (angle between O_A O_B and O_A O_C) - (angle between O_A O_B and O_A T_AB) - (angle between O_A O_C and O_A T_AC) = 360° - 60° - 90° - 90° = 120°.

Yes, this is the angle between the two radii, which is the central angle for the arc between the two tangent points on circle A.

Now, is this the arc that is part of the belt or the opposite arc?

Since the belt is the outer path, and the radii are on the "outside" of the triangle, the arc between the two tangent points that is on the outside is the larger arc, which is 360° - 120° = 240°.

Yes, because if you have two points on a circle, the two arcs between them are the minor and major arcs. The minor arc is 120°, major arc is 240°. The belt going around the outside of the triangle should follow the major arc, which is the longer path around the circle.

Let's verify with a simple case: if you have a circle and a very small angle at the center, the belt would follow the major arc. If the angle between the radii is 180°, the belt would follow the semicircle.

In our case, the angle between the radii is 120°, so the arc on the belt is 240°, which is 240° * (π/180°) = (4π/3) radians.

Therefore, the arc length per circle is r * (4π/3) = 10 * (4π/3) = (40π)/3 cm.

Wait, no—wait, the central angle is in radians, so 240° = (240/180)π = (4/3)π radians.

Yes, so arc length = r * θ = 10 * (4π/3) = 40π/3 cm per circle.

Three circles, so total arc length = 3 * (40π/3) = 40π cm.

Wait, but let's check if the central angle is actually 120° or 240°.

Take the top circle: center at (0, 10√3), radius 10.

Tangent point from left circle B: we found earlier using coordinates that the tangent point on circle A from B is at (-5, 5√3), but wait, no—when we calculated the tangent line for circle A and B, we got the same point for both circles, which was the point of tangency between A and B, but that's the internal tangent, not the external tangent.

Wait, no—there are two external tangents: one above the line AB, one below. The one above the line AB would be the one we need for the outer belt.

Let's find the tangent points for the top circle A.

Circle A: center (0, 10√3), radius 10.

Circle B: center (-10, 0), radius 10.

The upper external tangent: since the circles are tangent at (-5, 5√3), the upper external tangent should be above that point.

The tangent points on circle A for the upper external tangent would be at the top of the circle, but no, the tangent segment should be on the "outside".

Wait, let's use the angle of the tangent.

The angle between the tangent segments at each circle is equal to the angle of the triangle formed by the centers.

The triangle formed by the centers is equilateral with 60° angles.

The belt goes around the outside, so at each circle, the angle between the two straight segments is equal to 180° - 60° = 120°.

Wait, yes! The angle between the two straight segments meeting at a circle is equal to the supplement of the angle at the center of the triangle.

For the equilateral triangle, each angle is 60°, so the angle between the straight segments at the circle is 120°.

Now, the angle between the two straight segments at the circle is equal to the angle between the tangent lines at the circle, which is equal to the angle between the radii.

Wait, the tangent lines are the straight segments, so the angle between the two straight segments at the circle is the angle of the belt's turn at that circle.

For a circle, if two tangent lines meet at a point on the circle (but they're tangent at two points, so the angle between the two tangent lines is the angle between the two tangent points).

The angle between the two tangent lines (straight segments) at the circle is equal to the angle of the triangle formed by the centers.

No, let's use the fact that for any two tangent lines to a circle, the angle between them is equal to the central angle between the points of tangency.

Yes! For a circle, the measure of the angle formed by two tangent lines to the circle is equal to 180° minus the measure of the central angle between the points of tangency.

Wait, no—if the central angle is θ, then the angle between the tangent lines is 180° - θ.

Let's verify: if the central angle is 0° (same point), angle between tangents is 180° (they coincide), 180° - 0° = 180°, correct.

If central angle is 180° (diametrically opposite), angle between tangents is 90°, 180° - 180° = 0°, wrong.

Wait, actually, the angle between the tangent lines is equal to half the difference of the intercepted arcs, but since it's two tangent lines, it's equal to 180° minus the central angle.

Wait, no—consider a circle with center O, and two tangent lines meeting at point P outside the circle. The angle at P between the tangents is equal to half the difference of the measures of the intercepted arcs, which is half of (360° - θ), where θ is the central angle between the points of tangency.

So angle at P = (360° - θ)/2 = 180° - θ/2.

Ah, yes! That's the correct formula.

In our case, the point where the two straight segments meet (on the belt) is not an external point outside the circle, but rather the belt is a closed loop, so the two straight segments are tangent to the circle at two points, and they meet at the center of the belt? No, the straight segments are tangent to the circle at two points, so the angle between the two straight segments at those points is not the angle at a point on the circle, but the angle at the circle is the central angle between the tangent points.

Wait, let's get back to basics for one circle.

- Circle with center O, radius r.

- Two tangent lines to the circle: one tangent at point P, the other at point Q.

- The angle between the tangent lines at the circle (i.e., the angle at P and Q) is the angle between OP and OQ, which is the central angle θ.

- The measure of the angle between the two tangent lines (the angle formed by the lines at the intersection point outside the circle) is equal to 180° - θ/2.

But in our problem, the two straight segments (tangent lines) are not meeting at a point outside the circle—they are meeting at the tangent points on the circle. Wait, no—each straight segment is tangent to one circle at one point, so for circle A, the straight segment S_AB is tangent to circle A at point T_AB, and the straight segment S_AC is tangent to circle A at point T_AC. Therefore, the two tangent lines are S_AB and S_AC, which are two lines, each tangent to circle A at T_AB and T_AC, respectively.

The angle between S_AB and S_AC at the intersection of these two lines (which is not at the circle, but at a point outside the circle) is equal to the angle between the two tangent lines.

But we want the angle between the two radii OP and OQ (P = T_AB, Q = T_AC), which is the central angle θ.

The angle between the tangent lines is equal to 180° - θ/2, but we need the central angle θ.

Now, where do these two tangent lines (S_AB and S_AC) meet? They meet at the point where the belt turns, which is outside the three circles, but we can find the angle between them.

Since S_AB is tangent to circles A and B, and S_AC is tangent to circles A and C, the lines S_AB and S_AC form a triangle with the lines connecting the centers.

Specifically, the lines connecting the centers form the triangle ABC, and the tangent lines form a triangle similar to ABC.

For the external tangent, the triangle formed by the tangent points and the centers is a rectangle or a triangle with angles 90°.

Wait, let's use the fact that the distance from each center to the two tangent points is 90° from the tangent lines.

In the triangle formed by the three centers, each angle is 60°, and the angle between the tangent lines at the vertex of the triangle is equal to the angle of the triangle.

Wait, I found a reference in my mind: for three equal circles packed together, the length of the belt (external) is 6r + 2πr.

Wait, no, let's calculate it with r = 10.

Wait, another method: the total length of the belt is equal to the perimeter of the equilateral triangle formed by the centers plus the length of the arcs that are not covered by the triangle.

The perimeter of the triangle is 3*2r = 6r = 60 cm.

The length of the arcs: each circle has a portion that is covered by the belt, and the remaining portion is the arc. The portion covered by the triangle is the angle at the center, which for an equilateral triangle is 60°, so the arc covered by the belt is 360° - 60° = 300°, but wait, no.

Wait, when you have three circles, each circle is tangent to the other two, so the area inside the triangle formed by the centers is a sort of equilateral triangle, and the belt goes around the outside of the three circles, so the "indent" of the belt at each circle is the angle of the triangle.

The sum of the angles of the triangle is 180°, so the total arc length is 2πr * (1 - 180°/360°) = 2πr * (1/2) = πr, but that's not right.

Wait, no—the total angle of the belt around the three circles is 360°, but the belt is not enclosing the center, it's enclosing the circles, so the total angle for the arc length should be 360°.

Wait, here's a correct way:

For each circle, the angle of the arc that is part of the belt is equal to 60° (the angle of the triangle), so the total arc length is 3 * (60°/360°) * 2πr = 3 * (1/6) * 2πr = πr.

But wait, that contradicts our earlier angle calculation.

Wait, let's look up the standard solution for three equal circles with a belt around them.

Upon recalling, for three circles of radius r, mutually tangent, the length of the external belt is 6r + 2πr.

Wait, no—let's think about the straight segments.

Each straight segment is the external tangent between two circles, which for equal radii and centers distance 2r apart is 2r, as the external tangent length is sqrt((2r)^2 - (r - r)^2) = 2r. So three segments, 3*2r = 6r.

For the arc segments: each circle has an arc that is 60° (the angle of the triangle), so 60° per circle, 3*60° = 180°, so arc length = (180°/360°)*2πr = πr.

Wait, 6r + πr = 7r? But that can't be, let's check with r = 1.



## B7 · steps 719–835 · REPAIR_OR_RESOLUTION · 3704 tokens

Wait, no—when you have three circles, the belt around them has a "corner" at each circle, and the angle of the corner is 180° - 60° = 120°, so the arc length per circle is 120°, so 3*120° = 360°, arc length 2πr.

Ah! That's it.

The angle of the belt's turn at each circle is 120°, so the total angle around the belt is 3*120° = 360°, which makes sense.

Wait, for a polygon, the total angle is 360°, but here it's a belt, which is a curve.

The key is that for each circle, the central angle corresponding to the arc on the belt is 120°.

Wait, let's use the following logic:

The centers form an equilateral triangle with side length 2r.

The belt consists of three straight segments, each parallel to a side of the triangle (since they're external tangents to equal radii), and three curved segments, each with central angle equal to 60°.

Wait, no—each straight segment is parallel to the side of the triangle, and the length of the straight segment is equal to the side length of the triangle, which is 2r.

Now, the angle between two straight segments at a circle is equal to the angle of the triangle at that vertex, which is 60°.

For the belt, the angle between the two straight segments at the circle is 60°, so the arc on the belt is the remainder: 360° - 60° = 300°.

Wait, let's think about a single circle with two tangent lines meeting at an angle of 60°. The central angle between the tangent points is 120°, because the angle between the tangent lines is 60°, so the central angle is 180° - 60° = 120°.

Yes! If two tangent lines to a circle meet at an angle θ, then the central angle between the points of tangency is 180° - θ.

In our case, the angle between the two straight segments (tangent lines) at the vertex where they meet (the point where the belt turns) is equal to the angle of the triangle formed by the centers, which is 60°.

Therefore, the central angle between the two tangent points on the circle is 180° - 60° = 120°.

But wait, the angle between the tangent lines is not the angle at the circle, but the angle between the lines where they meet outside the circle.

Yes, the two tangent lines S_AB and S_AC meet at a point outside the three circles, say point P. The angle at P between S_AB and S_AC is equal to the angle of the triangle formed by the centers, which is 60°.

Then, the central angle θ for the arc on circle A is equal to 180° - (angle at P) = 180° - 60° = 120°.

Therefore, the arc length on circle A is r * θ = r * (120° * π/180°) = (2πr)/3.

Three circles, so total arc length = 3 * (2πr)/3 = 2πr.

Now, the straight segments: each straight segment is the external tangent between two circles, and the length of each straight segment is equal to the distance between the centers minus the length of the "indent" from the radius.

Wait, no—using the formula for the length of the external tangent between two circles with radii r, centers distance d apart: L = sqrt(d² - (r - r)²) = d.

For d = 2r, L = 2r.

Three straight segments, so total straight length = 3 * 2r = 6r.

Wait, but let's confirm with r = 1:

- Three circles, radius 1, centers at (0,0), (2,0), (1,√3).

- Straight segment between (0,0) and (2,0): length 2 (external tangent at y=1, from (0,1) to (2,1)).

- Straight segment between (0,0) and (1,√3): we calculated earlier using coordinates, but let's use the formula L = 2r = 2.

- Straight segment between (2,0) and (1,√3): same, length 2.

- Total straight length = 2 + 2 + 2 = 6.

- Total arc length: for each circle, central angle 120°, arc length 120° * (π/180°) * 1 = 2π/3 per circle, total 2π.

- Total belt length = 6 + 2π.

Ah! This makes sense. For r = 1, the belt length is 6 + 2π, which is 6*1 + 2π*1.

Wait, but in our problem, r = 10, so total belt length = 6*10 + 2π*10 = 60 + 20π.

Wait, but wait—earlier we thought the straight segments might be shorter, but the formula for external tangent length for equal radii is d, which is 2r, so that's correct.

But let's verify the central angle with r = 1.

For circle at (0,0), the two tangent points for the straight segments:

- One from the segment between (0,0) and (2,0): tangent point (0,1).

- One from the segment between (0,0) and (1,√3): let's find it.

The straight segment between (0,0) and (1,√3) has slope (√3 - 0)/(1 - 0) = √3, so equation y = √3 x.

The external tangent line is not the line connecting the centers, but the tangent line that's parallel to the tangent segment.

Wait, for two circles with centers (0,0) and (1,√3), radius 1 each, the external tangent line can be found by moving from each center by the radius in the direction perpendicular to the tangent.

The direction of the tangent line is such that the distance from each center to the line is 1.

The line y = √3 x - c has distance from (0,0) equal to | -c | / sqrt(3 + 1) = |c| / 2 = 1 ⇒ c = ±2.

Take c = 2, so line y = √3 x - 2. Distance from (1,√3) to line: |√3 - 2 - 2| / 2 = |√3 - 4| / 2 ≈ (4 - 1.732)/2 ≈ 1.134 > 1, not tangent.

Take c = -2, line y = √3 x + 2. Distance from (0,0) is 2/2 = 1, good. Distance from (1,√3) is |√3 + 2 - 2| / 2 = |√3| / 2 ≈ 0.866 < 1, not tangent.

Ah, right—external tangent for equal radii when d = 2r is when the tangent line is such that the radii are parallel and outward.

For circles at (0,0) and (1,√3), d = 2, r = 1, so external tangent length L = sqrt(d² - 0) = 2.

The tangent points: the line connecting the centers is of length 2, and the tangent segment is also length 2.

The tangent points on circle (0,0) and (1,√3) are each at a distance of 1 from the center, along the direction perpendicular to the tangent line.

The direction of the tangent line is such that the vector from center (0,0) to tangent point is perpendicular to the tangent line, and same for the other center.

The angle between the centers is 60°, so the angle between the radii to the tangent points is 60°, so the arc length on the circle is 60°.

Wait, this is confusing.

Wait, let's look at a known example: if you have two circles of radius r, centers distance d apart, the length of the external belt is 2L + 2rπ, where L = sqrt(d² - (r - r)²) = d.

But for three circles, it's different.

Wait, I found the correct method here: for three circles of radius r, centers forming an equilateral triangle with side 2r, the length of the belt around them is equal to the sum of the lengths of the three external tangent segments plus the sum of the three arcs that are not enclosed by the triangle.

Each external tangent segment has length 2r, so three segments: 6r.

For each circle, the arc that is not enclosed by the triangle is the arc that is opposite to the angle of the triangle at that vertex.

The angle of the triangle at each vertex is 60°, so the arc not enclosed is 360° - 60° = 300°.

Wait, no—each circle is touched by two tangent segments, and the angle between the tangent segments at the circle is 60°, so the arc on the belt is 360° - 60° = 300°.

For three circles, total arc length = 3 * (300° * π/180°) = 3 * (5π/3) = 5π? No, 300° is 5/3 of 360°, so 5πr/3 per circle, total 5πr.

But let's use the angle between the radii.

The angle between the radii to the tangent points on a circle is equal to the angle of the triangle at that vertex, which is 60°, so the arc length is 60° * πr/180° = πr/3 per circle, total πr.

Wait, I think the mistake is in the angle between the radii.

Here's a clear derivation:

For each circle, the two tangent points on the belt are such that the radii to these points are perpendicular to the straight segments.

The straight segments form a triangle with the center-to-center lines, and the angle between the straight segments is equal to 180° - 60° = 120°.

Since the radii are perpendicular to the straight segments, the angle between the radii is equal to the angle between the straight segments, which is 120°.

Yes! If two lines are perpendicular to two other lines, then the angle between the first two lines is equal to the angle between the second two lines.

So, the angle between the straight segments at the circle is equal to the angle between the radii to the tangent points.

The straight segments meet at a point where the angle is 120° (since the triangle formed by the centers has 60° angles, and the straight segments form a triangle similar to it with 120° angles).

Wait, for three circles, the straight segments form a larger equilateral triangle, and the angle at each vertex of the straight segments is 120°.

Yes! Because the centers form an equilateral triangle, the straight segments (external tangents) also form an equilateral triangle, but with side length equal to the distance between centers, which is 2r, but the angle at each vertex is 120°.

Wait, no—external tangents to equal circles form a triangle where the angle at each vertex is 120°.

Let's consider the three centers: ABC, equilateral triangle with 60° angles.

The external tangent between A and B is a line segment that is parallel to AB but offset by the radius.

The distance between the centers is 2r, and the offset is such that the tangent segment length is equal to the distance between centers, 2r.

The angle between the tangent segments at the point where they meet is 120°, because the angle of the tangent triangle is supplementary to the center triangle.

Yes! The tangent segments form a triangle similar to the center triangle, but with angles 120°.

Wait, the angle between two external tangents between two circles is 180° - 60° = 120°.

Therefore, the angle between the two straight segments at the circle is 120°.

Since the radii are perpendicular to the straight segments, the angle between the radii is equal to the angle between the straight segments, which is 120°.

Therefore, the central angle for the arc on the circle is 120°.

Thus, arc length per circle is (120/360)*2πr = (1/3)*2πr = 2πr/3.

Total arc length for three circles: 3*(2πr/3) = 2πr.

Straight segment length: for each pair of circles, the external tangent length is equal to the distance between centers, which is 2r (since for equal radii, L = d = 2r).

Three straight segments, so total straight length = 3*2r = 6r.

Therefore, total belt length = 6r + 2πr = r(6 + 2π).

Wait, but wait—let's check with r = 1:

- Three circles, radius 1, centers at (0,0), (2,0), (1,√3).

- Straight segment between (0,0) and (2,0): length 2.

- Straight segment between (0,0) and (1,√3): length 2.

- Straight segment between (2,0) and (1,√3): length 2.

- Total straight length: 6.

- Arc on each circle: central angle 120°, so arc length 120° * π/180° * 1 = 2π/3 per circle.

- Total arc length: 3*(2π/3) = 2π.

- Total belt length: 6 + 2π.

Yes, this makes sense.

But wait, why is the straight segment length equal to 2r?

Because for two circles of radius r, centers distance d apart, external tangent length L = sqrt(d² - (r - r)²) = d.

For d = 2r, L = 2r, correct.

Now, why is the central angle 120°?

Because the angle between the two radii to the tangent points is 120°.

Let's verify with the triangle of centers:

- The centers form an equilateral triangle ABC with angles 60°.

- The radii to the tangent points form a triangle where each angle is 120°, because the angle between the radius and the center-to-center line is 90°, so the angle between the radii is 60° + 90° + 90° - 360° = 120°.

Wait, no—using vectors:

- Vector AB = B - A.

- The radius to the tangent point on A from B is perpendicular to AB, so the angle between AB and the radius is 90°.

- Similarly, the radius to the tangent point on A from C is perpendicular to AC.

- The angle between AB and AC is 60°.

- Therefore, the angle between the two radii is 60° + 90° + 90° - 360° = 120°.

Yes, because the two radii are on the outside of the 60° angle between AB and AC, so the total angle around A is 360°, and the angle between the radii is 360° - 60° - 90° - 90° = 120°.

This is the key. The angle between the two radii (the direction of the belt at the circle) is 120°, so the arc on the belt is the arc that is not between the radii, which is the major arc, but wait—no, the arc on the belt is the arc that is between the two tangent points, which is the arc corresponding to the central angle between the radii.

Since the central angle between the radii is 120°, the arc length is (120°/360°)*2πr = 2πr/3 per circle, total 2πr.

The straight segments are each length 2r, so three segments, 6r.

Total belt length = 6r + 2πr = 2r(3 + π).



## B8 · steps 836–956 · INTERMEDIATE_COMPUTATION · 3614 tokens

Wait, but wait—let's confirm with the coordinate system where the belt is drawn.

Take the bottom two circles: centers at (0,0) and (20,0), radius 10.

The top external tangent is at y = 10, tangent points (0,10) and (20,10), so the straight segment length is 20, which is 2r, correct.

Now, the top circle: center at (10, 10√3), radius 10.

The left tangent segment from the bottom left circle (0,0) to the top circle (10, 10√3) should be a line that is tangent to both circles.

Let's find the tangent point on the bottom left circle (0,0) for the left tangent segment.

The tangent line from (0,0) to (10, 10√3) is y = √3 x.

The external tangent line for the belt should be a line that is tangent to both circles and not crossing the triangle.

The condition for tangency: distance from (0,0) to line y = mx + c is 10, and distance from (10, 10√3) to line is 10.

So |c| / sqrt(m² + 1) = 10 and |10m + 10√3 - c| / sqrt(m² + 1) = 10.

Assuming the tangent line is above the line connecting the centers, which has slope √3, so the tangent line should have a slope less than √3 (for the upper external tangent).

From the equations:

c = 10 sqrt(m² + 1)

10m + 10√3 - c = ±10 sqrt(m² + 1)

Assuming the positive sign (upper tangent):

10m + 10√3 - 10 sqrt(m² + 1) = 10 sqrt(m² + 1)

10m + 10√3 = 20 sqrt(m² + 1)

m + √3 = 2 sqrt(m² + 1)

Square both sides:

m² + 2√3 m + 3 = 4m² + 4

0 = 3m² - 2√3 m + 1

Discriminant = 12 - 12 = 0 ⇒ m = (2√3)/6 = √3/3

So tangent line: y = (√3/3)x + c, c = 10 sqrt( (1/3) + 1 ) = 10 sqrt(4/3) = 20/√3 = (20√3)/3

Tangent point on circle (0,0): solve x² + y² = 100 with y = (√3/3)x + 20√3/3

x² + ( (1/3)x² + (40/3)x + 400/3 ) = 100

4x²/3 + 40x/3 + 400/3 = 300/3

4x² + 40x + 400 = 300

4x² + 40x + 100 = 0

x² + 10x + 25 = 0 ⇒ (x + 5)² = 0 ⇒ x = -5

y = (√3/3)(-5) + 20√3/3 = 15√3/3 = 5√3

So tangent point on circle (0,0) is (-5, 5√3).

Now, find the tangent point on the top circle (10, 10√3):

Circle equation: (x - 10)² + (y - 10√3)² = 100

Substitute y = (√3/3)x + 20√3/3:

(x - 10)² + ( (√3/3)x + 20√3/3 - 10√3 )² = 100

(x - 10)² + ( (√3/3)x + 10√3/3 )² = 100

(x - 10)² + ( √3/3 (x + 10) )² = 100

(x² - 20x + 100) + (3/9)(x² + 20x + 100) = 100

(x² - 20x + 100) + (1/3)(x² + 20x + 100) = 100

Multiply by 3: 3x² - 60x + 300 + x² + 20x + 100 = 300

4x² - 40x + 100 = 0

x² - 10x + 25 = 0 ⇒ (x - 5)² = 0 ⇒ x = 5

y = (√3/3)(5) + 20√3/3 = 25√3/3

So tangent point on top circle is (5, 25√3/3).

Now, let's find the arc on the top circle between these two tangent points.

First, find the center of the top circle: O(10, 10√3).

Tangent point on bottom left circle: T1(-5, 5√3)

Tangent point on bottom right circle: T2(15, 5√3) (by symmetry)

Wait, let's find the tangent point on the bottom right circle (20,0) to the top circle.

By symmetry, it should be (15, 5√3).

Distance from O to T2: sqrt( (15 - 10)^2 + (5√3 - 10√3)^2 ) = sqrt(25 + 75) = 10, correct.

Now, find the angle between vectors O to T1 and O to T2.

Vector OT1 = T1 - O = (-5 - 10, 5√3 - 10√3) = (-15, -5√3)

Vector OT2 = T2 - O = (15 - 10, 5√3 - 10√3) = (5, -5√3)

Now, compute the angle θ between OT1 and OT2 using dot product:

OT1 • OT2 = (-15)(5) + (-5√3)(-5√3) = -75 + 75 = 0

Oh! The dot product is zero, so the angle between OT1 and OT2 is 90°?

Wait, that can't be, but let's calculate the magnitudes:

|OT1| = 10, |OT2| = 10.

OT1 • OT2 = 0 ⇒ θ = 90°.

Wait, but we thought it was 120°. What's happening here?

Wait, we found the tangent points on the top circle from the left and right bottom circles, and the angle between the radii is 90°?

Wait, no—let's recalculate the tangent points.

Tangent point on bottom left circle (0,0) is (-5, 5√3), distance from (0,0) is 10, correct.

Tangent point on bottom right circle (20,0) should be (15, 5√3), distance from (20,0) is sqrt(5² + (5√3)²) = sqrt(25 + 75) = 10, correct.

Tangent point on top circle (10, 10√3) for the left tangent segment: we calculated (5, 25√3/3).

Distance from top circle center to (5, 25√3/3): sqrt( (5-10)^2 + (25√3/3 - 10√3)^2 ) = sqrt(25 + (25√3/3 - 30√3/3)^2) = sqrt(25 + (-5√3/3)^2) = sqrt(25 + 25/3) = sqrt(100/3) ≈ 5.77, not 10. That's a mistake in the calculation.

Wait, let's recalculate the tangent point on the top circle.

We had the tangent line: y = (√3/3)x + 20√3/3.

Circle equation: (x - 10)^2 + (y - 10√3)^2 = 100.

Substitute y:

(x - 10)^2 + ( (√3/3 x + 20√3/3) - 10√3 )^2 = 100

Simplify the y-term:

(√3/3 x + 20√3/3 - 30√3/3) = (√3/3 x - 10√3/3) = √3/3 (x - 10)

So the equation becomes:

(x - 10)^2 + [√3/3 (x - 10)]^2 = 100

(x - 10)^2 + (3/9)(x - 10)^2 = 100

(x - 10)^2 + (1/3)(x - 10)^2 = 100

(4/3)(x - 10)^2 = 100

(x - 10)^2 = 75

x - 10 = ±5√3

x = 10 ± 5√3

Ah, there we go, I made a mistake earlier.

So x = 10 + 5√3 or 10 - 5√3.

Take x = 10 - 5√3 (left side), then y = (√3/3)(10 - 5√3) + 20√3/3 = (10√3/3 - 5) + 20√3/3 = 10√3/3 + 20√3/3 - 5 = 10√3 - 5.

Wait, no:

(√3/3)(10 - 5√3) = 10√3/3 - 5

Then + 20√3/3 = 10√3/3 + 20√3/3 - 5 = 10√3 - 5.

So tangent point on top circle is (10 - 5√3, 10√3 - 5).

Now, distance from top center (10, 10√3) to this point:

sqrt( (-5√3)^2 + (-5)^2 ) = sqrt(75 + 25) = sqrt(100) = 10, correct.

Now, tangent point on bottom left circle (0,0): we had (-5, 5√3), distance from (0,0) is 10, correct.

Now, let's find the vector from top center to bottom left tangent point:

OT1 = (-5 - 10, 5√3 - 10√3) = (-15, -5√3)

Vector from top center to bottom right tangent point (by symmetry):

OT2 = (5√3 - 10, 10√3 - 5) = (-10 + 5√3, 10√3 - 5)

Wait, no, bottom right circle is at (20,0), so tangent point should be (20 - 5√3, 10√3 - 5), since it's symmetric to the left tangent point.

Distance from (20,0) to (20 - 5√3, 10√3 - 5): sqrt( (5√3)^2 + (10√3 - 5)^2 ) = sqrt(75 + 300 - 100√3 + 25) = wait, no, (x - 20) = -5√3, y - 0 = 10√3 - 5, so squared is 75 + 300 - 100√3 + 25? No, (10√3 - 5)^2 = 300 - 100√3 + 25 = 325 - 100√3, which is not 100. I think the symmetry is broken because the bottom circles are symmetric, but the tangent points should be symmetric with respect to the y-axis.

Top center at (10, 10√3), bottom left at (0,0), bottom right at (20,0), so symmetric over x=10.

Therefore, tangent point on bottom left circle is (a, b), tangent point on bottom right circle is (20 - a, b).

We found for bottom left circle: tangent point on the tangent segment is (-5, 5√3), so for bottom right circle, it should be (20 + 5, 5√3) = (25, 5√3), but wait, (25, 5√3) is outside the bottom right circle (radius 10, center (20,0): distance is sqrt(5² + (5√3)^2) = 10, correct.

Now, tangent point on top circle from bottom left: we found (10 - 5√3, 10√3 - 5).

Distance from top center (10, 10√3) to this point:

x: 10 - 5√3 - 10 = -5√3, y: 10√3 - 5 - 10√3 = -5, so distance sqrt( (5√3)^2 + 5^2 ) = sqrt(75 + 25) = 10, correct.

Tangent point on top circle from bottom right: by symmetry, (10 + 5√3, 10√3 - 5).

Now, let's find the angle between the two radii from the top circle to these two tangent points.

Vector OT1 = (10 - 5√3 - 10, 10√3 - 5 - 10√3) = (-5√3, -5)

Vector OT2 = (10 + 5√3 - 10, 10√3 - 5 - 10√3) = (5√3, -5)

Now, compute the dot product:

OT1 • OT2 = (-5√3)(5√3) + (-5)(-5) = -75 + 25 = -50

|OT1| = 10, |OT2| = 10

cosθ = (-50)/(10*10) = -0.5 ⇒ θ = 120°

Ah! There we go. The central angle is 120°, which matches our earlier calculation.

So the angle between the two radii to the tangent points on the top circle is 120°, so the arc length on the top circle is 120°/360° * 2πr = (1/3)*2πr = 2πr/3.

Three circles, so total arc length = 3*(2πr/3) = 2πr.

Straight segments: each is the external tangent between two circles, length = distance between centers = 2r (since for equal radii, external tangent length is d = 2r).

Three straight segments, so total straight length = 3*2r = 6r.

Therefore, total belt length = 6r + 2πr = 2r(3 + π).

Wait, but let's confirm with r = 10.

Total belt length = 6*10 + 2π*10 = 60 + 20π.

The problem states the length is written as a + bπ, so a = 60, b = 20, so 