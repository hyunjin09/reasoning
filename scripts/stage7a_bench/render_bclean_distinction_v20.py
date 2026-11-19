"""Plot preserved local behavioral partitions beside their causal limits."""
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage7a.common import ROOT,read_json,sha,write_json

O=ROOT/'outputs/stage7a_bench_v2'

def main():
    native=O/'analysis/mmmu_pro_complete_native_accounting_20260914_v1.json'
    compatibility=O/'audit/mmmu_bclean_frozen_protocol_compatibility_v1.json'
    pilot=O/'causal_pilot/reports/mmmu_causal_v10_20260915/yield.json'
    a=read_json(native);b=a['paired_behavior_summary'];c=read_json(pilot)
    assert b['paired_universe']['bases']==64 and not b['published_bclean_labels_reproduced']
    assert b['causal_states_assigned'] is False and b['subset_selected'] is False
    keys=['some_absent_condition_correct','both_absent_conditions_wrong','unresolved_absent_conditions']
    counts=[b['partitions'][k]['bases'] for k in keys]
    assert counts==[17,25,22] and sum(counts)==64
    assert c['pilot']['events']==33 and c['strong_faithful']['events']==1 and c['state_counts']['PRIOR_FILL']['certified_events']==0
    fig,axes=plt.subplots(1,2,figsize=(16,8),gridspec_kw={'width_ratios':[1,1.05]})
    plt.rcParams.update({'svg.fonttype':'none','pdf.fonttype':42})
    fig.subplots_adjust(left=.26,right=.96,bottom=.23,top=.78,wspace=.35)
    ax=axes[0];labels=['At least one absent\ncondition correct','Both absent\nconditions wrong','Unresolved absent\nconditions']
    ax.barh(range(3),counts,color=['#377f9d','#b86b42','#82919d'],height=.55)
    ax.set_yticks(range(3),labels);ax.invert_yaxis();ax.set(xlim=(0,32),xlabel='Paired native bases (64 total)')
    ax.set_title('Local behavioral partition',fontsize=14,fontweight='bold',pad=20)
    ax.spines[['top','right']].set_visible(False)
    for i,n in enumerate(counts):ax.text(n+.5,i,f'{n}/64',va='center',fontsize=12)
    ax=axes[1];ax.axis('off');ax.set_title('Causal status remains separate',fontsize=14,fontweight='bold',pad=20)
    lines=[('19 paired bases','Image-present correct; both absent conditions wrong. This is behavioral image advantage.'),
           ('33 selected image-present events','1 certified faithful;24 weaker faithful;8 unresolved. This pilot is a different unit and selection.'),
           ('PRIOR_FILL: 0 certified events','No certified source-null / prior-convergence evidence. No-image correctness is insufficient.'),
           ('Causal B-Clean: not established','The19 behavioral bases are not promoted to a causal cohort.')]
    for y,(title,body) in zip([.99,.74,.47,.22],lines):
        ax.text(0,y,title,va='top',fontsize=12.5,fontweight='bold',transform=ax.transAxes)
        ax.text(0,y-.075,textwrap.fill(body,50),va='top',fontsize=11,linespacing=1.35,transform=ax.transAxes)
    fig.suptitle('Behavioral B-Clean-like accounting does not establish causal B-Clean',x=.04,ha='left',fontsize=18,fontweight='bold')
    fig.text(.04,.135,'Figure12 | Same64 paired bases /62 source families. Unknown and capped outcomes remain unresolved.',fontsize=11.5)
    fig.text(.04,.067,'This is one frozen4B model with reviewed semantic answers. Published multi-model B-Clean labels and its\ndouble-bracket answer parser are not reproduced. No cohort is selected from these behavioral partitions.',fontsize=11,linespacing=1.5,color='#465566')
    dest=O/'analysis/figures/paired_batches/mmmu_bclean_distinction_v20';dest.mkdir(parents=True,exist_ok=False)
    files={}
    for ext in ('png','pdf','svg'):
        p=dest/('12_behavioral_causal_bclean.'+ext);fig.savefig(p,dpi=160,bbox_inches='tight');files[ext]=dict(path=str(p.relative_to(ROOT)),sha256=sha(p))
    plt.close(fig)
    write_json(dest/'manifest.json',dict(status='RENDERED_PENDING_VISUAL_REVIEW',figure_number=12,files=files,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in (native,compatibility,pilot)},
        renderer_sha256=sha(ROOT/'scripts/stage7a_bench/render_bclean_distinction_v20.py'),
        behavioral_counts=dict(zip(keys,counts)),causal_bclean_established=False,subset_selected=False))
    print(dest)

if __name__=='__main__':main()
