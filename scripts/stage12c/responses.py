"""Navigable, unabridged C/T response archive without correctness or old labels."""
from pathlib import Path
from scripts.stage12c.common import ROOT,load


def main():
    full=load(ROOT/'stage12c_frozen_bottleneck_manifest.json')
    report=Path('reports/stage12c/v1');report.mkdir(parents=True,exist_ok=True)
    lines=['# Stage12C responses','',
        'Original prompts and complete generated text. Correctness and historical bottleneck labels are omitted from this reading view.',
        'C: prompted CoT,4B Instruct. T: native4B Thinking. The native Thinking text includes its generated `</think>` boundary.','',
        '| MathVision item | C | T | Full responses |','|---|---|---|---|']
    for i in full['sanity_ids']+full['remaining_ids']:
        tasks={a:next(t for t in full['tasks'] if t['item_id']==i and t['arm']==a) for a in 'CT'}
        paths={a:ROOT/'generations'/t['task_id']/'generation.json' for a,t in tasks.items()}
        if not any(p.exists() for p in paths.values()):continue
        body=[f'# MathVision {i}',f"Family: {tasks['C']['family_id']}",'']
        counts={}
        for a in 'CT':
            body.extend([f'## {a} input',tasks[a]['prompt'],'',f'## {a} response'])
            if not paths[a].exists():body.extend(['Pending.','']);counts[a]='pending';continue
            g=load(paths[a]);counts[a]=f"{g['tokens']:,} tokens; {g['finish_reason']}"
            body.extend([counts[a],f'[Immutable raw JSON](../../../{paths[a]})','',
                         '`````text',g['raw_decoded_response'],'`````',''])
        (report/f'{i}.md').write_text('\n'.join(body)+'\n')
        lines.append(f"| {i} | {counts['C']} | {counts['T']} | [Read]({i}.md) |")
    (report/'index.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':main()
