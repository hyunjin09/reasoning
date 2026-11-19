from pathlib import Path
from scripts.stage12xs.common import load,save,sha,now,ALLOWED_NODES
from scripts.stage13c.protocol import digest

ROOT=Path('outputs/stage13c/v1')
OLD=Path('outputs/stage13a/v1')
PREFIX='vr_stage13c_v1_'
CONDITIONS=['T_NATIVE','T_SHORT','T_LONG','T_DERIVED','T_DERIVED_DUMMY','I_BASE','I_DERIVED','I_DUMMY','I_SHUFFLED']
FORCED={'T_SHORT','T_LONG','T_DERIVED','T_DERIVED_DUMMY'}


def seed(family,condition,replicate,technical=False):
    ns='stage13c-v1-technical' if technical else 'stage13c-v1'
    return int(digest(f'{ns}|{family}|{condition}|{replicate}'),16)%(2**31)
