"""Native Thinking task and response boundaries; no model inference."""
def thinking_prompt(prompt):
    line='Think step by step. You must write intermediate steps.\n'
    assert prompt.count(line)==1
    return prompt.replace(line,'')


def sections(ids,close_id,decode):
    positions=[i for i,t in enumerate(ids) if t==close_id]
    end=positions[0] if positions else len(ids)
    return dict(reasoning_tokens=end,reasoning_text=decode(ids[:end]),
        final_text=decode(ids[end+1:]) if positions else '',
        reasoning_closed=len(positions)==1,closure_count=len(positions))
