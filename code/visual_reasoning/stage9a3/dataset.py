"""Deterministic attribute-counting scenes; no model-dependent selection."""
import math
import numpy as np

SEED=920260927
COLORS=('red','green','yellow','blue')
SHAPES=('star','circle','triangle','square')


def prompt(query):
    options=', '.join(f'{k}: {v}' for k,v in query['options'].items())
    return (f"How many {query['target']} objects are in the image?\n"
            f'options: {{{options}}}\nThink step by step. You must write intermediate steps.\n'
            'Respond in curly braces format: {A}')


def scene(index):
    rng=np.random.default_rng(np.random.SeedSequence([SEED,index,0]))
    objects=[]
    for j in range(int(rng.integers(6,8))):
        diameter=int(rng.choice([18,24,30,36]));radius=diameter/2
        for _ in range(10000):
            center=rng.uniform(radius+3,253-radius,2).tolist()
            if all(math.dist(center,o['center'])>=radius+o['diameter']/2+6 for o in objects):break
        else:raise RuntimeError('Failed nonoverlapping placement')
        objects.append(dict(object_id=j,color=str(rng.choice(COLORS)),shape=str(rng.choice(SHAPES)),
                            diameter=diameter,angle=int(rng.choice([0,45,90,135])),center=center,
                            quadrant=('upper_' if center[1]>=128 else 'lower_')+('right' if center[0]>=128 else 'left')))
    queries=[]
    for attribute,classes in [('color',COLORS),('shape',SHAPES)]:
        qrng=np.random.default_rng(np.random.SeedSequence([SEED,index,1 if attribute=='color' else 2]))
        counts={c:sum(o[attribute]==c for o in objects) for c in classes}
        target=str(qrng.choice([c for c in classes if 1<=counts[c]<=5]))
        options={chr(65+k):int(v) for k,v in enumerate(qrng.permutation(np.arange(1,6)))}
        queries.append(dict(query_id=f'image{index:03d}_{attribute}',image_id=f'image{index:03d}',
                            attribute=attribute,target=target,count=counts[target],options=options,
                            answer=next(k for k,v in options.items() if v==counts[target])))
    return dict(image_id=f'image{index:03d}',index=index,
                split='primary' if index<32 else 'reserve' if index<48 else 'technical',objects=objects,queries=queries)


def render(row,path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle,Polygon
    fig=plt.figure(figsize=(2.56,2.56),dpi=100,facecolor='white')
    ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,256),ylim=(0,256),aspect='equal');ax.axis('off')
    for o in row['objects']:
        center=np.asarray(o['center']);radius=o['diameter']/2;theta=np.deg2rad(o['angle'])
        if o['shape']=='circle':patch=Circle(center,radius,facecolor=o['color'],edgecolor='none')
        else:
            count={'triangle':3,'square':4,'star':10}[o['shape']]
            angles=np.arange(count)*2*np.pi/count+theta+np.pi/2
            radii=np.full(count,radius)
            if o['shape']=='star':radii[1::2]*=.45
            vertices=center+np.column_stack([np.cos(angles),np.sin(angles)])*radii[:,None]
            patch=Polygon(vertices,closed=True,facecolor=o['color'],edgecolor='none')
        ax.add_patch(patch)
    fig.savefig(path,dpi=100,facecolor='white');plt.close(fig)
    from PIL import Image
    with Image.open(path) as im:rgb=im.convert('RGB')
    assert rgb.size==(256,256);rgb.save(path)
