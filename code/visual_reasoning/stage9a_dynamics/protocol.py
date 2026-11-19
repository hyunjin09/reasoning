"""Outcome-independent intervention coordinates and exposure-matched controls."""
LAYERS=(19,20,21,22)
CUTOFFS=(0,16,32,64,128,256,512,1024,2048,4096,None)


def cumulative_interval(cutoff):
    return None if cutoff is None else (int(cutoff)+1,None)


def local_windows(start,end):
    assert 0<=start<=end
    return [(start+(k*(end-start))//10,start+((k+1)*(end-start))//10) for k in range(10)]


def demand_control(center,radius,start,end,accepted_centers,rejected_centers):
    lo=max(1,start,center-radius);hi=min(end,center+radius+1)
    if hi<=lo:return None,None
    width=hi-lo;left=max(1,start);last=end-width
    def valid(a):
        return left<=a<=last and all(a+width<=d-32 or a>=d+33 for d in accepted_centers)
    candidates=[int(d)-width//2 for d in sorted(rejected_centers,key=lambda d:(abs(d-center),d))]
    length=end-start
    candidates += [left+((lo-left+int(f*length))%max(1,last-left+1)) for f in (.5,.25,.75)]
    candidates += sorted(range(left,last+1),key=lambda a:(abs(a-candidates[len(rejected_centers)]),a))
    control=next(((a,a+width) for a in candidates if valid(a)),None)
    return (lo,hi),control
