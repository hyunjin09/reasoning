"""Stage-local verification around the unchanged native runtime."""
from scripts.stage10ar.common import verify_config
from scripts.stage9a5.runtime import load_runtime as old_load,inputs,environment
from scripts.stage10a.runtime import fresh,cached,record,text_inputs,start,resume


def load_runtime():
    cfg=verify_config();old,processor,model=old_load()
    assert cfg['checkpoint']==old['checkpoint'] and cfg['max_total_tokens']==old['max_new_tokens']==512
    return cfg,processor,model
