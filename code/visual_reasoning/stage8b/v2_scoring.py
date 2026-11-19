"""Qwen-compatible response scope and grading, with explicit local extraction.

Pinned upstream: outputs/stage8b/v2/protocol_sources/provenance.json.
No API calls or eval of generated text. Ambiguous cases require blind extraction;
this adapter is not an exact replacement for upstream's GPT-4o fallback.
"""
import re

from .scoring import safe_number


def equivalent(left, right):
    if str(left).lower().strip() == str(right).lower().strip():
        return True
    a, b = safe_number(str(left)), safe_number(str(right))
    return None if a is None or b is None else abs(a - b) < 1e-6


def extract_answer(text, options):
    offset = text.rfind('</think>') + len('</think>') if '</think>' in text else 0
    body = text[offset:].replace('<|im_end|>', ' ' * len('<|im_end|>'))
    result = dict(extracted=None, span=None, scope='post_think' if offset else 'whole_response',
                  method=None, status='needs_blind_extraction')

    def found(value, start, end, method):
        return dict(result, extracted=value, span=[offset+start, offset+end],
                    method=method, status='extracted')

    # Upstream MCQ prefetch: unique standalone letter, then unique choice text.
    if options:
        letters = [chr(65+i) for i in range(len(options))]
        modified = body.translate(str.maketrans({x: ' ' for x in '.()[],:;!*#{}'}))
        words = modified.split()
        candidates = [ch for ch in letters if ch in words]
        rejects = ["Sorry, I can't help with images of people yet.", "I can't process this file.",
                   "I'm sorry, but without the image provided", 'Cannot determine the answer']
        if not any(x in body for x in rejects) and 'Failed to obtain answer via API.' not in body:
            if len(candidates) == 1 and not ('A' in words and len(words) > 3):
                match = next(m for m in re.finditer(r'\S+', modified) if m.group() == candidates[0])
                return found(candidates[0], *match.span(), 'qwen_option_rule')
            matches = [i for i, choice in enumerate(options) if str(choice).lower() in body.lower()]
            if len(matches) == 1:
                i = matches[0]; start = body.lower().index(str(options[i]).lower())
                return found(letters[i], start, start+len(str(options[i])), 'qwen_choice_text_rule')

    # Deterministic explicit-answer adapter before a blind manual fallback.
    starts = list(re.finditer(r'\\(?:boxed|fbox)\s*\{', body))
    if starts:
        start = starts[-1].end(); depth = 1
        for end in range(start, len(body)):
            if body[end] == '{': depth += 1
            elif body[end] == '}': depth -= 1
            if depth == 0:
                return found(body[start:end].strip(), start, end, 'local_balanced_box')
        return result
    markers = list(re.finditer(r'(?:final\s+answer|answer)\s*(?:is\s*|[:=]\s*)([^\n]+)', body, re.I))
    if markers:
        match = markers[-1]
        value = match.group(1).strip().strip('$').rstrip('.').strip()
        if value:
            return found(value, *match.span(1), 'local_explicit_answer')
    plain = body.strip().strip('$').strip()
    if plain and (safe_number(plain) is not None or (options and plain in letters)):
        start = body.index(plain)
        return found(plain, start, start+len(plain), 'local_plain_answer')
    return result


def score_answer(text, row):
    extraction = extract_answer(text, row['options'])
    result = dict(extraction, correct=None, benchmark_label='unscorable',
                  grader='qwen_1e-6_bounded_numeric', external_judge_used=False)
    answer = extraction['extracted']
    if answer is None:
        return result
    if row['options']:
        letters = [chr(65+i) for i in range(len(row['options']))]
        letter = answer.strip().strip('().').upper()
        if letter in letters:
            correct = letter == row['answer']
        else:
            matches = [letters[i] for i, value in enumerate(row['options']) if equivalent(answer, value) is True]
            correct = matches[0] == row['answer'] if len(matches) == 1 else None
    else:
        correct = equivalent(answer, row['answer'])
    if correct is not None:
        result.update(correct=correct, benchmark_label='correct' if correct else 'wrong')
    return result
