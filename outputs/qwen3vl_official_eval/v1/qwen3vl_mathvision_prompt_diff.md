# Exact MathVision prompt audit

Source: [96588727e44c run_mathv.py](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/evaluation/MathVision/run_mathv.py). Canonical TSV MD593f6de14f7916e598aa1b7165589831e verified.

Direct adds no reasoning suffix, but canonical question text already contains an answer-format hint. Therefore D is image + canonical TSV question, not necessarily image + raw HF question. No system message. Images precede one text item. Native chat template is applied with tokenize=False and add_generation_prompt=True.

CoT uses the same selected checkpoint and appends exactly `" Let's think step by step."` to the last user text element when --use-cot is true. It does not switch checkpoints. Our planned old CoT suffix was `Think step by step before answering.`; no CoT generation is authorized in this audit.

Canonical TSV contains actual newline characters (zero literal backslash-n sequences in the12 questions). Item409 retains an <image1> text placeholder. Preserve these exact bytes. Canonical JPEGs represent the same12 items but are not pixel-identical to our HF exports; original files remain untouched.

## Item 2908

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the final answer at the end.\nQuestion: A belt is drawn tightly around three circles of radius $10$ cm each, as shown. The length of the belt, in cm, can be written in the form $a + b\\pi$ for rational numbers $a$ and $b$. What is the value of $a + b$? '
```

Project text:

```text
'A belt is drawn tightly around three circles of radius $10$ cm each, as shown. The length of the belt, in cm, can be written in the form $a + b\\pi$ for rational numbers $a$ and $b$. What is the value of $a + b$?'
```

## Item 651

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the final answer at the end.\nQuestion: On a tall building there are 4 fire escape ladders, as shown. The heights of 3 ladders are at their tops. What is the height of the shortest ladder?'
```

Project text:

```text
'On a tall building there are 4 fire escape ladders, as shown. The heights of 3 ladders are at their tops. What is the height of the shortest ladder?'
```

## Item 1146

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the correct option letter, e.g., A, B, C, D, at the end.\nQuestion: The diagram shows two rectangles whose sides are parallel to each other. By how much is the perimeter of the bigger rectangle greater than the perimeter of the smaller rectangle?\nChoices:\n(A) $12 \\mathrm{~m}$\n(B) $16 \\mathrm{~m}$\n(C) $20 \\mathrm{~m}$\n(D) $21 \\mathrm{~m}$\n(E) $24 \\mathrm{~m}$'
```

Project text:

```text
'The diagram shows two rectangles whose sides are parallel to each other. By how much is the perimeter of the bigger rectangle greater than the perimeter of the smaller rectangle?\n\nOptions:\nA. $12 \\mathrm{~m}$\nB. $16 \\mathrm{~m}$\nC. $20 \\mathrm{~m}$\nD. $21 \\mathrm{~m}$\nE. $24 \\mathrm{~m}$'
```

## Item 1476

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the correct option letter, e.g., A, B, C, D, at the end.\nQuestion: The diagram shows a square $P Q R S$ with side length 1. The point $U$ is the midpoint of the side $R S$ and the point $W$ is the midpoint of the square. The three line segments, $T W, U W$ and $V W$ split the square into three equally big areas. How long is the line segment $S V$?\nChoices:\n(A) $\\frac{1}{2}$\n(B) $\\frac{2}{3}$\n(C) $\\frac{3}{4}$\n(D) $\\frac{4}{5}$\n(E) $\\frac{5}{6}$'
```

Project text:

```text
'The diagram shows a square $P Q R S$ with side length 1. The point $U$ is the midpoint of the side $R S$ and the point $W$ is the midpoint of the square. The three line segments, $T W, U W$ and $V W$ split the square into three equally big areas. How long is the line segment $S V$?\n\nOptions:\nA. $\\frac{1}{2}$\nB. $\\frac{2}{3}$\nC. $\\frac{3}{4}$\nD. $\\frac{4}{5}$\nE. $\\frac{5}{6}$'
```

## Item 409

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the correct option letter, e.g., A, B, C, D, at the end.\nQuestion: In this picture there is what I saw on four different clocks at the same time. Only one of them had the right time. One was 20 minutes fast. Another 20 minutes slow. One had stopped some time ago.\n<image1>\nWhat was the right time?\nChoices:\n(A) 4:45\n(B) 5:05\n(C) 5:25\n(D) 5:40\n(E) 12:00'
```

Project text:

```text
'In this picture there is what I saw on four different clocks at the same time. Only one of them had the right time. One was 20 minutes fast. Another 20 minutes slow. One had stopped some time ago.\n\nWhat was the right time?\n\nOptions:\nA. 4:45\nB. 5:05\nC. 5:25\nD. 5:40\nE. 12:00'
```

## Item 1563

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the final answer at the end.\nQuestion: The diagram shows a solid with six triangular faces. At each vertex there is a number and two of the numbers are 1 and 5, as shown. For each face the sum of the numbers at the three vertices of each face is calculated, and all the sums are the same. What is the sum of all five numbers at the vertices? '
```

Project text:

```text
'The diagram shows a solid with six triangular faces. At each vertex there is a number and two of the numbers are 1 and 5, as shown. For each face the sum of the numbers at the three vertices of each face is calculated, and all the sums are the same. What is the sum of all five numbers at the vertices?'
```

## Item 2214

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the final answer at the end.\nQuestion: All of the triangles in the diagram below are similar to iscoceles triangle $ABC$, in which $AB=AC$. Each of the 7 smallest triangles has area 1, and $\\triangle ABC$ has area 40. What is the area of trapezoid $DBCE$?'
```

Project text:

```text
'All of the triangles in the diagram below are similar to iscoceles triangle $ABC$, in which $AB=AC$. Each of the 7 smallest triangles has area 1, and $\\triangle ABC$ has area 40. What is the area of trapezoid $DBCE$?'
```

## Item 725

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the final answer at the end.\nQuestion: There are seven squares in the picture. How many more triangles than squares are there in the picture?'
```

Project text:

```text
'There are seven squares in the picture. How many more triangles than squares are there in the picture?'
```

## Item 2981

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the final answer at the end.\nQuestion: The right pyramid shown has a square base and all eight of its edges are the same length. What is the degree measure of angle $ABD$?'
```

Project text:

```text
'The right pyramid shown has a square base and all eight of its edges are the same length. What is the degree measure of angle $ABD$?'
```

## Item 750

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the correct option letter, e.g., A, B, C, D, at the end.\nQuestion: The squares are formed by intersecting the segment $A B$ of $24 \\mathrm{~cm}$ by the broken line $A A_{1} A_{2} \\ldots A_{12} B$ (see the figure). Find the length of $A A_{1} A_{2} \\ldots A_{12} B$.\nChoices:\n(A) $48 \\mathrm{~cm}$\n(B) $72 \\mathrm{~cm}$\n(C) $96 \\mathrm{~cm}$\n(D) $56 \\mathrm{~cm}$\n(E) $106 \\mathrm{~cm}$'
```

Project text:

```text
'The squares are formed by intersecting the segment $A B$ of $24 \\mathrm{~cm}$ by the broken line $A A_{1} A_{2} \\ldots A_{12} B$ (see the figure). Find the length of $A A_{1} A_{2} \\ldots A_{12} B$.\n\nOptions:\nA. $48 \\mathrm{~cm}$\nB. $72 \\mathrm{~cm}$\nC. $96 \\mathrm{~cm}$\nD. $56 \\mathrm{~cm}$\nE. $106 \\mathrm{~cm}$'
```

## Item 1027

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the final answer at the end.\nQuestion: Belinda is making patterns with toothpicks according to the schema of the figure. How many toothpicks does Belinda add to the 30th pattern to make the 31 st?'
```

Project text:

```text
'Belinda is making patterns with toothpicks according to the schema of the figure. How many toothpicks does Belinda add to the 30th pattern to make the 31 st?'
```

## Item 469

Official stored text (Python repr makes escapes visible):

```text
'Hint: Please answer the question and provide the final answer at the end.\nQuestion: Six coins build a triangle (see picture). What is the smallest number of coins that must be moved to create the circle?'
```

Project text:

```text
'Six coins build a triangle (see picture). What is the smallest number of coins that must be moved to create the circle?'
```
