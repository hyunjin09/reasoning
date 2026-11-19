"""Frozen image-free assistant-prefill semantics and deterministic seeds."""
import hashlib
import re
from scripts.stage12us.common import ROOT, load, sha


def seed(family, condition, replicate):
    payload = f'stage12us-v1|{family}|{condition}|{replicate}'
    return int(hashlib.sha256(payload.encode()).hexdigest(), 16) % (2**31)


def canonical(raw_prefix):
    # Remove only checkpoint control wrappers; all whitespace remains unchanged.
    return re.sub(r'</?think>', '', raw_prefix)


def render(processor, question, prefix, target):
    messages = [{'role': 'user', 'content': [{'type': 'text', 'text': question}]}]
    base = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    suffix = '<|im_start|>assistant\n' + ('<think>\n' if target == 'T' else '')
    assert base.endswith(suffix)
    assert all(x not in prefix for x in ['<think>', '</think>', '<|im_start|>', '<|im_end|>'])
    prompt = base + prefix
    ids = processor.tokenizer.encode(prompt, add_special_tokens=False)
    assert not set([151652, 151653, 151655, 151656]).intersection(ids), 'Image/video input forbidden'
    assert not prefix or prompt[-len(prefix):] == prefix
    return dict(messages=messages, chat_prompt=prompt, prompt_token_ids=ids,
                prefix_char_start=len(base), prefix_char_end=len(prompt), image_present=False,
                visual_tokens=0, native_template_suffix=suffix)


def authorize(manifest):
    frozen = load(ROOT/'audit'/f"{manifest['phase']}_execution.json")
    expected = {t['task_id']: t for t in frozen['tasks']}
    assert manifest['frozen'] and manifest['config_sha256'] == sha(ROOT/'config.json')
    assert len({r['task_id'] for r in manifest['rows']}) == len(manifest['rows'])
    assert all(t == expected.get(t['task_id']) for t in manifest['rows'])
    if manifest['phase'] == 'science':
        assert load(ROOT/'stage12us_technical_validation.json')['pass']
        seal = load(ROOT/'audit/source_prefix_seal.json')
        for p,h in seal['hashes'].items(): assert sha(p) == h


def majority(values):
    assert len(values) == 3
    wins = sum(v is True for v in values)
    missing = sum(v is None for v in values)
    if wins >= 2: return True
    if wins + missing < 2: return False
    return None

