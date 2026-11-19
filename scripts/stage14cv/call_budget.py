"""Atomic global attempt reservations, including retries across GPU workers."""
import fcntl
import re
from pathlib import Path
from scripts.stage14c.common import save,now


def reserve(root,panel,task_id,attempt,total_limit=2624,technical_limit=24):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    assert panel in {'R','C','technical'} and re.fullmatch(r'[A-Za-z0-9_]+',task_id) and attempt in {0,1}
    name=f'{panel}__{task_id}__attempt_{attempt}.json'
    with (root/'.reservation.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        existing=list(root.glob('*.json'))
        if (root/name).exists():raise RuntimeError('Call attempt already reserved')
        if len(existing)>=total_limit:raise RuntimeError('Hard total generation-attempt ceiling reached')
        if panel=='technical' and sum(p.name.startswith('technical__') for p in existing)>=technical_limit:
            raise RuntimeError('Hard technical-call ceiling reached')
        save(root/name,dict(at=now(),panel=panel,task_id=task_id,attempt=attempt,
            total_reservation_number=len(existing)+1,total_limit=total_limit,technical_limit=technical_limit,
            rule='Permanent conservative reservation before request submission; failed or interrupted attempts remain counted.'))
    return root/name
