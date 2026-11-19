# phaseC_2975_ESTAR_r0

Family 2975; condition ESTAR; replicate 0; seed 883325831.

9828 generated tokens; stop=stop. Input image-free; source text is supplied assistant prefill, not newly generated reasoning.

## User message

Use the following facts from the image as given.
Do not question or reinterpret them.

Visual facts:
- E1: In what order does the sloping secant from T meet the labelled circle points? R and S are respectively the far and near intersections of the secant from T with the circle.
- E2: What is the incidence and order of B, O and T along the horizontal line? B, O and T are collinear, with O between B and T and B on the circle.

Original question:
In the figure, point $O$ is the center of the circle, the measure of angle $RTB$ is 28 degrees, and the measure of angle $ROB$ is three times the measure of angle $SOT$. What is the measure of minor arc $RS$, in degrees?

[Exact prefix](../../../../outputs/stage12ws/v1/prefixes/2975_ESTAR.txt) · [Raw token receipt](../../../../outputs/stage12ws/v1/generations/phaseC_2975_ESTAR_r0/generation.json)

## New continuation

We are given:

- $O$ is the center of the circle.
- The secant from point $T$ intersects the circle at points $R$ and $S$, with $R$ being the **far** intersection and $S$ the **near** intersection (so order along the secant is: $T \to S \to R$).
- Points $B$, $O$, $T$ are collinear, with $O$ between $B$ and $T$, and $B$ lies on the circle.
- $\angle RTB = 28^\circ$
- $\angle ROB = 3 \times \angle SOT$

We are to find the measure of **minor arc $RS$**.

---

### Step 1: Understand the configuration

Since $O$ is the center, any angle at the center subtended by an arc equals the measure of that arc.

Also, angles formed by a tangent and a chord or by secants can be related to arcs via inscribed angle theorems.

But here, we have an angle $\angle RTB = 28^\circ$. Point $T$ is outside the circle, and $TB$ is a line through the center $O$ (since $B, O, T$ are collinear). So $TB$ is a line from $T$ through the center to point $B$ on the circle.

Point $R$ is also on the circle, and $TR$ is a secant from $T$ intersecting the circle at $R$ and $S$.

So $\angle RTB$ is the angle between two lines from $T$: one to $B$ (which passes through the center), and one to $R$.

This is an angle formed by a **secant** ($TR$) and a **line through the center** ($TB$).

There is a standard theorem for such angles:

> The measure of the angle formed by a secant and a line through the center (or a tangent) is half the difference of the intercepted arcs.

But in this case, since $TB$ passes through the center, and $TR$ is a secant, then:

$$
\angle RTB = \frac{1}{2} \left| \text{arc } RB - \text{arc } SB \right|
$$

Wait — let’s think carefully.

Actually, the standard **external angle** theorem for a point outside a circle:

> If two secants intersect at a point outside the circle, then the measure of the angle is half the difference of the intercepted arcs.

In our case, we have **one secant** ($TR$) and **one line through the center** ($TB$), which is actually a **tangent?** No — because $TB$ passes through the center, so unless $B$ is the point of tangency, it's not a tangent.

Wait — if $TB$ passes through the center, and $B$ is on the circle, then $TB$ is a **radius extended**, so it's a **line from external point T through center O to point B on circle**. So it’s a **line segment from T to B**, passing through center O.

Therefore, the angle $\angle RTB$ is formed by two lines from $T$: one is the secant $TR$ (intersecting circle at $R$ and $S$), and the other is the line $TB$ (passing through center to $B$).

This is a classic **angle between a secant and a radius**.

Actually, there is a useful theorem:

> The angle between a tangent and a chord is equal to half the measure of the intercepted arc.

But here, we don’t have a tangent — we have a secant and a radius.

Alternatively, consider triangle $RTB$.

But perhaps we should use the **inscribed angle theorem** or relate the angle to arcs.

Let’s try using the following approach:

Let’s denote:

Let $\angle SOT = x$. Then $\angle ROB = 3x$.

Now, since $O$ is the center, and $R, S, B$ are points on the circle, the central angles correspond directly to arc measures.

Note: Since $R$ and $S$ are points where the secant from $T$ meets the circle, and $R$ is farther from $T$, $S$ is closer, so along the secant, order is $T-S-R$.

Points $B, O, T$ are collinear, with $O$ between $B$ and $T$, so $B-O-T$.

So the direction from $T$ to $B$ goes through $O$, and $B$ is on the circle.

Now, consider the angle $\angle RTB = 28^\circ$. This is the angle between lines $TR$ and $TB$.

We can relate this angle to arcs using the **intercepted arcs**.

There is a formula for the angle between a secant and a line through the center.

Alternatively, consider the triangle $TOB$ and $TOR$.

But perhaps the most straightforward method is to use the **tangent-secant angle theorem**.

Wait — actually, since $TB$ passes through the center, and $B$ is on the circle, then $TB$ is a **diameter extension** — meaning it’s a straight line through the center to point $B$.

So, the angle $\angle RTB$ is formed by two lines from $T$: one to $B$ (along diameter), and one to $R$ (secant).

The angle between them is 28°.

There is a theorem: the angle between a secant and a line through the center is equal to **half the difference of the intercepted arcs**.

Specifically, for an external point $T$, and two points $R$ and $S$ on the circle, with secant $TR$ intersecting at $R$ and $S$, and another line $TB$ through the center intersecting at $B$, then:

$$
\angle RTB = \frac{1}{2} \left| \text{arc } RB - \text{arc } SB \right|
$$

Wait — let’s verify.

Actually, the general formula for the angle formed by two secants from an external point is:

$$
\angle = \frac{1}{2} | \text{major arc} - \text{minor arc} |
$$

But here, we have only one secant and one line through the center.

Wait — perhaps we can consider the angle as part of a triangle.

Alternatively, let’s use coordinates or vectors — but that might be messy.

Another idea: use the fact that the angle between two chords intersecting outside the circle is half the difference of the intercepted arcs.

But again, we have only one secant and a radius.

Wait — here’s a better idea.

Let’s consider the triangle $RTB$.

But we don’t know much about side lengths.

Instead, consider the arcs.

Let’s denote the measure of minor arc $RS$ as $y$ degrees. That’s what we need to find.

We are told that $\angle ROB = 3 \cdot \angle SOT = 3x$, and $\angle RTB = 28^\circ$.

Now, note that $\angle ROB$ and $\angle SOT$ are central angles.

Since $R, S, B$ are points on the circle, and $O$ is center, then:

- Arc $RB$ corresponds to central angle $\angle ROB = 3x$
- Arc $SO$? Wait — $\angle SOT$ — point $T$ is outside, so angle $SOT$ is not a central angle — point $T$ is not on the circle.

Ah! Important: $\angle SOT$ is an angle at point $O$, between points $S$, $O$, $T$. Since $O$ is the center, and $T$ is outside, then $\angle SOT$ is an angle formed by two rays: $OS$ and $OT$.

Similarly, $\angle ROB$ is formed by rays $OR$ and $OB$.

So both are angles at the center.

Therefore, the arcs they subtend are:

- $\angle ROB$ subtends arc $RB$ — so arc $RB = 3x$
- $\angle SOT$ subtends arc $ST$ — wait, no.

Actually, angle $SOT$ is between rays $OS$ and $OT$. But point $T$ is not on the circle, so this angle does not directly correspond to an arc on the circle.

Wait — that’s a problem.

Unless... perhaps $\angle SOT$ is meant to be interpreted as the angle between $OS$ and $OT$, but since $T$ is outside, this doesn't directly give an arc.

Wait — maybe the notation $\angle SOT$ refers to the central angle corresponding to arc $ST$? But that would require $T$ to be on the circle, which it isn't.

So perhaps there's a misinterpretation.

Wait — look back at E2: “What is the incidence and order of B, O and T along the horizontal line? B, O and T are collinear, with O between B and T and B on the circle.”

So $B, O, T$ are collinear, with $O$ between $B$ and $T$, and $B$ on the circle.

Then, $\angle SOT$ is the angle at $O$ between points $S$, $O$, $T$.

That is, in triangle $SOT$, angle at $O$.

But point $T$ is outside the circle, so ray $OT$ goes from center $O$ to point $T$, which is outside.

So $\angle SOT$ is the angle between radius $OS$ and line $OT$.

Similarly, $\angle ROB$ is the angle between radius $OR$ and radius $OB$.

So these are angles at the center.

But $\angle SOT$ is not a central angle over an arc — it’s the angle between a radius and a line to an external point.

So how do we relate that?

Perhaps we can use the fact that the angle between a radius and a secant from an external point relates to the arc.

Wait — here’s a key insight.

Consider the angle $\angle SOT$.

Since $OT$ is a straight line from $O$ to $T$, and $OS$ is a radius, then the angle $\angle SOT$ is the angle between radius $OS$ and the line $OT$.

But since $B, O, T$ are collinear, and $O$ is between $B$ and $T$, then line $OT$ is the same as line $OB$, extended beyond $O$ to $T$.

So ray $OT$ is opposite to ray $OB$.

Thus, $\angle SOT$ is the angle between $OS$ and the line $OT$, which is the same as the angle between $OS$ and $OB$, but measured in the opposite direction.

Actually, since $OT$ is the extension of $OB$, then $\angle SOT = \angle SOB$, because $OT$ and $OB$ are opposite rays.

Wait — no.

If $B, O, T$ are collinear with $O$ between $B$ and $T$, then vector $OT$ is in the opposite direction to vector $OB$.

So the angle $\angle SOT$ is the angle between $OS$ and $OT$, which is equal to the angle between $OS$ and the opposite of $OB$.

So $\angle SOT = 180^\circ - \angle SOB$.

Because if you extend $OB$ to $T$, then the angle between $OS$ and $OT$ is supplementary to the angle between $OS$ and $OB$.

Is that correct?

Let me draw mentally:

- Point $O$, point $B$ on circle, point $T$ on the line $BO$ extended beyond $O$.
- So $B-O-T$ in a straight line.
- Ray $OS$ is some radius.
- Angle $\angle SOT$ is angle at $O$ between points $S$, $O$, $T$ — so between vectors $OS$ and $OT$.
- Angle $\angle SOB$ is angle between $OS$ and $OB$.
- Since $OT$ is opposite to $OB$, then $\angle SOT = 180^\circ - \angle SOB$.

Yes.

Therefore,

$$
\angle SOT = 180^\circ - \angle SOB
$$

But we are told that $\angle ROB = 3 \cdot \angle SOT$

And $\angle ROB$ is the angle between $OR$ and $OB$.

Let’s denote $\angle SOB = \theta$, then $\angle SOT = 180^\circ - \theta$

Then:

$$
\angle ROB = 3(180^\circ - \theta)
$$

But $\angle ROB$ is also the angle between $OR$ and $OB$.

Now, note that $\angle ROB$ and $\angle SOB$ are adjacent angles if $R$ and $S$ are on the same side of $OB$, or opposite.

But we don’t know the relative positions.

However, since $R$ and $S$ are both on the circle, and the secant from $T$ intersects the circle at $R$ (far) and $S$ (near), and since $T$ is outside, the points $R$ and $S$ lie on the same side of line $OT$ (which is line $OB$).

Actually, the secant from $T$ intersects the circle at two points: $S$ (closer to $T$) and $R$ (farther). Since $T$ is outside, and $O$ is center, then the secant must cross the circle twice, and since $T$ is on one side, the two points $S$ and $R$ are on the same side of line $OT$.

So the rays $OS$ and $OR$ are both on the same side of line $OT$ (i.e., line $OB$).

Therefore, $\angle ROB$ and $\angle SOB$ are adjacent angles along the same side.

So, if we let $\angle SOB = \theta$, then $\angle ROB = 3(180^\circ - \theta)$

But since $R$ and $S$ are on the same side of $OB$, and $R$ is farther from $T$, then likely $R$ is farther around the circle from $S$.

Actually, the arc from $S$ to $R$ could be going clockwise or counterclockwise.

But we are to find minor arc $RS$, so we’ll take the smaller one.

Now, the total angle around point $O$ is 360°.

But perhaps we can express the position of $R$ and $S$ relative to $B$.

Let’s define:

Let’s set point $B$ at angle 0° for simplicity.

Since $B, O, T$ are collinear with $O$ between $B$ and $T$, and $T$ is on the opposite side of $O$ from $B$, then the line $OT$ is the negative direction of $OB$.

So, let’s say the ray $OB$ is at angle 0°, then ray $OT$ is at angle 180°.

Now, point $S$ is on the circle, so let’s say $\angle SOB = \theta$, so the direction of $OS$ is at angle $\theta$.

Similarly, point $R$ is on the circle, and $\angle ROB = 3(180^\circ - \theta)$

But since $R$ and $S$ are on the same side of $OB$ (because the secant from $T$ enters near $S$ and exits far $R$, both on the same side of the line $OT$), then the angle for $R$ should be greater than that for $S$ if we are measuring from $OB$.

So, if $OS$ is at angle $\theta$, then $OR$ is at angle $\angle ROB = 3(180^\circ - \theta)$, but since $R$ is farther from $T$, and $T$ is on the 180° side, then $R$ should be at a larger angle than $S$.

But wait — if $OB$ is at 0°, and $OT$ is at 180°, then the secant from $T$ (at 180°) hits the circle first at $S$ (closer to $T$), then at $R$ (farther).

As we move from $T$ toward the circle, we hit $S$ first, then $R$. Since $T$ is on the 180° side, and the circle is centered at $O$, then the points $S$ and $R$ are on the circle, and the secant from $T$ (on the 180° ray) intersects the circle at two points.

The point $S$ is closer to $T$, so its angular position should be closer to 180° than $R$ is.

So if we measure angles from $OB$ (0°), then $S$ is at angle $\theta$, and $R$ is at angle $\phi > \theta$.

But $\angle ROB = \phi$, and $\angle SOB = \theta$.

Given that $\angle ROB = 3 \angle SOT$

And $\angle SOT = 180^\circ - \theta$ (as established earlier)

So:

$$
\phi = 3(180^\circ - \theta)
$$

But since $R$ is farther from $T$ (which is at 180°), and $S$ is closer, then $\phi$ should be less than 180°, and $\theta$ should be less than $\phi$, and both less than 180°.

But $\phi = 3(180 - \theta) = 540 - 3\theta$

For $\phi < 180^\circ$:

$$
540 - 3\theta < 180 \Rightarrow -3\theta < -360 \Rightarrow \theta > 120^\circ
$$

Also, since $\theta = \angle SOB$, and $S$ is on the circle, $\theta$ should be between 0° and 180°.

So $\theta > 120^\circ$, and $\phi = 540 - 3\theta < 180^\circ$, so $\theta > 120^\circ$, and also $\phi > 0^\circ$, so $540 - 3\theta > 0 \Rightarrow \theta < 180^\circ$

So $\theta \in (120^\circ, 180^\circ)$

Now, we need to relate this to the angle $\angle RTB = 28^\circ$

Recall that $\angle RTB$ is the angle at $T$ between points $R$, $T$, $B$.

So, in triangle $RTB$, we have points $R$, $T$, $B$.

We know $B$ is on the circle, $T$ is outside, $R$ is on the circle.

We can use the law of sines or properties of circles.

But perhaps the best way is to use the **angle between two secants**.

Actually, since $TB$ is a line through the center, and $TR$ is a secant, then the angle $\angle RTB$ is equal to half the difference of the intercepted arcs.

Specifically, for an external point $T$, and two points $R$ and $S$ on the circle, the angle between the secant $TR$ and the line $TB$ (which is a radius) is half the difference of the arcs intercepted.

But which arcs?

The angle $\angle RTB$ intercepts arc $RB$ and arc $SB$? Not exactly.

Actually, the angle between the secant $TR$ and the line $TB$ (which is a radius) — since $TB$ is a radius extended, it’s like a tangent? No, it’s not tangent unless perpendicular.

Wait — there is a theorem: the angle between a secant and a radius drawn to the point of intersection is equal to half the difference of the intercepted arcs.

But I recall that for a point outside the circle, the angle between a secant and a tangent is half the difference of the intercepted arcs.

But here, we have a secant and a radius — which is not a tangent.

However, since the radius is part of the line from the center to the circle, perhaps we can consider the angle between the secant and the radius as half the difference of the arcs.

Let me try to derive it.

Consider triangle $ORT$.

But perhaps use coordinates.

Let’s place point $O$ at origin.

Let’s assume point $B$ is at $(1, 0)$, since it’s on the circle.

Since $O$ is center, and $B$ is on circle, let’s assume radius is 1 for simplicity.

So $O = (0,0)$, $B = (1,0)$

Since $B, O, T$ are collinear with $O$ between $B$ and $T$, then $T$ is on the negative x-axis, so $T = (-t, 0)$ for some $t > 0$.

Now, the secant from $T$ intersects the circle at $S$ and $R$, with $S$ closer to $T$, $R$ farther.

The circle has equation $x^2 + y^2 = 1$.

The secant from $T = (-t, 0)$ intersects the circle at two points.

The line from $T$ to $R$ and $S$ — but we don't know the direction.

But we know that the angle $\angle RTB = 28^\circ$

Point $T = (-t, 0)$, point $B = (1,0)$, point $R = (x,y)$ on circle.

Vector $TB = B - T = (1 - (-t), 0 - 0) = (1+t, 0)$

Vector $TR = R - T = (x - (-t), y - 0) = (x + t, y)$

The angle between vectors $TB$ and $TR$ is 28 degrees.

So:

$$
\cos(28^\circ) = \frac{ \vec{TB} \cdot \vec{TR} }{ |\vec{TB}| |\vec{TR}| }
$$

Compute dot product:

$\vec{TB} \cdot \vec{TR} = (1+t)(x + t) + (0)(y) = (1+t)(x + t)$

$|\vec{TB}| = \sqrt{(1+t)^2} = 1 + t$ (since $t > 0$)

$|\vec{TR}| = \sqrt{(x + t)^2 + y^2}$

But since $R$ is on the circle, $x^2 + y^2 = 1$

So $|\vec{TR}| = \sqrt{(x + t)^2 + y^2} = \sqrt{x^2 + 2tx + t^2 + y^2} = \sqrt{1 + 2tx + t^2}$

So:

$$
\cos(28^\circ) = \frac{ (1+t)(x + t) }{ (1 + t) \sqrt{1 + 2tx + t^2} } = \frac{ x + t }{ \sqrt{1 + 2tx + t^2} }
$$

So:

$$
\cos(28^\circ) = \frac{ x + t }{ \sqrt{1 + 2tx + t^2} }
$$

Square both sides:

$$
\cos^2(28^\circ) = \frac{ (x + t)^2 }{ 1 + 2tx + t^2 }
$$

Note that denominator is $1 + 2tx + t^2 = (x + t)^2 + 1 - x^2 - 2tx - t^2 + 2tx + t^2$ — wait, better:

Actually, $1 + 2tx + t^2 = (x + t)^2 + 1 - x^2 - 2tx - t^2 + 2tx + t^2$ — no.

From above:

Denominator = $1 + 2tx + t^2$

Numerator = $(x + t)^2$

So:

$$
\cos^2(28^\circ) = \frac{ (x + t)^2 }{ 1 + 2tx + t^2 }
$$

Let’s denote $u = x + t$, then numerator is $u^2$, denominator is $1 + 2t(x) + t^2 = 1 + 2t(u - t) + t^2 = 1 + 2tu - 2t^2 + t^2 = 1 + 2tu - t^2$

So:

$$
\cos^2(28^\circ) = \frac{ u^2 }{ 1 + 2tu - t^2 }
$$

But this seems messy.

Alternatively, from:

$$
\cos^2(28^\circ) = \frac{ (x + t)^2 }{ (x + t)^2 + 1 - x^2 - 2tx - t^2 + 2tx + t^2 } — no.

Wait — from:

Denominator = 1 + 2tx + t^2

But 1 + 2tx + t^2 = (x^2 + y^2) + 2tx + t^2 = x^2 + 2tx + t^2 + y^2 = (x + t)^2 + y^2

Oh! Yes!

Since $x^2 + y^2 = 1$, then:

$$
1 + 2tx + t^2 = x^2 + y^2 + 2tx + t^2 = (x + t)^2 + y^2
$$

So:

$$
\cos^2(28^\circ) = \frac{ (x + t)^2 }{ (x + t)^2 + y^2 }
$$

Let $A = x + t$, $B = y$, then:

$$
\cos^2(28^\circ) = \frac{ A^2 }{ A^2 + B^2 }
$$

So:

$$
\frac{ A^2 }{ A^2 + B^2 } = \cos^2(28^\circ)
\Rightarrow 1 - \frac{B^2}{A^2 + B^2} = \cos^2(28^\circ)
\Rightarrow \frac{B^2}{A^2 + B^2} = 1 - \cos^2(28^\circ) = \sin^2(28^\circ)
$$

So:

$$
\frac{y^2}{(x + t)^2 + y^2} = \sin^2(28^\circ)
$$

But from earlier, we have:

$$
\frac{y^2}{(x + t)^2 + y^2} = \sin^2(28^\circ)
$$

Now, this gives us a relation between $x, y, t$.

But we also have the condition involving the arcs.

Recall that $\angle ROB = 3 \angle SOT$, and we have expressions in terms of angles.

Earlier, we had:

Let $\angle SOB = \theta$, then $\angle SOT = 180^\circ - \theta$, and $\angle ROB = 3(180^\circ - \theta)$

And since $R$ and $S$ are on the same side of $OB$, and $R$ is farther from $T$, then the angle for $R$ is greater than for $S$, so $\angle ROB > \angle SOB$, which is consistent with $3(180 - \theta) > \theta$ for $\theta > 120^\circ$.

Now, the arc $RS$ is the arc between $R$ and $S$.

The measure of arc $RS$ is the absolute difference of their central angles.

Let’s denote the central angle for $S$ as $\theta$, and for $R$ as $\phi = 3(180 - \theta)$

Then the arc $RS$ is $|\phi - \theta|$

But since $\phi > \theta$, arc $RS = \phi - \theta = 3(180 - \theta) - \theta = 540 - 3\theta - \theta = 540 - 4\theta$

But arc measure must be between 0 and 360, and minor arc means the smaller one.

But 540 - 4\theta, and since \theta > 120, then 540 - 4*120 = 540 - 480 = 60, and since \theta < 180, 540 - 4*180 = 540 - 720 = -180, which is negative, so arc RS = 540 - 4\theta, but since it's negative, we take the supplement? No.

Actually, the arc between R and S is the smaller arc, so if the central angle is large, we take 360 minus that.

But in this case, since \phi - \theta = 540 - 4\theta, and \theta > 120, then 540 - 4\theta < 60, and since \theta < 180, 540 - 4\theta > 540 - 720 = -180, so it can be negative.

But arc measure is always positive, so the actual arc measure is the minimum of | \phi - \theta | and 360 - | \phi - \theta |.

But since \phi = 3(180 - \theta) = 540 - 3\theta, and \theta > 120, then \phi = 540 - 3\theta < 540 - 360 = 180, and since \theta > 120, \phi < 180, and \theta > 120, so \phi - \theta = 540 - 4\theta < 60, and since \theta < 180, \phi - \theta > 540 - 720 = -180, so \phi - \theta can be negative.

But the arc between R and S is the smaller arc, so if \phi - \theta is negative, then the arc is \theta - \phi, but since \phi > \theta? Let's check.

\phi = 540 - 3\theta, \theta = \angle SOB

For example, if \theta = 120, then \phi = 540 - 360 = 180, so \phi - \theta = 60 > 0

If \theta = 150, \phi = 540 - 450 = 90, so \phi - \theta = 90 - 150 = -60 < 0

So when \theta > 180 - 3\theta? When is \phi > \theta?

540 - 3\theta > \theta => 540 > 4\theta => \theta < 135

So for \theta < 135, \phi > \theta, so arc RS = \phi - \theta = 540 - 4\theta

For \theta > 135, \phi < \theta, so arc RS = \theta - \phi = \theta - (540 - 3\theta) = 4\theta - 540

And since \theta > 135, 4\theta - 540 > 4*135 - 540 = 540 - 540 = 0, and \theta < 180, 4*180 - 540 = 720 - 540 = 180, so arc RS = 4\theta - 540 for \theta > 135

But we have to use the angle condition from the secant.

Back to the angle.

We have:

$$
\frac{y^2}{(x + t)^2 + y^2} = \sin^2(28^\circ)
$$

But also, the central angle for S is \theta, and since we placed B at (1,0), then the angle for S is \theta, so if we assume the circle is unit circle, then S has coordinates (cos\theta, sin\theta)

Similarly, R has coordinates (cos\phi, sin\phi) = (cos(540 - 3\theta), sin(540 - 3\theta)) = (cos(180 - 3\theta), sin(180 - 3\theta)) = (-cos(3\theta), sin(3\theta)) because cos(180 - x) = -cos x, sin(180 - x) = sin x.

Let me check:

540 - 3\theta = 360 + 180 - 3\theta = 180 - 3\theta mod 360, yes.

So R: (cos(180 - 3\theta), sin(180 - 3\theta)) = (-cos(3\theta), sin(3\theta))

Similarly, S: (cos\theta, sin\theta)

Now, T is at (-t, 0), and B is at (1,0)

Now, the angle \angle RTB = 28^\circ

But we can compute the angle between vectors TB and TR.

Vector TB = B - T = (1 - (-t), 0 - 0) = (1 + t, 0)

Vector TR = R - T = ( -cos(3\theta) - (-t), sin(3\theta) - 0 ) = ( -cos(3\theta) + t, sin(3\theta) )

The angle between TB and TR is 28 degrees.

So:

$$
\cos(28^\circ) = \frac{ \vec{TB} \cdot \vec{TR} }{ |\vec{TB}| |\vec{TR}| }
$$

Dot product = (1 + t)( -cos(3\theta) + t ) + (0)(sin(3\theta)) = (1 + t)(t - cos(3\theta))

|TB| = 1 + t

|TR| = \sqrt{ (t - cos(3\theta))^2 + (sin(3\theta))^2 } = \sqrt{ t^2 - 2t cos(3\theta) + cos^2(3\theta) + sin^2(3\theta) } = \sqrt{ t^2 - 2t cos(3\theta) + 1 }

So:

$$
\cos(28^\circ) = \frac{ (1 + t)(t - cos(3\theta)) }{ (1 + t) \sqrt{ t^2 - 2t cos(3\theta) + 1 } } = \frac{ t - cos(3\theta) }{ \sqrt{ t^2 - 2t cos(3\theta) + 1 } }
$$

Let’s denote c = cos(3\theta), then:

$$
\cos(28^\circ) = \frac{ t - c }{ \sqrt{ t^2 - 2t c + 1 } }
$$

Square both sides:

$$
\cos^2(28^\circ) = \frac{ (t - c)^2 }{ t^2 - 2t c + 1 }
$$

Note that denominator = (t - c)^2 + 1 - c^2? Let's see:

(t - c)^2 = t^2 - 2t c + c^2

So denominator = t^2 - 2t c + 1 = (t - c)^2 + 1 - c^2

But perhaps keep as is.

So:

$$
\cos^2(28^\circ) ( t^2 - 2t c + 1 ) = (t - c)^2
$$

Expand both sides:

Left: \cos^2(28^\circ) ( t^2 - 2t c + 1 )

Right: t^2 - 2t c + c^2

So:

$$
\cos^2(28^\circ) t^2 - 2t c \cos^2(28^\circ) + \cos^2(28^\circ) = t^2 - 2t c + c^2
$$

Bring all to left:

$$
\cos^2(28^\circ) t^2 - 2t c \cos^2(28^\circ) + \cos^2(28^\circ) - t^2 + 2t c - c^2 = 0
$$

Group like terms:

t^2 ( \cos^2(28^\circ) - 1 ) + t ( -2c \cos^2(28^\circ) + 2c ) + ( \cos^2(28^\circ) - c^2 ) = 0

Simplify:

t^2 ( - \sin^2(28^\circ) ) + t ( 2c (1 - \cos^2(28^\circ)) ) + ( \cos^2(28^\circ) - c^2 ) = 0

Since 1 - cos^2 = sin^2:

- t^2 \sin^2(28^\circ) + 2c t \sin^2(28^\circ) + \cos^2(28^\circ) - c^2 = 0

Divide both sides by \sin^2(28^\circ) (assuming sin≠0, which it isn't):

- t^2 + 2c t + \frac{\cos^2(28^\circ)}{\sin^2(28^\circ)} - \frac{c^2}{\sin^2(28^\circ)} = 0

Which is:

- t^2 + 2c t + \cot^2(28^\circ) - c^2 \csc^2(28^\circ) = 0

But this is messy.

Notice that we have c = cos(3\theta), and we need to find arc RS = | \phi - \theta | = |540 - 4\theta| or 4\theta - 540, but since we have a specific value, perhaps we can solve for \theta.

But we have one equation with two variables, t and \theta.

But perhaps we can eliminate t.

From the equation:

- t^2 + 2c t + \cot^2(28^\circ) - c^2 \csc^2(28^\circ) = 0

Let me write it as:

2c t - t^2 = c^2 \csc^2(28^\circ) - \cot^2(28^\circ)

Left side is - (t^2 - 2c t) = - [ (t - c)^2 - c^2 ] = - (t - c)^2 + c^2

Not helpful.

From:

- t^2 + 2c t + \cot^2(28^\circ) - c^2 \csc^2(28^\circ) = 0

Let me denote k = cot^2(28^\circ) - c^2 \csc^2(28^\circ)

Then -t^2 + 2c t + k = 0

So t^2 - 2c t - k = 0

But k depends on c.

Perhaps for the arc RS, we can find it without t.

Recall that the arc RS is the central angle between R and S, which is | \phi - \theta | = |540 - 4\theta|, but since \theta > 120, and for \theta < 135, it's 540 - 4\theta, for \theta > 135, it's 4\theta - 540.

But perhaps we can use the fact that the angle at T is 28 degrees, and relate to the arcs.

Another idea: use the formula for the angle between a secant and a radius.

I recall that the angle between a secant and a radius to the point of intersection is equal to half the difference of the intercepted arcs.

In this case, the secant is TR, and the radius is OB (since TB is the line to B).

The angle at T is between TR and TB.

The intercepted arcs are arc RB and arc SB.

So perhaps:

$$
\angle RTB = \frac{1}{2} | \text{arc } RB - \text{arc } SB |
$$

Arc RB is the arc from R to B, which is \angle ROB = 3x, where x = \angle SOT

Arc SB is the arc from S to B, which is \angle SOB = \theta

But arc RB = 3x, arc SB = \theta

And from earlier, x = \angle SOT = 180^\circ - \theta

So arc RB = 3(180 - \theta) = 540 - 3\theta

Arc SB = \theta

Then:

$$
\angle RTB = \frac{1}{2} | (540 - 3\theta) - \theta | = \frac{1}{2} |540 - 4\theta|
$$

And this equals 28 degrees.

So:

$$
\frac{1}{2} |540 - 4\theta| = 28
\Rightarrow |540 - 4\theta| = 56
$$

So 540 - 4\theta = 56 or 540 - 4\theta = -56

Case 1: 540 - 4\theta = 56 => 4\theta = 540 - 56 = 484 => \theta = 121

Case 2: 540 - 4\theta = -56 => 4\theta = 540 + 56 = 596 => \theta = 149

Now, recall that \theta > 120, and \theta < 180, so both are possible.

Now, arc RS = | \phi - \theta | = |540 - 4\theta|

For \theta = 121, |540 - 4*121| = |540 - 484| = 56

For \theta = 149, |540 - 4*149| = |540 - 596| = 56

So in both cases, arc RS = 56 degrees.

And since 56 < 180, it is the minor arc.

So the measure of minor arc RS is 56 degrees.

Let me verify.

In both cases, |540 - 4\theta| = 56, so arc RS = 56 degrees.

Now, is this consistent?

For \theta = 121, then \phi = 540 - 3*121 = 540 - 363 = 177

Then arc RS = |177 - 121| = 56

For \theta = 149, \phi = 540 - 3*149 = 540 - 447 = 93

Then arc RS = |93 - 149| = 56

Both give minor arc RS = 56 degrees.

And angle RTB = 28 degrees, as required.

So the answer is 56 degrees.

Therefore, the measure of minor arc RS is **56 degrees**.

**Final Answer**
\boxed{56}
