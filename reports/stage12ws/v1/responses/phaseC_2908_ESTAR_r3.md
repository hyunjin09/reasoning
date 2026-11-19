# phaseC_2908_ESTAR_r3

Family 2908; condition ESTAR; replicate 3; seed 1209218879.

7611 generated tokens; stop=stop. Input image-free; source text is supplied assistant prefill, not newly generated reasoning.

## User message

Use the following facts from the image as given.
Do not question or reinterpret them.

Visual facts:
- E1: How do the upper and lower-left circles meet? The upper circle is externally tangent to the lower-left circle.
- E2: How do the upper and lower-right circles meet? The upper circle is externally tangent to the lower-right circle.
- E3: How do the two lower circles meet? The two lower circles are externally tangent.

Original question:
A belt is drawn tightly around three circles of radius $10$ cm each, as shown. The length of the belt, in cm, can be written in the form $a + b\pi$ for rational numbers $a$ and $b$. What is the value of $a + b$?

[Exact prefix](../../../../outputs/stage12ws/v1/prefixes/2908_ESTAR.txt) · [Raw token receipt](../../../../outputs/stage12ws/v1/generations/phaseC_2908_ESTAR_r3/generation.json)

## New continuation

We are given three circles, each of radius $10$ cm, arranged such that:

- The upper circle is externally tangent to both the lower-left and lower-right circles.
- The two lower circles are externally tangent to each other.

This forms a symmetric triangular arrangement: the three circles are mutually externally tangent, forming an equilateral triangle when connecting their centers.

We are to find the length of a belt drawn tightly around all three circles. Since the belt is tight, it will consist of:

1. **Three straight segments** — each lying between the points of tangency on adjacent circles.
2. **Three circular arcs** — each arc lies on one circle and connects the points of tangency with its neighbors.

---

### Step 1: Determine the distance between centers

Since each circle has radius $10$, and they are externally tangent, the distance between any two centers is:

$$
d = 10 + 10 = 20 \text{ cm}
$$

So the centers form an equilateral triangle of side 20 cm.

---

### Step 2: Understand the belt path

The belt wraps around the three circles. Between each pair of adjacent circles, there is a straight segment of the belt that connects the two points of tangency. These straight segments lie along the external common tangents of the two circles.

But since the circles are arranged in a symmetric triangle, the belt will hug the outer sides of the circles, and the straight parts will be the external common tangents.

However, because the circles are mutually externally tangent, and arranged in a triangle, the belt will consist of:

- Three straight segments, each connecting the point of tangency between two circles.
- Three arcs, each on one circle, between those points of tangency.

Wait — actually, the belt will go around the *outside* of the three circles. So for each circle, the belt will follow an arc that spans an angle, and then connect to the next circle via a straight line.

In this configuration, the belt will touch each circle at two points (one on each adjacent circle), and the arc on each circle will be the part not covered by the straight segments.

Because of symmetry, the belt will make equal arcs on each circle, and the straight segments will be equal in length.

---

### Step 3: Find the angle of the arc on each circle

Consider one circle. The belt touches it at two points: one from the left neighbor and one from the right neighbor. The angle between these two points, as seen from the center of the circle, is the central angle corresponding to the arc of the belt wrapped around that circle.

Due to symmetry, the belt will form an equilateral triangle of centers, and the belt’s straight segments will be tangent to the circles.

Actually, let’s think geometrically.

Imagine the belt going around the three circles. At each circle, the belt will be tangent to it. The belt will make a “corner” at each circle, but since the circles are arranged symmetrically, the belt will form a sort of “triangle” around the circles.

The key idea: The belt consists of **three straight segments** and **three circular arcs**.

Each straight segment is the external common tangent between two adjacent circles.

Each arc is the portion of the circle between the two points of tangency.

Let’s compute the angle subtended by each arc.

---

### Step 4: Compute the angle of the arc on each circle

Let’s focus on one circle. Let O be its center. Let A and B be the centers of the adjacent circles.

The belt touches the circle at two points: P (tangent to circle on the left) and Q (tangent to circle on the right).

The lines OP and OQ are radii to the points of tangency, so they are perpendicular to the respective tangent lines.

The belt’s straight segments are the external common tangents — so the angle between the two radii OP and OQ is equal to the angle between the two tangent lines.

Actually, consider the triangle formed by the centers O, A, B.

Triangle OAB is equilateral with side 20 cm.

The belt’s straight segments are the external common tangents. But for two circles of equal radius, the external common tangent is perpendicular to the line joining centers? Not exactly — the external tangent makes equal angles with the line joining centers.

Actually, for two circles of equal radius, the external common tangent is parallel to the line joining centers? No — it's not.

Wait — better approach: For two circles of radius r, centers separated by d, the external common tangent forms a right triangle with the line joining centers.

Specifically, if you draw the line joining centers, and then drop perpendiculars from centers to the tangent line (which are both radius r), then the distance between the feet of the perpendiculars is d, and the angle θ between the line joining centers and the tangent is such that sinθ = r / (d/2)? Wait.

Actually, for two circles of radius r, centers separated by d, the external common tangent creates a trapezoid with two radii perpendicular to the tangent, so the two radii are parallel, and the distance between them is d. Then, the angle between the line joining centers and each radius is α, where cosα = r / (d/2)? Not quite.

Wait — here’s the correct method.

Draw the two centers O1, O2, distance d = 20 cm apart. Draw the external common tangent touching the circles at T1 and T2. The radii O1T1 and O2T2 are perpendicular to the tangent, so they are parallel. Thus, the figure O1O2T1T2 is a trapezoid with O1T1 and O2T2 parallel and equal length (both radius 10). So the distance between O1 and O2 is 20, and the two radii are 10, so the angle between O1O2 and O1T1 is such that...

Actually, if we draw the line O1O2, and then from O1 and O2 draw lines perpendicular to the tangent, which meet at T1 and T2. The segment T1T2 is the tangent, and the distance between O1 and O2 is 20.

Now, if we draw the line connecting O1 to O2, and then the two radii O1T1 and O2T2, they are both perpendicular to the same line (the tangent), so they are parallel. Therefore, the quadrilateral O1T1T2O2 is a rectangle? No — unless the tangent is horizontal and the centers are aligned vertically.

Wait — actually, for external tangent, the centers and the tangent form a trapezoid, and the angle between O1O2 and O1T1 can be found using trigonometry.

Consider the triangle formed by O1, O2, and the point where the line O1O2 meets the line connecting T1 and T2 — but perhaps simpler:

The external common tangent creates a right triangle if we connect the centers and then draw a line from O1 to O2, and then from O1 draw a line to the point where the tangent would intersect the line O1O2 extended.

Actually, standard result: For two circles of equal radius r, centers separated by d, the external common tangent forms an angle θ with the line joining centers, where sinθ = r / (d/2)? No.

Wait — here’s the correct way:

The external common tangent will be such that the two radii to the points of tangency are parallel, and the distance between centers is d. So if you draw a line from O1 to O2, and then draw a line from O1 perpendicular to the tangent (radius), and similarly from O2, then the angle between O1O2 and the radius is such that the difference in direction is 180° minus the angle between the tangent and the line joining centers.

Alternatively, imagine translating one circle so that the centers coincide. The external tangent will be offset by 2r in the direction perpendicular to the line joining centers? No.

Actually, the angle φ between the line joining centers and the tangent is such that tanφ = r / (d/2)? Let me think.

If you draw the line joining centers O1O2, length d=20. Now, the external tangent touches the circles at T1 and T2. The radii O1T1 and O2T2 are both perpendicular to the tangent, so they are parallel. Therefore, the vector from O1 to O2 is the vector connecting the centers, and the vector from O1 to T1 is perpendicular to the tangent, same for O2 to T2.

Therefore, the displacement from O1 to O2 is equal to the displacement from T1 to T2 projected along the direction perpendicular to the tangent? Actually, no.

Better: Consider the triangle formed by O1, O2, and the point where the external tangent intersects the line O1O2 extended. But perhaps easier: The angle between O1O2 and the radius O1T1 is equal to the angle between O1O2 and O2T2.

Actually, since O1T1 and O2T2 are parallel and both perpendicular to the tangent, the angle between O1O2 and the line O1T1 is equal to the angle between O1O2 and O2T2, say α.

Then, the triangle O1O2P, where P is the intersection point of the lines O1T1 and O2T2 extended — but since they are parallel, they don’t intersect.

Wait — instead, consider the triangle formed by O1, O2, and the point where the external tangent meets the line O1O2 extended.

Actually, here’s a standard result:

For two circles of radius r, centers distance d apart, the angle θ between the line joining centers and the external common tangent is given by:

$$
\sin\theta = \frac{r}{d}
$$

Wait — no. Let’s derive it.

Draw the line joining centers O1O2, length d=20. From O1, draw radius perpendicular to tangent → length r=10. From O2, same. Since the radii are parallel, the distance between O1 and O2 is d, and the two radii are separated by d, so the angle between the line O1O2 and the radius is β, such that:

cosβ = r / (d/2)? No.

Actually, if you draw a line from O1 to O2, and then from O1 draw a line perpendicular to the tangent (radius), and from O2 draw another perpendicular (also radius), then the two radii are parallel, and the distance between O1 and O2 is d, so the angle between O1O2 and the radius is such that:

The projection of O1O2 onto the direction perpendicular to the radii is zero? Not helpful.

Wait — here’s a better idea: The external common tangent forms a triangle with the line joining centers and the two radii.

Actually, the external common tangent will create a triangle with the centers and the point where the tangent meets the line joining centers — but since the radii are parallel, the line joining centers is transverse.

Actually, the angle between the line joining centers and the tangent is θ, and sinθ = r / (d/2)? Let me check with a diagram.

Suppose the two circles are side by side, centers 20 cm apart, radius 10 cm each. The external tangent above them — the distance between the centers is 20, and the vertical distance between the points of tangency is 0? No.

Actually, for two circles of equal radius, the external common tangent is horizontal if the centers are aligned horizontally. The radii are vertical, so the angle between the line joining centers and the radius is 90 degrees? That doesn’t help.

Wait — I think I made a mistake.

Actually, for two circles of radius r, centers distance d apart, the external common tangent is not perpendicular to the line joining centers — unless d = 2r, in which case the external tangent is perpendicular.

Wait — no. If the circles are separate, the external tangent is slanted.

Here’s the correct derivation:

Draw the line joining centers O1O2, length d=20. Draw the external tangent touching the circles at T1 and T2. The radii O1T1 and O2T2 are both perpendicular to the tangent, so they are parallel. Therefore, the distance between the two radii is d = 20.

But the radii are both length 10, so if we draw a line connecting O1 to O2, and then from O1 draw a line to T1 (perpendicular to tangent), and from O2 draw a line to T2 (perpendicular to tangent), then since the radii are parallel, the vector O1T1 and O2T2 are parallel and same direction.

So the displacement from O1 to O2 is equal to the displacement from T1 to T2 projected along the direction of the radii? Not exactly.

Actually, the line segment T1T2 is the external tangent, and the line segment O1O2 is the line connecting centers.

The angle between O1O2 and the tangent is θ, and the angle between O1O2 and the radius is also θ, because the radius is perpendicular to the tangent.

Wait — yes! The radius is perpendicular to the tangent, so the angle between the radius and the tangent is 90°. The angle between the line joining centers and the radius is θ, then the angle between the line joining centers and the tangent is 90° - θ.

But perhaps more directly: In the triangle formed by O1, O2, and the point where the tangent meets the line O1O2 extended — but since the radii are parallel, we can construct a triangle.

Actually, here’s a standard result: The angle φ between the line joining centers and the external common tangent satisfies:

$$
\tan\phi = \frac{r}{d/2}?
$$

No — let’s do it properly.

Consider the triangle formed by O1, O2, and the point where the external tangent intersects the line O1O2 extended — call it P. But since the radii are parallel, the triangle O1O2P is such that O1P and O2P are not necessarily equal.

Actually, draw the line O1O2. From O1, draw a line perpendicular to the tangent — that’s the radius to T1. Similarly for O2. Since the radii are parallel, the distance between O1 and O2 is d, and the angle between O1O2 and the radius is α, such that the component of O1O2 along the direction perpendicular to the radius is zero? Not helping.

Wait — here’s a better idea: The external common tangent creates a triangle with the centers and the point where the tangent meets the line joining centers — but since the radii are parallel, the triangle is not formed.

Actually, the correct way is to note that the external common tangent forms a right triangle with the line joining centers and the difference in position.

Standard formula: For two circles of radius r, centers distance d apart, the length of the external common tangent is $ \sqrt{d^2 - (r_1 - r_2)^2} $. But since r1 = r2 = 10, then the length of the external common tangent is $ \sqrt{d^2 - 0} = d = 20 $? That can't be right — because if the circles are separate, the external tangent should be longer than d.

Wait — no, for external tangent, if r1 = r2, then the external common tangent is actually perpendicular to the line joining centers only if the circles are on opposite sides — but for external tangent, the formula is:

Length of external common tangent = $ \sqrt{d^2 - (r_1 - r_2)^2} $

Yes, and for r1 = r2, this becomes $ \sqrt{d^2 - 0} = d $.

But that seems counterintuitive — if the circles are side by side, the external tangent should be longer than d.

Wait — no, for two circles of equal radius, the external common tangent is indeed equal to d? Let me think.

Suppose two circles of radius 10, centers 20 cm apart. The external tangent above them — the tangent line touches each circle at the top. Then the distance between the points of tangency is 20 cm, same as the distance between centers — because the radii are vertical, so the tangent is horizontal, and the points of tangency are directly above the centers, so the distance between them is 20 cm.

Ah! So the length of the external common tangent is 20 cm.

And the angle between the line joining centers and the tangent is 90 degrees — because the radii are perpendicular to the tangent.

So in this case, for two circles of equal radius, the external common tangent is perpendicular to the line joining centers? Only if the circles are aligned horizontally — yes, in this symmetric case.

Wait — no, if the circles are arranged in a triangle, the external tangent will not be perpendicular to the line joining centers — only if the circles are side by side.

In our problem, the three circles are arranged in an equilateral triangle, so the centers form an equilateral triangle of side 20 cm.

So for two adjacent circles, the line joining centers is 20 cm, and the external common tangent will be at an angle.

So we must find the angle between the line joining centers and the external common tangent.

Let’s denote the centers as A, B, C, forming an equilateral triangle with side 20 cm.

Consider the belt wrapping around the three circles. Between two adjacent circles, say A and B, the belt will have a straight segment that is the external common tangent.

This tangent will touch circle A at point P and circle B at point Q.

The line AB is 20 cm. The radii AP and BQ are both perpendicular to the tangent, so they are parallel.

The angle between AB and the tangent is θ.

In the triangle formed by A, B, and the point where the tangent meets the line AB extended — but since the radii are parallel, we can consider the triangle formed by A, B, and the point where the line AB meets the line connecting the two points of tangency — but perhaps better to use vectors or geometry.

Actually, the angle between the line joining centers and the external common tangent is equal to the angle between the line joining centers and the radius.

Since the radius is perpendicular to the tangent, the angle between the line joining centers and the radius is φ, and then the angle between the line joining centers and the tangent is 90° - φ.

But we can find φ using the fact that the triangle formed by A, B, and the point where the tangent meets the line AB extended — but since the radii are parallel, the triangle is not formed.

Wait — here’s a better idea: Consider the triangle formed by the centers A, B, and the point where the external tangent intersects the line AB extended — but since the radii are parallel, the line connecting the points of tangency is parallel to the line joining centers? No.

Actually, for two circles of equal radius, the external common tangent is parallel to the line joining centers only if the circles are aligned horizontally — but in general, it’s not.

Wait — no, in the case where the circles are side by side, the external tangent is horizontal, and the line joining centers is horizontal — so they are parallel.

In our case, the centers form an equilateral triangle, so the line joining centers is not horizontal — but the external common tangent will still be perpendicular to the radii.

So let’s consider the triangle formed by the centers A, B, and the point where the external tangent meets the line AB — but since the radii are parallel, the line AB is not perpendicular to the tangent.

Actually, let’s calculate the angle between the line AB and the radius.

From center A, draw radius to point of tangency — this radius is perpendicular to the tangent. The line AB is 20 cm long.

The angle between AB and the radius is the angle between the line joining centers and the radius.

In the triangle formed by A, B, and the point where the tangent meets the line AB extended — but since the radii are parallel, the distance between the two radii is d = 20 cm, and each radius is 10 cm, so the angle between AB and the radius is such that:

If we draw a line from A to B, and from A draw a line perpendicular to the tangent (radius), then the angle between AB and the radius is α, and the component of AB along the direction of the radius is 0? No.

Actually, the correct way is to realize that the external common tangent creates a triangle with the centers and the point where the tangent meets the line joining centers — but since the radii are parallel, the triangle is not formed.

Wait — here’s a standard geometry fact: For two circles of radius r, centers distance d apart, the angle θ between the line joining centers and the external common tangent is given by:

$$
\sin\theta = \frac{r}{d}
$$

Wait — let’s test with d = 20, r = 10: sinθ = 10/20 = 0.5, so θ = 30°.

Is that possible?

If the angle between the line joining centers and the external common tangent is 30°, then the angle between the line joining centers and the radius is 60°, since the radius is perpendicular to the tangent.

So for each straight segment of the belt, it is at 30° to the line joining centers.

But in our case, the centers form an equilateral triangle, so the angle between the line joining centers and the side of the triangle is 60°.

Wait — let’s think differently.

Perhaps it's easier to consider the angle at the center of each circle.

When the belt wraps around a circle, the arc is the part not covered by the straight segments.

At each circle, the belt is tangent to the circle at two points, and the angle between those two radii is the central angle of the arc.

Due to symmetry, this angle is the same for all three circles.

Let’s denote this angle as 2α.

Then the arc length on each circle is r * 2α = 10 * 2α = 20α.

The total arc length is 3 * 20α = 60α.

Now, what is α?

Consider one circle, say the top circle. The belt is tangent to it at two points: one from the left circle and one from the right circle.

The line joining the centers of the top and left circles is 20 cm, and the angle between this line and the radius to the point of tangency is 30°, as per earlier calculation.

Wait — let’s calculate the angle between the line joining centers and the radius.

From the center of the top circle, draw the radius to the point of tangency with the left circle. This radius is perpendicular to the tangent.

The line joining centers is 20 cm.

The angle between the line joining centers and the radius is β.

Then, in the triangle formed by the two centers and the point of tangency — wait, it's a bit messy.

Actually, consider the triangle formed by the center of the top circle, the center of the left circle, and the point of tangency.

The distance between centers is 20 cm. The radius to the point of tangency is 10 cm, and it is perpendicular to the tangent.

The line joining the centers is 20 cm, and the angle between this line and the radius is β.

Then, the angle between the line joining centers and the tangent is 90° - β.

But we want the angle between the line joining centers and the radius.

Actually, the angle β can be found using the law of sines or cosines.

Consider the triangle formed by the two centers and the point of tangency — but the point of tangency is not on the line joining centers.

Actually, the correct way is to realize that the external common tangent creates a triangle with the two centers and the point where the tangent meets the line joining centers — but since the radii are parallel, the line joining centers is not perpendicular to the tangent.

Wait — here’s a better idea: The angle between the line joining centers and the external common tangent is θ, and sinθ = r / d = 10 / 20 = 0.5, so θ = 30°.

Yes, that’s a standard result: for two circles of radius r, centers distance d apart, the angle between the line joining centers and the external common tangent is θ, where sinθ = r/d.

Why? Because if you draw the line joining centers, and then from each center draw a radius perpendicular to the tangent, then the two radii are parallel, and the distance between the two centers is d, and the distance between the two radii is d, but since the radii are perpendicular to the tangent, the angle between the line joining centers and the radius is such that the component of d along the direction perpendicular to the radii is 0? Not helpful.

Actually, if you consider the triangle formed by the two centers and the point where the external tangent meets the line joining centers — but since the radii are parallel, the line joining centers is not perpendicular to the tangent.

Wait — here’s the correct derivation:

Draw the line joining centers O1O2, length d=20. From O1, draw a radius perpendicular to the external tangent — length r=10. From O2, draw a radius perpendicular to the external tangent — length r=10. Since the radii are parallel, the distance between the two radii is d=20.

But the radii are both length 10, so the angle between O1O2 and the radius is such that the triangle formed by O1, O2, and the point where the line O1O2 meets the line connecting the two radii — but since the radii are parallel, the line O1O2 is transverse.

Actually, the angle between O1O2 and the radius is β, and then the distance between the two radii is d = 2 * r * sinβ? No.

Wait — if you have two parallel lines (the radii), distance between them is d=20, and each radius is r=10, then the angle β between the line joining centers and the radius is such that:

The distance between the two parallel lines is d, and the angle between the line joining centers and the radius is β, then d = 2 * r * sinβ? No.

Actually, if you have two parallel lines, distance between them is d, and you have a line connecting a point on one line to a point on the other line, length L, then the angle β between the line and the direction perpendicular to the lines is such that sinβ = d / L.

But here, the line joining centers is not perpendicular to the radii — the radii are perpendicular to the tangent, so the line joining centers is not perpendicular to the tangent.

Actually, the angle between the line joining centers and the radius is β, and the distance between the two radii is d, and the length of the line joining centers is also d, so in the triangle formed by the two centers and the point where the line joining centers meets the line connecting the two radii — but since the radii are parallel, the line joining centers is not perpendicular to them.

Actually, the correct formula is:

The angle β between the line joining centers and the radius is given by:

$$
\cos\beta = \frac{d}{2r} ? 
$$

No — let’s use coordinates.

Place the two centers: O1 at (0,0), O2 at (20,0). The external common tangent above them.

The tangent is above, and the radii are perpendicular to it.

Assume the tangent has slope m, but since the radii are perpendicular to it, and equal in length, the tangent will be at some angle.

The condition for the external common tangent: the distance from O1 to the tangent is 10, and from O2 to the tangent is 10.

The set of lines at distance 10 from O1 and from O2.

The external common tangent will be the line that is at distance 10 from both O1 and O2, and above them.

The distance from O1(0,0) to the line ax+by+c=0 is |c|/sqrt(a²+b²) = 10, similarly for O2(20,0): |20a + c|/sqrt(a²+b²) = 10.

Also, since it's external, the signs are the same.

Assume the line is y = mx + c.

Distance from (0,0) to line: |c| / sqrt(1+m²) = 10.

Distance from (20,0) to line: |20m + c| / sqrt(1+m²) = 10.

So |c| = 10 sqrt(1+m²)

|20m + c| = 10 sqrt(1+m²)

Square both equations:

c² = 100 (1+m²)

(20m + c)² = 100 (1+m²)

Expand: 400m² + 40m c + c² = 100 + 100m²

Substitute c² = 100 + 100m²:

400m² + 40m c + 100 + 100m² = 100 + 100m²

Simplify:

500m² + 40m c = 100m²

400m² + 40m c = 0

Divide by 40: 10m² + m c = 0

So m(10m + c) = 0

So either m=0, or c = -10m.

If m=0, then from c² = 100(1+0) = 100, so c=±10.

If c=10, then distance from (20,0) is |20*0 + 10| /1 = 10, good.

If c=-10, distance from (20,0) is |-10| = 10, also good.

But for external tangent, if c=10, the line is y=0, which is the x-axis — but that's the internal tangent.

For external, we need c=-10, then the line is y=0, again the same.

Wait — for m=0, the line is y=c, and for external tangent, we want the line above, so c>0, but then for O2, |20m + c| = |c| = 10, so c=10, and the line is y=10, which is above both centers.

Distance from (0,0) to y=10 is 10, good.

Distance from (20,0) to y=10 is 10, good.

And it's external — yes.

So the external common tangent is y=10.

Then the angle between the line joining centers (x-axis) and the tangent (y=10) is 90 degrees.

But in this case, the angle between the line joining centers and the radius is 90 degrees, because the radius is vertical, and the line joining centers is horizontal.

So for two circles side by side, the angle is 90 degrees.

But in our case, the circles are arranged in a triangle, so the line joining centers is not horizontal — it's at an angle.

In our case, the centers form an equilateral triangle, so the angle between the line joining centers and the horizontal is 60 degrees.

So for the external common tangent, the angle between the line joining centers and the tangent is 90 degrees — because the radius is perpendicular to the tangent.

Wait — no, in the side-by-side case, the radius is vertical, the line joining centers is horizontal, so the angle between them is 90 degrees.

In our case, the line joining centers is at 60 degrees to the horizontal, and the radius is perpendicular to the tangent, so if the tangent is horizontal, then the radius is vertical, so the angle between the line joining centers and the radius is 90 degrees - 60 degrees = 30 degrees.

Yes!

So for each pair of adjacent circles, the angle between the line joining centers and the radius to the point of tangency is 30 degrees.

Therefore, at each circle, the two radii to the points of tangency are separated by an angle of 2 * 30 degrees = 60 degrees.

Wait — is that correct?

Let’s see: from the center of a circle, the radius to the point of tangency with the left circle is at 30 degrees to the line joining centers.

Similarly, the radius to the point of tangency with the right circle is also at 30 degrees to the line joining centers, but on the other side.

So the total angle between the two radii is 30 + 30 = 60 degrees.

Yes!

So the central angle for the arc on each circle is 60 degrees.

Therefore, the arc length on each circle is (60/360) * 2πr = (1/6) * 2π * 10 = (1/3)π * 10 = (10/3)π cm.

Total arc length = 3 * (10/3)π = 10π cm.

Now, the straight segments.

There are three straight segments, each being the external common tangent between two adjacent circles.

From earlier, for two circles of radius r, centers distance d apart, the length of the external common tangent is √(d² - (r1 - r2)²) = √(d² - 0) = d = 20 cm.

But in our case, the circles are not side by side — they are arranged in an equilateral triangle, so the line joining centers is 20 cm, and the external common tangent is still 20 cm? Is that true?

In the side-by-side case, yes, the external common tangent is 20 cm.

In our case, the external common tangent will be the same length, because the formula depends only on d and r, not on the orientation.

Yes — the length of the external common tangent for two circles of radius r, centers distance d apart, is √(d² - (r1 - r2)²) = √(d² - 0) = d = 20 cm.

So each straight segment is 20 cm.

Total straight length = 3 * 20 = 60 cm.

Therefore, total belt length = arc length + straight length = 10π + 60 cm.

So in the form a + bπ, we have a = 60, b = 10.

Thus, a + b = 60 + 10 = 70.

---

### ✅ Final Answer: $\boxed{70}$
