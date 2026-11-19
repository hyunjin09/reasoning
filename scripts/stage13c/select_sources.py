"""Seal source-only selection before inspecting historical Thinking traces."""
from scripts.stage13c.common import *
from scripts.stage13c.protocol import select

def main():
    source=OLD/'stage13a_frozen96_manifest.json'; rows=load(source)['rows']
    selected=select(rows); byid={r['family_id']:r for r in rows}
    assert not (ROOT/'stage13c_frozen24_manifest.json').exists()
    save(ROOT/'stage13c_frozen24_manifest.json',dict(at=now(),source=str(source),source_sha256=sha(source),
        selection=selected,rows=[byid[f] for f in selected['scientific']],
        selection_code_sha256=sha('scripts/stage13c/protocol.py'),
        model_outcomes_used=False,source_trace_outcomes_opened=False,generation_started=False))
    save(ROOT/'stage13c_technical4_manifest.json',dict(at=now(),rows=[byid[f] for f in selected['technical']],
        source_sha256=sha(source),scientific=False))
    print('SEALED',len(selected['scientific']),len(selected['technical']))

if __name__=='__main__':main()
