"""Finite intervals using the unchanged validated all-layer standard mask operator."""
from visual_reasoning.stage9a3 import access as established
from scripts.stage10c.protocol import selected_queries

class LocalAccessMask(established.AccessMask):
 def __init__(self,*,visual,prompt_length,intervals,audit=False,mode='standard'):
  super().__init__(backend='qwen3',visual=visual,prompt_length=prompt_length,layers=28,
                   layer_cutoff=28,token_cutoff=None,mode=mode,audit=audit)
  self.intervals=intervals
 def __enter__(self):
  self.old_selector=established.blocked_rows
  established.blocked_rows=lambda layer,start,length,prompt_length,layer_cutoff,token_cutoff:selected_queries(prompt_length,start,length,self.intervals)
  try:return super().__enter__()
  except BaseException:established.blocked_rows=self.old_selector;raise
 def __exit__(self,*exc):
  try:return super().__exit__(*exc)
  finally:established.blocked_rows=self.old_selector
