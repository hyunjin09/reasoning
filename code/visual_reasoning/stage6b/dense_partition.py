"""Reusable full chunks with exactly the historical per-endpoint query partition."""

def endpoint_partition(end):
    if end<8:raise ValueError('Endpoint requires eight native queries')
    start=end-8;checkpoint=(start//2048)*2048
    partial=[(checkpoint,start)] if start>checkpoint else []
    return checkpoint,partial,[(i,i+1) for i in range(start,end)]
