# A_I_BASE_3022_r1

Tokens:8894; cap:False; seed:1545396148.

## Input

```text
<|im_start|>user
Use the following facts from the image as given.
Do not question or reinterpret them.

Visual facts:
- E1: On which segment is point P drawn, and is it interior? P is in the interior of AC.
- E2: On which segment is point Q drawn, and is it interior? Q is in the interior of BC.

Original question:
In the diagram shown here (which is not drawn to scale), suppose that $\triangle ABC \sim \triangle PAQ$ and $\triangle ABQ \sim \triangle QCP$.  If $m\angle BAC = 70^\circ$, then compute $m\angle PQC$.<|im_end|>
<|im_start|>assistant

```

## Raw generated response

```text
We are given:

- $\triangle ABC \sim \triangle PAQ$
- $\triangle ABQ \sim \triangle QCP$
- $m\angle BAC = 70^\circ$
- Point $P$ is on segment $AC$, and interior.
- Point $Q$ is on segment $BC$, and interior.

We are to compute $m\angle PQC$.

---

### Step 1: Use similarity $\triangle ABC \sim \triangle PAQ$

Since $\triangle ABC \sim \triangle PAQ$, their corresponding angles are equal. We must determine the correspondence.

The order of vertices matters for similarity. Since $A$ corresponds to $P$, $B$ to $A$, and $C$ to $Q$, we have:

$$
\angle A \leftrightarrow \angle P, \quad \angle B \leftrightarrow \angle A, \quad \angle C \leftrightarrow \angle Q
$$

So,

$$
\angle BAC = \angle APQ = 70^\circ
$$

Also,

$$
\angle ABC = \angle PAQ, \quad \angle ACB = \angle AQP
$$

---

### Step 2: Use similarity $\triangle ABQ \sim \triangle QCP$

Correspondence: $A \leftrightarrow Q$, $B \leftrightarrow C$, $Q \leftrightarrow P$

So,

$$
\angle ABQ \leftrightarrow \angle QCP, \quad \angle BAQ \leftrightarrow \angle CQP, \quad \angle AQ B \leftrightarrow \angle QPC
$$

Wait — let’s be precise.

Given $\triangle ABQ \sim \triangle QCP$, so vertex $A$ corresponds to $Q$, $B$ to $C$, $Q$ to $P$.

Thus:

- $\angle A \leftrightarrow \angle Q$ in $\triangle QCP$
- $\angle B \leftrightarrow \angle C$
- $\angle Q \leftrightarrow \angle P$

So:

$$
\angle BAQ = \angle CQP, \quad \angle ABQ = \angle QCP, \quad \angle AQB = \angle QPC
$$

But note: $\angle BAQ$ is part of $\angle BAC = 70^\circ$, since $Q$ is on $BC$, and $P$ on $AC$, so point $Q$ is between $B$ and $C$, and $P$ between $A$ and $C$. So triangle $PAQ$ is inside $\triangle ABC$.

Let’s denote:

Let $x = \angle PQC$ — this is what we want to find.

Note that $\angle PQC$ is an angle at point $Q$ formed by points $P$, $Q$, $C$. Since $Q$ is on $BC$, and $P$ is on $AC$, then $\angle PQC$ is the angle between segments $QP$ and $QC$.

But notice that $\angle PQC$ is part of $\angle AQC$ or $\angle BQC$? Actually, since $Q$ is on $BC$, and $P$ is not on $BC$, then $\angle PQC$ is an angle inside triangle $PQC$.

From the second similarity, $\triangle ABQ \sim \triangle QCP$, we know:

$$
\angle AQB = \angle QPC
$$

But also, $\angle AQB$ is an angle in triangle $ABQ$, which is adjacent to angle $BQC$ (since $Q$ is on $BC$).

Alternatively, perhaps we can use angle chasing with the known angle.

---

### Step 3: Use angle sum in triangle ABC

In $\triangle ABC$, we know $\angle A = 70^\circ$. Let’s denote:

Let $\angle ABC = B$, $\angle ACB = C$, so $B + C = 110^\circ$.

From first similarity: $\triangle ABC \sim \triangle PAQ$, so:

- $\angle APQ = \angle BAC = 70^\circ$
- $\angle PAQ = \angle ABC = B$
- $\angle AQP = \angle ACB = C$

Now, consider triangle $PAQ$. Its angles are:

- $\angle PAQ = B$
- $\angle APQ = 70^\circ$
- $\angle AQP = C$

Sum: $B + 70^\circ + C = 180^\circ$ → $B + C = 110^\circ$, which checks out.

---

### Step 4: Use second similarity: $\triangle ABQ \sim \triangle QCP$

As before, correspondence: $A \leftrightarrow Q$, $B \leftrightarrow C$, $Q \leftrightarrow P$

So:

- $\angle BAQ = \angle CQP$
- $\angle ABQ = \angle QCP$
- $\angle AQB = \angle QPC$

Now, $\angle BAQ$ is part of $\angle BAC = 70^\circ$. Specifically, since $P$ is on $AC$, and $Q$ is on $BC$, then $\angle BAQ = \angle BAC = 70^\circ$? No — wait, point $Q$ is on $BC$, so ray $AQ$ splits angle $BAC$ into two parts: $\angle BAQ$ and $\angle QAC$.

Actually, $\angle BAQ$ is the angle between $BA$ and $AQ$, while $\angle BAC$ is between $BA$ and $CA$. So unless $Q$ lies on $AC$, which it doesn’t, $\angle BAQ < \angle BAC$.

But from similarity $\triangle ABQ \sim \triangle QCP$, we have:

$$
\angle BAQ = \angle CQP
$$

But $\angle CQP$ is the same as $\angle PQC$? Not exactly — $\angle CQP$ is the angle at $Q$ between $CQ$ and $QP$, which is exactly $\angle PQC$! Because it's the angle at $Q$ between points $P$, $Q$, $C$.

So:

$$
\angle BAQ = \angle PQC
$$

Therefore, if we can find $\angle BAQ$, we can find $\angle PQC$.

---

### Step 5: Express $\angle BAQ$ in terms of known quantities

We know $\angle BAC = 70^\circ$. But $\angle BAC = \angle BAQ + \angle QAC$.

So if we can find $\angle QAC$, we can find $\angle BAQ$.

But how?

From the first similarity, $\triangle ABC \sim \triangle PAQ$, we found:

- $\angle AQP = \angle ACB = C$

But $\angle AQP$ is the angle at $Q$ in triangle $PAQ$, which is between $AQ$ and $PQ$.

Note that point $Q$ is on $BC$, and $P$ is on $AC$, so line $PQ$ connects them.

Now, consider triangle $AQC$ — but maybe better to look at quadrilateral or triangle $PQC$.

Alternatively, consider triangle $ABC$ and point $Q$ on $BC$, so we can consider triangle $ABQ$ and triangle $AQC$.

But perhaps a better idea: use the fact that in triangle $ABC$, angles sum to 180°, and relate to other triangles.

We already know $B + C = 110^\circ$.

Now, in triangle $ABQ$, angles are:

- $\angle BAQ$ — let’s call it $x$
- $\angle ABQ = B$
- $\angle AQB = ?$

From earlier, from similarity $\triangle ABQ \sim \triangle QCP$, we have:

$$
\angle AQB = \angle QPC
$$

Also, from triangle $ABQ$, angle sum:

$$
x + B + \angle AQB = 180^\circ
$$

But we don't know $\angle AQB$ yet.

Wait — from the similarity $\triangle ABQ \sim \triangle QCP$, we also have:

$$
\angle AQB = \angle QPC
$$

And $\angle QPC$ is an angle in triangle $QPC$, which shares side $QC$ with triangle $QCP$.

But perhaps we can relate angles around point $Q$.

At point $Q$, the angles around it sum to 360°.

We have several angles at $Q$:

- $\angle AQB$: from triangle $ABQ$
- $\angle AQP$: from triangle $PAQ$
- $\angle PQC$: from triangle $PQC$ — this is what we want!
- Also, since $Q$ is on $BC$, the straight angle along $BC$ is 180°, so $\angle AQB + \angle AQC = 180^\circ$? Not necessarily — unless $A$ is on one side.

Actually, since $Q$ is on $BC$, and $A$ is not on $BC$, the rays from $Q$ to $A$, $P$, $C$ form angles.

Specifically, the angles around point $Q$:

- $\angle AQB$ — between $QA$ and $QB$
- $\angle AQP$ — between $QA$ and $QP$
- $\angle PQC$ — between $QP$ and $QC$
- $\angle CQA$ — between $QC$ and $QA$ — but this is the same as $\angle AQC$, which is supplementary to $\angle AQB$ if $A$, $Q$, $B$ are colinear? No, they’re not.

Actually, since $B$, $Q$, $C$ are colinear (because $Q$ is on $BC$), then the angles $\angle AQB$ and $\angle AQC$ are adjacent angles forming a straight line!

Yes! Because $B-Q-C$ is a straight line, so:

$$
\angle AQB + \angle AQC = 180^\circ
$$

Similarly, at point $Q$, the angles around point $Q$ include:

- $\angle AQB$ (in triangle $ABQ$)
- $\angle AQP$ (in triangle $PAQ$)
- $\angle PQC$ (in triangle $PQC$)
- And $\angle CQA$ — but since $B-Q-C$ is straight, $\angle AQC = 180^\circ - \angle AQB$

But also, $\angle AQP$ and $\angle PQC$ are adjacent angles along the direction from $A$ to $C$ via $P$? Not quite.

Actually, the rays from $Q$ are: $QA$, $QP$, $QC$ (with $QB$ and $QC$ opposite). Since $B-Q-C$ is straight, the ray $QB$ and $QC$ are opposite.

So the angles around point $Q$:

- Between $QA$ and $QB$: $\angle AQB$
- Between $QA$ and $QP$: $\angle AQP$
- Between $QP$ and $QC$: $\angle PQC$
- Between $QC$ and $QA$: $\angle AQC = 180^\circ - \angle AQB$

But note that $\angle AQP$ and $\angle PQC$ are adjacent and together form $\angle AQC$? Not necessarily — because $QP$ may not lie between $QA$ and $QC$.

Actually, since $P$ is on $AC$, and $Q$ is on $BC$, then the line $PQ$ goes from $AC$ to $BC$, so from point $Q$, the ray $QP$ lies between $QA$ and $QC$? Possibly.

Assuming the diagram is drawn such that $P$ is on $AC$, $Q$ on $BC$, and $PQ$ connects them, then from point $Q$, the rays are ordered: $QA$, then $QP$, then $QC$, because $P$ is on $AC$, so $QP$ is inside triangle $AQC$.

So, the angle $\angle AQC$ is split into $\angle AQP + \angle PQC$.

That is:

$$
\angle AQC = \angle AQP + \angle PQC
$$

But $\angle AQC = 180^\circ - \angle AQB$, since $B-Q-C$ is straight.

So:

$$
180^\circ - \angle AQB = \angle AQP + \angle PQC
$$

From earlier, from similarity $\triangle ABC \sim \triangle PAQ$, we have:

$$
\angle AQP = \angle ACB = C
$$

And from similarity $\triangle ABQ \sim \triangle QCP$, we have:

$$
\angle BAQ = \angle PQC
$$

Let’s denote $\angle BAQ = x = \angle PQC$ (as established above).

So:

$$
180^\circ - \angle AQB = \angle AQP + x = C + x
$$

So:

$$
180^\circ - \angle AQB = C + x \quad \text{(Equation 1)}
$$

Also, in triangle $ABQ$, angle sum:

$$
\angle BAQ + \angle ABQ + \angle AQB = 180^\circ
$$

Which is:

$$
x + B + \angle AQB = 180^\circ \quad \text{(Equation 2)}
$$

Subtract Equation 2 from Equation 1:

Left side: $(180^\circ - \angle AQB) - (x + B + \angle AQB) = 180^\circ - \angle AQB - x - B - \angle AQB = 180^\circ - x - B - 2\angle AQB$

Right side: $(C + x) - 180^\circ$? No — we are subtracting Equation 2 from Equation 1.

Wait — let me write again:

Equation 1: $180^\circ - \angle AQB = C + x$

Equation 2: $x + B + \angle AQB = 180^\circ$

Subtract Equation 2 from Equation 1:

$$
(180^\circ - \angle AQB) - (x + B + \angle AQB) = (C + x) - 180^\circ
$$

Simplify left: $180^\circ - \angle AQB - x - B - \angle AQB = 180^\circ - x - B - 2\angle AQB$

Right: $C + x - 180^\circ$

So:

$$
180^\circ - x - B - 2\angle AQB = C + x - 180^\circ
$$

Bring all terms to left:

$$
180^\circ - x - B - 2\angle AQB - C - x + 180^\circ = 0
$$

$$
360^\circ - 2x - B - C - 2\angle AQB = 0
$$

But $B + C = 110^\circ$, so:

$$
360^\circ - 2x - 110^\circ - 2\angle AQB = 0
$$

$$
250^\circ - 2x - 2\angle AQB = 0
$$

Divide by 2:

$$
125^\circ - x - \angle AQB = 0 \quad \Rightarrow \quad \angle AQB = 125^\circ - x
$$

Now plug back into Equation 2:

$$
x + B + (125^\circ - x) = 180^\circ
$$

Simplify:

$$
x + B + 125^\circ - x = 180^\circ \Rightarrow B + 125^\circ = 180^\circ \Rightarrow B = 55^\circ
$$

Then since $B + C = 110^\circ$, we get $C = 55^\circ$.

Now recall from earlier: $\angle BAQ = x = \angle PQC$

But from triangle $ABQ$, we have:

$$
x + B + \angle AQB = 180^\circ
$$

We now know $B = 55^\circ$, $\angle AQB = 125^\circ - x$, so:

$$
x + 55^\circ + (125^\circ - x) = 180^\circ \Rightarrow 55^\circ + 125^\circ = 180^\circ \Rightarrow 180^\circ = 180^\circ
$$

Consistent.

But we still need to find $x = \angle PQC$.

Wait — we have more information.

From triangle $ABQ$, we can find $\angle AQB$ if needed, but we don’t have enough to find $x$ directly.

Wait — we also have similarity $\triangle ABQ \sim \triangle QCP$.

From that, we have:

$$
\angle AQB = \angle QPC
$$

But $\angle QPC$ is an angle in triangle $QPC$.

In triangle $QPC$, we know:

- $\angle QCP = \angle ABQ = B = 55^\circ$ (from similarity)
- $\angle QPC = \angle AQB = 125^\circ - x$
- $\angle PQC = x$

Sum of angles in triangle $QPC$:

$$
\angle QCP + \angle QPC + \angle PQC = 55^\circ + (125^\circ - x) + x = 55^\circ + 125^\circ = 180^\circ
$$

Perfect! It checks out for any $x$. So we haven’t determined $x$ yet.

But we have another relation.

Recall that in triangle $PAQ$, we have:

- $\angle PAQ = B = 55^\circ$
- $\angle APQ = 70^\circ$
- $\angle AQP = C = 55^\circ$

Wait — $\angle AQP = C = 55^\circ$, and $\angle AQP$ is the same as $\angle AQP$ — yes.

But now, in triangle $PAQ$, angles are 55°, 70°, 55° — so it’s isosceles with $AP = PQ$? Not necessary for our purpose.

Now, at point $Q$, we had:

$$
\angle AQC = \angle AQP + \angle PQC = 55^\circ + x
$$

But also, $\angle AQC = 180^\circ - \angle AQB = 180^\circ - (125^\circ - x) = 55^\circ + x$

Which matches — so no new info.

We need another equation.

Wait — perhaps use the fact that $\angle BAQ = x$, and $\angle BAC = 70^\circ$, and $\angle BAC = \angle BAQ + \angle QAC$

So:

$$
\angle QAC = 70^\circ - x
$$

But in triangle $AQC$, we can find angles.

Triangle $AQC$: points $A$, $Q$, $C$.

Angles:

- At $A$: $\angle QAC = 70^\circ - x$
- At $C$: $\angle ACQ = \angle ACB = C = 55^\circ$ (since $Q$ is on $BC$, so angle at $C$ in triangle $AQC$ is same as angle $ACB$)
- At $Q$: $\angle AQC = 55^\circ + x$

Sum: $(70^\circ - x) + 55^\circ + (55^\circ + x) = 70^\circ - x + 55^\circ + 55^\circ + x = 180^\circ$

Again, identity.

So we are stuck — we cannot determine $x$ from this?

But we must be able to, since the problem asks for a numerical answer.

Perhaps I made a mistake in assuming the correspondence in the similarity.

Let me re-examine the similarity $\triangle ABQ \sim \triangle QCP$.

The problem says: $\triangle ABQ \sim \triangle QCP$

This means the correspondence is: A→Q, B→C, Q→P.

So:

- Angle at A corresponds to angle at Q in $\triangle QCP$
- Angle at B corresponds to angle at C in $\triangle QCP$
- Angle at Q corresponds to angle at P in $\triangle QCP$

So:

- $\angle BAQ = \angle CQP$ — which is $\angle PQC$, so yes, $\angle BAQ = \angle PQC = x$
- $\angle ABQ = \angle QCP$ — which is angle at C in $\triangle QCP$, which is $\angle QCP = \angle ACB = C$ (since Q is on BC, so angle at C in triangle QCP is same as angle ACB)
- $\angle AQB = \angle QPC$

But we also have from first similarity that $\angle ACB = C = 55^\circ$, so $\angle QCP = 55^\circ = \angle ABQ$

But $\angle ABQ$ is angle at B in triangle ABQ, which is angle ABC = B = 55^\circ — consistent.

So everything is consistent, but we still don't have a value for $x$.

Wait — perhaps there is another way.

Let me try to find $\angle PQC$ using the fact that in triangle $QPC$, we have angles:

- $\angle QCP = 55^\circ$
- $\angle QPC = \angle AQB = 125^\circ - x$
- $\angle PQC = x$

Sum: 55 + (125 - x) + x = 180 — always true.

But perhaps we can use the Law of Sines in some triangles.

Let me try.

In triangle $ABC$, by Law of Sines:

$$
\frac{AB}{\sin C} = \frac{BC}{\sin A} = \frac{AC}{\sin B}
$$

With $A=70^\circ$, $B=55^\circ$, $C=55^\circ$, so it's isosceles with $AB = AC$? Wait, angles at B and C are both 55°, so sides opposite are equal: side opposite B is AC, opposite C is AB, so yes, $AB = AC$.

So triangle ABC is isosceles with AB = AC.

Now, in triangle PAQ, we have:

- $\angle PAQ = B = 55^\circ$
- $\angle APQ = 70^\circ$
- $\angle AQP = C = 55^\circ$

So triangle PAQ has angles 55°, 70°, 55° — so it's isosceles with AP = PQ? Angles at A and Q are equal, so sides opposite are equal: side opposite A is PQ, opposite Q is AP, so AP = PQ.

So AP = PQ.

Now, from similarity $\triangle ABQ \sim \triangle QCP$, ratio of sides.

But perhaps use Law of Sines in triangle ABQ and triangle QCP.

In triangle ABQ:

- $\angle BAQ = x$
- $\angle ABQ = 55^\circ$
- $\angle AQB = 125^\circ - x$

By Law of Sines:

$$
\frac{AB}{\sin(\angle AQB)} = \frac{BQ}{\sin(x)} = \frac{AQ}{\sin(55^\circ)}
$$

In triangle QCP:

- $\angle QCP = 55^\circ$
- $\angle QPC = 125^\circ - x$
- $\angle PQC = x$

Law of Sines:

$$
\frac{QC}{\sin(\angle QPC)} = \frac{CP}{\sin(x)} = \frac{QP}{\sin(55^\circ)}
$$

But from triangle PAQ, we have AP = PQ.

Also, since AB = AC (from earlier), and P is on AC, let’s set lengths.

Let’s assume AB = AC = 1 for simplicity.

Then in triangle ABC, since AB = AC, and angles at B and C are 55°, angle at A is 70°, so by Law of Sines:

$$
\frac{BC}{\sin 70^\circ} = \frac{AB}{\sin 55^\circ} = \frac{1}{\sin 55^\circ}
$$

So BC = $\frac{\sin 70^\circ}{\sin 55^\circ}$

Now, in triangle ABQ, we have:

$$
\frac{AB}{\sin(\angle AQB)} = \frac{BQ}{\sin(x)} \Rightarrow \frac{1}{\sin(125^\circ - x)} = \frac{BQ}{\sin(x)}
\Rightarrow BQ = \frac{\sin(x)}{\sin(125^\circ - x)}
$$

Similarly, in triangle QCP, we have:

$$
\frac{QC}{\sin(\angle QPC)} = \frac{CP}{\sin(x)} = \frac{QP}{\sin(55^\circ)}
$$

But QP = AP (from triangle PAQ).

Now, AC = AB = 1, and P is on AC, so AC = AP + PC = 1.

Let AP = y, then PC = 1 - y.

But from triangle PAQ, since it's isosceles with AP = PQ, so PQ = y.

So in triangle QCP, we have:

$$
\frac{QP}{\sin(55^\circ)} = \frac{CP}{\sin(x)} \Rightarrow \frac{y}{\sin(55^\circ)} = \frac{1 - y}{\sin(x)}
$$

So:

$$
y \sin(x) = (1 - y) \sin(55^\circ)
\Rightarrow y \sin(x) + y \sin(55^\circ) = \sin(55^\circ)
\Rightarrow y (\sin(x) + \sin(55^\circ)) = \sin(55^\circ)
\Rightarrow y = \frac{\sin(55^\circ)}{\sin(x) + \sin(55^\circ)} \quad \text{(Equation 3)}
$$

Now, also, from triangle ABQ, we have:

BQ = $\frac{\sin(x)}{\sin(125^\circ - x)}$

But QC = BC - BQ = $\frac{\sin 70^\circ}{\sin 55^\circ} - \frac{\sin(x)}{\sin(125^\circ - x)}$

But also, from triangle QCP, we have:

$$
\frac{QC}{\sin(125^\circ - x)} = \frac{QP}{\sin(55^\circ)} = \frac{y}{\sin(55^\circ)}
$$

So:

$$
QC = y \cdot \frac{\sin(125^\circ - x)}{\sin(55^\circ)}
$$

But also, QC = BC - BQ = $\frac{\sin 70^\circ}{\sin 55^\circ} - \frac{\sin(x)}{\sin(125^\circ - x)}$

So set equal:

$$
y \cdot \frac{\sin(125^\circ - x)}{\sin(55^\circ)} = \frac{\sin 70^\circ}{\sin 55^\circ} - \frac{\sin(x)}{\sin(125^\circ - x)}
$$

Multiply both sides by $\sin(55^\circ)$:

$$
y \sin(125^\circ - x) = \sin 70^\circ - \frac{\sin(x) \sin(55^\circ)}{\sin(125^\circ - x)}
$$

Now substitute y from Equation 3:

$$
\left( \frac{\sin(55^\circ)}{\sin(x) + \sin(55^\circ)} \right) \sin(125^\circ - x) = \sin 70^\circ - \frac{\sin(x) \sin(55^\circ)}{\sin(125^\circ - x)}
$$

Multiply both sides by $\sin(x) + \sin(55^\circ)$ to eliminate denominator:

Left side: $\sin(55^\circ) \sin(125^\circ - x)$

Right side: $\sin 70^\circ (\sin(x) + \sin(55^\circ)) - \sin(x) \sin(55^\circ) \cdot \frac{\sin(x) + \sin(55^\circ)}{\sin(125^\circ - x)}$

This is getting messy.

Perhaps try numerical values.

Since we suspect that x might be 35 degrees or something.

Try x = 35°.

Then from Equation 3:

y = sin(55°) / (sin(35°) + sin(55°)) ≈ 0.8192 / (0.5736 + 0.8192) = 0.8192 / 1.3928 ≈ 0.588

Then CP = 1 - y ≈ 0.412

From triangle QCP:

QC = y * sin(125° - 35°) / sin(55°) = 0.588 * sin(90°) / sin(55°) = 0.588 * 1 / 0.8192 ≈ 0.717

BQ = sin(35°)/sin(125° - 35°) = 0.5736 / sin(90°) = 0.5736

BC = BQ + QC = 0.5736 + 0.717 = 1.2906

But from triangle ABC, BC = sin(70°)/sin(55°) = 0.9397 / 0.8192 ≈ 1.147 — not matching.

So x=35 is too big.

Try x=25°.

Then y = sin(55°)/(sin(25°)+sin(55°)) = 0.8192/(0.4226+0.8192)=0.8192/1.2418≈0.6597

CP=1-0.6597=0.3403

QC = y * sin(125-25)/sin(55) = 0.6597 * sin(100°)/sin(55°)

sin(100°)=sin(80°)=0.9848, sin(55°)=0.8192

QC = 0.6597 * 0.9848 / 0.8192 ≈ 0.6597 * 1.201 ≈ 0.792

BQ = sin(25°)/sin(100°) = 0.4226 / 0.9848 ≈ 0.429

BC = 0.429 + 0.792 = 1.221 — still larger than 1.147.

Try x=20°.

y = sin(55)/(sin(20)+sin(55)) = 0.8192/(0.3420+0.8192)=0.8192/1.1612≈0.7056

CP=1-0.7056=0.2944

QC = y * sin(105°)/sin(55) = 0.7056 * sin(105°)/0.8192

sin(105°)=sin(75°)=0.9659

QC = 0.7056 * 0.9659 / 0.8192 ≈ 0.7056 * 1.180 = 0.832

BQ = sin(20)/sin(105) = 0.3420 / 0.9659 ≈ 0.354

BC = 0.354 + 0.832 = 1.186 — still > 1.147

Try x=15°.

y = 0.8192/(sin(15)+sin(55)) = 0.8192/(0.2588+0.8192)=0.8192/1.078=0.760

CP=0.24

QC = 0.760 * sin(110°)/0.8192 = 0.760 * sin(70°)/0.8192 = 0.760 * 0.9397 / 0.8192 ≈ 0.760 * 1.147 = 0.871

BQ = sin(15)/sin(110) = 0.2588 / 0.9397 ≈ 0.275

BC = 0.275 + 0.871 = 1.146 — very close to 1.147!

So x≈15°.

Check with x=15°:

From earlier, BC should be sin(70°)/sin(55°) = 0.9397/0.8192≈1.147

Computed BC=0.275+0.871=1.146 — close enough.

So likely x=15°.

Thus, $\angle PQC = x = 15^\circ$

But let me verify with exact values.

From triangle ABC, with angles 70°, 55°, 55°, so isosceles.

Let AB = AC = 1.

Then BC = sin(70°)/sin(55°)

In triangle ABQ, with angle at A = x, angle at B = 55°, angle at Q = 125° - x.

Law of Sines: AB / sin(angle AQB) = BQ / sin(x)

So 1 / sin(125° - x) = BQ / sin(x) => BQ = sin(x) / sin(125° - x)

In triangle QCP, angle at C = 55°, angle at P = 125° - x, angle at Q = x.

QP = AP, and from triangle PAQ, since angles at A and Q are both 55°, so AP = PQ.

In triangle PAQ, angles: at A: 55°, at P: 70°, at Q: 55°, so yes, AP = PQ.

Let AP = y, then PQ = y, and PC = 1 - y.

In triangle QCP, Law of Sines:

QC / sin(125° - x) = PQ / sin(55°) = y / sin(55°)

So QC = y * sin(125° - x) / sin(55°)

But also, BC = BQ + QC = sin(x)/sin(125° - x) + y * sin(125° - x) / sin(55°)

And BC = sin(70°)/sin(55°)

Also, from triangle PAQ, since it's isosceles with AP = PQ = y, and angle at P is 70°, we can find y in terms of AB.

In triangle PAQ, by Law of Sines:

PQ / sin(55°) = AP / sin(55°) = AQ / sin(70°)

Since AP = PQ, and angles at A and Q are both 55°, so sides opposite are equal, so yes.

But also, AQ is common.

From triangle PAQ, by Law of Sines:

AP / sin(55°) = AQ / sin(70°)

So y / sin(55°) = AQ / sin(70°) => AQ = y * sin(70°) / sin(55°)

Now, in triangle ABQ, we have:

AB / sin(angle AQB) = AQ / sin(55°)

AB = 1, angle AQB = 125° - x, so:

1 / sin(125° - x) = AQ / sin(55°) => AQ = sin(55°) / sin(125° - x)

But from above, AQ = y * sin(70°) / sin(55°)

So:

sin(55°) / sin(125° - x) = y * sin(70°) / sin(55°)

=> y = [sin(55°)]^2 / [sin(125° - x) * sin(70°)]

Now, from earlier, BC = BQ + QC = sin(x)/sin(125° - x) + y * sin(125° - x) / sin(55°)

Substitute y:

BC = sin(x)/sin(125° - x) + [sin(55°)]^2 / [sin(125° - x) * sin(70°)] * sin(125° - x) / sin(55°)

Simplify:

= sin(x)/sin(125° - x) + [sin(55°)]^2 / [sin(70°) * sin(55°)] 

= sin(x)/sin(125° - x) + sin(55°) / sin(70°)

But BC = sin(70°)/sin(55°)

So:

sin(x)/sin(125° - x) + sin(55°)/sin(70°) = sin(70°)/sin(55°)

Let’s compute numerical values:

sin(55°)≈0.8192, sin(70°)≈0.9397

So right side: 0.9397 / 0.8192 ≈ 1.147

Left side: sin(x)/sin(125-x) + 0.8192/0.9397 ≈ sin(x)/sin(125-x) + 0.871

Set equal:

sin(x)/sin(125-x) + 0.871 = 1.147

=> sin(x)/sin(125-x) = 1.147 - 0.871 = 0.276

Now solve sin(x)/sin(125-x) = 0.276

Try x=15°: sin(15°)≈0.2588, sin(110°)≈0.9397, ratio≈0.275 — very close to 0.276

Try x=15.1°: sin(15.1)≈0.260, sin(109.9)≈0.939, ratio≈0.277 — a bit high.

x=15.0° gives 0.2588/0.9397≈0.275, which is very close to 0.276.

Probably intended to be 15°.

So $\angle PQC = x = 15^\circ$

Thus, the answer is:

$$
\boxed{15^\circ}
$$<|im_end|>
```
