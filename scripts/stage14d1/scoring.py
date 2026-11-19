"""Offline-only final-answer adapter; never imported by the inference worker."""
from scripts.stage14b.protocol import extract,grade

def score(raw,finish_reason,options,gold_answer):
 parsed=extract(raw,options,'T',finish_reason)
 if parsed['status']!='EXTRACTED':return dict(parsed,final_status='UNSCORABLE_PENDING_RESPONSE_REVIEW',correct=None)
 judged=grade(parsed['answer'],dict(options=options,gold_answer=gold_answer))
 return dict(parsed,final_status=judged['status'],correct=judged['correct'],grader=judged['grader'])
