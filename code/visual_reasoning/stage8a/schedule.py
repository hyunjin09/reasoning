"""Native query/evidence coordinates for sparse exact cached measurements."""


def query_schedule(requests, native_ids, *, past_window=32):
    passive, readout = set(), {}
    for request in requests:
        prefix = request["prefix_token_ids"]
        evidence = request["original_token_ids"]
        p = len(prefix)
        if p < 2 or not evidence or list(native_ids[:p]) != prefix or list(native_ids[p:p+len(evidence)]) != evidence:
            raise ValueError("Request does not align with the native prefix/evidence")
        passive.update(range(max(0,p-1-past_window),p))
        for j in range(len(evidence)):
            readout.setdefault(p-1+j,[]).append((request["event_id"],j))
    if not readout:
        raise ValueError("No measurement requests")
    return dict(passive=passive,readout=readout,last_query=max(readout))
