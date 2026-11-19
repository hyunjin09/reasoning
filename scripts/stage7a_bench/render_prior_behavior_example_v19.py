"""Figure24: a verified paired behavioral example, without a PRIOR_FILL label."""
import hashlib
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage7a.common import ROOT,read_json,write_json,sha
from scripts.stage7a_bench.image_inputs_v2 import payload,decode

O=ROOT/'outputs/stage7a_bench_v2'

def main():
    report_path=O/'native_screen/reports/mmmu_pro_pilot_bound_native_v15/report.json'
    report=read_json(report_path)
    refs={str(report_path.relative_to(ROOT)):sha(report_path)}
    base='mmmu_pro__test_Psychology_201'
    cases=[]
    source=None
    for condition in ('image_present','silent_no_image','explicit_guess'):
        eid=base+'__'+condition
        owner=next(r for r in report['unit_provenance'] if r['event_id']==eid)
        review_path=ROOT/owner['review_path']
        import json
        review=next(r for r in map(json.loads,review_path.read_text().splitlines()) if r['event_id']==eid)
        directory=O/'native_screen/generations'/owner['native_run_id']/'examples'/eid
        meta=read_json(directory/'input.json');generation=read_json(directory/'generation.json')
        assert sha(directory/'generation.json')==review['generation_sha256']
        for p in (review_path,directory/'input.json',directory/'generation.json',directory/'result.json',directory/'tokens.jsonl'):
            key=str(p.relative_to(ROOT));digest=sha(p)
            assert report['artifact_sha256'][key]==digest
            refs[key]=digest
        if condition=='image_present':
            asset=meta['image_assets'][0]
            assert Path(asset['path']).resolve().is_relative_to('/data/dataset')
            data=payload(asset);assert hashlib.sha256(data).hexdigest()==asset['bytes_sha256']
            source=decode(data);assert hashlib.sha256(source.tobytes()).hexdigest()==asset['decoded_sha256']
            quote=review['claims'][0]['quote']
        elif condition=='silent_no_image':
            assert meta['no_image'] and not meta['visual_token_indices']
            quote=review['claims'][0]['quote'].split('. ',1)[0]+'.'
        else:
            assert meta['no_image'] and not meta['visual_token_indices']
            quote='I cannot determine the answer because the image is not available.'
        assert quote in generation['full_generated_response']
        cases.append(dict(condition=condition,event_id=eid,quote=quote,screen_label=review['screen_label'],
            source_review=review['source_review_note'],native_review=review['review_note'],
            final_correctness=review['final_correctness'],causal_state=None))
    dest=O/'analysis/figures/example_batches/mmmu_prior_behavior_v19'
    dest.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','pdf.fonttype':42})
    fig=plt.figure(figsize=(17,10))
    gs=fig.add_gridspec(3,2,width_ratios=[.72,2.6],left=.04,right=.97,bottom=.19,top=.87,hspace=.32,wspace=.10)
    ax=fig.add_subplot(gs[:,0]);ax.imshow(source);ax.axis('off');ax.set_title('Paired source\nimage-present only',fontsize=12)
    titles=['Image present: literal source description','Silent no-image: unsupported visual assertion','Explicit no-image / guess-mode: abstention']
    notes=['F0 screening candidate; subtype answer remains unadjudicated.',
           'F3 behavioral candidate. No image supplies this shape claim.',
           'F5 screening response; no visual evidence is asserted.']
    colors=['#347f9e','#b66a3f','#53616e']
    for i,(case,title,note,color) in enumerate(zip(cases,titles,notes,colors)):
        ax=fig.add_subplot(gs[i,1]);ax.axis('off');ax.set_facecolor('#f5f7f9')
        ax.text(0,1,title,fontsize=15,fontweight='bold',color=color,va='top',transform=ax.transAxes)
        ax.text(0,.68,textwrap.fill('“'+case['quote']+'”',93),fontsize=13,va='top',linespacing=1.4,transform=ax.transAxes)
        ax.text(0,.03,note,fontsize=11,color='#465566',va='bottom',transform=ax.transAxes)
    fig.suptitle('MMMU-Pro: image availability changes the evidence claim',x=.04,ha='left',fontsize=21,fontweight='bold')
    fig.text(.04,.115,'Figure24 — behavioral illustration; a certified PRIOR_FILL example is unavailable in this sweep.',fontsize=12,fontweight='bold')
    fig.text(.04,.065,'This paired response contrast does not establish causal non-visual reasoning. The image-present read is not certified here.\nAll three final subtype answers remain unadjudicated. Native item004 / test_Psychology_201; quotes verified against saved responses.',fontsize=10.5,color='#465566',linespacing=1.6)
    files={}
    for ext in ('png','pdf','svg'):
        path=dest/('24_image_availability_behavior.'+ext);fig.savefig(path,dpi=160,bbox_inches='tight');files[ext]=dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
    plt.close(fig)
    write_json(dest/'manifest.json',dict(status='RENDERED_PENDING_VISUAL_REVIEW',figure_number=24,files=files,
        cases=cases,asset=asset,source_sha256=refs,renderer_sha256=sha(Path(__file__)),
        causal_PRIOR_FILL_claimed=False,purpose='Preserve informative paired behavior while explicitly documenting the absence of a certified prior-filled example.'))
    print(dest)

if __name__=='__main__':main()
