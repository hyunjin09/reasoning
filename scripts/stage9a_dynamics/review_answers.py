"""Gold-blind literal-review routing and explicit decision ledger; no grading."""
import argparse,json,re
from pathlib import Path
from scripts.stage9a_dynamics.prepare_answers import MAIN,save,sha
from visual_reasoning.stage8b.v2_scoring import extract_answer
from visual_reasoning.stage8b.scoring import safe_number


def terminal_literal(p):
    if not p['normal_eos']:return None
    tail=p['tail'].replace('<|im_end|>','').strip()
    e=extract_answer(tail,[])
    if e['extracted'] is None:return None
    value=e['extracted']; suffix=tail[e['span'][1]:]
    # Only punctuation/TeX display closers may follow a terminal literal.
    if re.sub(r'[\s}$.*\\\[\]()]','',suffix):return None
    if p['options']:
        if value not in [chr(65+i) for i in range(len(p['options']))]:return None
    elif safe_number(value) is None:return None
    # Automated confirmation only, never override the frozen raw extraction.
    if value != p['extraction']['extracted']:return None
    return value


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','show','set','seal']);ap.add_argument('--root',default=str(MAIN));ap.add_argument('--start',type=int,default=0);ap.add_argument('--count',type=int,default=40);ap.add_argument('--decisions');args=ap.parse_args();root=Path(args.root);out=root/'annotations'
    packets=json.loads((out/'answer_packets.json').read_text())['rows'];ledger=out/'answer_decisions.json'
    if args.action=='prepare':
        auto={str(p['review_index']):dict(reviewed_answer=v,method='deterministic_terminal_literal_confirmation',reason='Normal EOS; explicit terminal literal agrees with raw extraction; no substantive suffix') for p in packets if (v:=terminal_literal(p)) is not None}
        save(ledger,dict(policy='Frozen native literal-extraction policy. No solving, gold or outcome inspection. Mechanical terminal confirmation is explicitly distinguished from Codex manual review. Nonterminal/capped/ambiguous answers require manual review; explicit repeated terminal claims at cap may be extracted. Options available, gold/condition hidden.',packets_sha256=sha(out/'answer_packets.json'),decisions=auto))
        print(dict(automatic=len(auto),manual_pending=len(packets)-len(auto)));return
    data=json.loads(ledger.read_text());dec=data['decisions']
    if args.action=='show':
        pending=[p for p in packets if str(p['review_index']) not in dec]
        for p in pending[args.start:args.start+args.count]:
            print(json.dumps(dict(i=p['review_index'],raw=p['extraction']['extracted'],cap=p['at_length_cap'],options=p['options'],tail=p['tail'][-(350 if p['at_length_cap'] else 230):]),ensure_ascii=False))
        print('PENDING',len(pending));return
    if args.action=='set':
        vals=json.loads(args.decisions)
        for k,v in vals.items():
            assert k not in dec
            dec[k]=dict(reviewed_answer=v,method='Codex_literal_packet_review',reason='Literal terminal intent; formatting/units/explicit option label only; unresolved if absent or abandoned')
        ledger.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');return
    assert len(dec)==len(packets),(len(dec),len(packets))
    from datetime import datetime,timezone
    rows=[dict(review_index=p['review_index'],packet_id=p['packet_id'],raw_extracted=p['extraction']['extracted'],changed=dec[str(p['review_index'])]['reviewed_answer']!=p['extraction']['extracted'],**dec[str(p['review_index'])]) for p in packets]
    save(out/'answer_extraction_review_frozen.json',dict(frozen=True,at=datetime.now(timezone.utc).isoformat(),policy=data['policy'],packets_sha256=data['packets_sha256'],ledger_sha256=sha(ledger),gold_or_accuracy_accessed=False,rows=rows,limitations='One Codex annotator; deterministic terminal confirmations separately labeled; writing style may reveal arm; no independent human review'))
    print('SEALED',len(rows))

if __name__=='__main__':main()
