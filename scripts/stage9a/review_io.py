"""Display and save explicit single-annotator masked semantic decisions."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path('outputs/stage9a/v1/annotations/review_work')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--start',type=int,default=0);ap.add_argument('--stop',type=int,default=30)
    ap.add_argument('--full',action='store_true');ap.add_argument('--indices',default='');args=ap.parse_args()
    rows=json.loads((ROOT/'masked_events.json').read_text())
    chosen=[rows[int(i)] for i in args.indices.split(',')] if args.indices else rows[args.start:args.stop]
    for row in chosen:
        text=row['excerpt']
        if not args.full:
            center=text.lower().find(row['nomination'].lower())
            if center>=0:
                previous=text.rfind('\n\n',0,center)
                lo=previous+2 if previous>=0 else 0
                hi=text.find('\n\n',center+len(row['nomination']))
                # Include following paragraph if the nominated paragraph is brief.
                if hi>=0 and hi-lo<240:
                    nxt=text.find('\n\n',hi+2);hi=nxt if nxt>=0 else len(text)
                text=text[lo:hi if hi>=0 else len(text)]
        print(json.dumps(dict(i=row['review_index'],image=Path(row['image']).stem,t=row['demand_token'],q=row['question'][:140],text=text),ensure_ascii=False))


if __name__=='__main__':main()
