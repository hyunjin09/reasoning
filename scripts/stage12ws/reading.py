"""Human-readable exact source material and generated continuations."""
from pathlib import Path
from scripts.stage12ws.common import ROOT,load

def main():
    out=Path('reports/stage12ws/v1');out.mkdir(parents=True,exist_ok=True);links=[]
    families=load(ROOT/'stage12ws_primary_manifest.json')['families']
    for f in families:
        p=out/f"source_{f['item_id']}.md"
        if not p.exists():
            chunks=[f"# Family {f['item_id']}: frozen source blocks",f['question']]
            for b in f['blocks']:
                chunks.extend([f"## B{b['block_id']} · steps {b['start_step']}–{b['end_step']} · {b['role']} · {b['token_count']} tokens",Path(b['path']).read_text()])
            with p.open('x') as w:w.write('\n\n'.join(chunks))
        links.append(f"- [{f['item_id']} source and block boundaries]({p.name})")
    for p in sorted((ROOT/'generations').glob('*/generation.json')):
        g=load(p);t=load(p.parent/'input.json')['task'];dest=out/'responses'/f"{t['task_id']}.md";dest.parent.mkdir(exist_ok=True)
        if not dest.exists():
            with dest.open('x') as w:w.write(f"# {t['task_id']}\n\nFamily {t['item_id']}; condition {t['condition']}; replicate {t['replicate']}; seed {t['seed']}.\n\n{g['tokens']} generated tokens; stop={g['finish_reason']}. Input image-free; source text is supplied assistant prefill, not newly generated reasoning.\n\n## User message\n\n{t['question']}\n\n[Exact prefix](../../../../{t['prefix_path']}) · [Raw token receipt](../../../../{p})\n\n## New continuation\n\n{g['raw_decoded_response']}\n")
        links.append(f"- [{t['task_id']}](responses/{dest.name})")
    (out/'index.md').write_text('# Stage12W-S source and response browser\n\n'+ '\n'.join(links)+'\n')

if __name__=='__main__':main()
