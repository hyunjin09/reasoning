"""Outcome-independent intervention diagram, distinct from result figures."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def main():
    root=Path('outputs/stage9a_dynamics/v1/figures');root.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(10,4.7))
    on='#408c70';off='#c05b58'
    for y,label,interval in [(2,'Cumulative cutoff',(0.30,1)),(1,'Local window',(0.50,.60)),(0,'Demand aligned',(.66,.75))]:
        ax.add_patch(Rectangle((0,y),1,.5,color=on))
        ax.add_patch(Rectangle((interval[0],y),interval[1]-interval[0],.5,color=off))
        ax.text(-.20,y+.25,label,ha='right',va='center',fontsize=11)
        ax.add_patch(Rectangle((-.17,y),.14,.5,color='#d2d7dc'))
    ax.annotate('cutoff',xy=(.3,2.5),xytext=(.3,2.8),ha='center',arrowprops={'arrowstyle':'->'})
    ax.annotate('annotated demand',xy=(.705,.5),xytext=(.705,.83),ha='center',arrowprops={'arrowstyle':'->'})
    ax.text(-.10,2.75,'Prefill',ha='center',fontsize=10)
    ax.set_xlim(-.65,1.03);ax.set_ylim(-.25,3.3);ax.set_yticks([])
    ax.set_xticks([0,.25,.5,.75,1],['start','','middle','','native end'])
    ax.set_xlabel('Frozen native reasoning coordinates; continuation can extend beyond native end')
    ax.set_title('Remove direct generated-query → image-key access\nRepository decoder indices 19–22',fontsize=13)
    for spine in ax.spines.values():spine.set_visible(False)
    ax.legend(handles=[Rectangle((0,0),1,1,color=on,label='Access on'),Rectangle((0,0),1,1,color=off,label='Image-key logits = −∞')],loc='upper right',frameon=False)
    fig.text(.5,.015,'Prefill and existing K/V are preserved. Subsequent generated state evolves under the mask. Schematic only.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.03,1,1))
    for ext in ['png','pdf']:fig.savefig(root/f'fig1_intervention_schematic.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__':main()
