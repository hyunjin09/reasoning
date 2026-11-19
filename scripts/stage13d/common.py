from pathlib import Path
import hashlib,json
from scripts.stage12xs.common import load,save,sha,now,ALLOWED_NODES
ROOT=Path('outputs/stage13d/v1')
OLD=Path('outputs/stage13c/v1')
PREFIX='vr_stage13d_v1_'
CONDITIONS=['I_BASE','I_DERIVED','I_DUMMY','I_SHUFFLED']
ANALYSIS_SEED=120220260929
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def fingerprint(x):return digest(json.dumps(x,sort_keys=True,ensure_ascii=False))
def seed(family,condition,rep):return int(digest(f'stage13d-v1|{family}|{condition}|{rep}'),16)%(2**31)
