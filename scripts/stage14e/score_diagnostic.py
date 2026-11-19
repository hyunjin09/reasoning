"""Materialize manual source review, provenance and paired descriptive estimates."""
import csv,json,collections,numpy as np
from scripts.stage14e.common import *
from scripts.stage14d1_pilot.statistics import bootstrap_indices,interval
notes={
'52':'O_context ring wording ambiguous; O_blind correctly places E between innermost walls, confirming a tentative premise. T outputs invent open connections or clock openings; the E chamber is walled off. Predicted crop is near A rather than O/E.',
'107':'Old B label repeats a known name. D_blind repeats generic intersection premise; D_struct falsely says every intersection has a house. T outputs miscount/misbind circle occupancy. One-house crop cannot contain requested all-ring configuration.',
'111':'First2/fourthgray already correctly established. T_context misbinds2to second cell; T_blind/GL only repeat correct first2. Noimage invents5. Crop contains shaded cell but excludes printed entry.',
'211':'Printed22** already explicitly correct in prefix. T_blind/GL cap-hit escaped-newline loop is invalid/uncommitted JSON. Noimage invents arithmetic rows. GLOBAL is appropriate.',
'292':'M is supplied in question; AB/CDlong already asserted though frame reconsidered. Readouts supply no new white-up or fold fact. Crop contains original rectangle panel.',
'333':'Old target asks for an absent label or repeats source-given center premise. T image conditions correctly distinguish grey pairwise lenses and white triple-overlap; not established in prefix. Noimage reverses shading. Crop is only part of needed global overlap.',
'337':'Native arithmetic alignment already correct. O_context is a carry derivation, O_blind falsely putsG in tens column. T image transcription correct but known. Noimage output malformed/repetitive. Crop is one character, not the requested full alignment.',
'407':'All gray cells and dimensions already correctly enumerated. Image records repeat known facts. Noimage4x4wrong. Crop is an arbitrary white cell.',
'436':'Prefix layer coordinates tentative. O_context confirms cube directly below top under its defined coordinate frame; T_context supplies correct1/3/6layercounts, partial layout. Blind and noimage undercount hidden cubes. GLOBAL retained.',
'487':'Prefix19explicitly tentative and requests checking; O_context confirms19. Blind count13wrong. T_context starts correct19but contradictory rowcounts then malformed cap output; do not count. All other T rowcounts wrong. Crop contains third pattern.',
'563':'Six visible kangaroos already confirmed. T_context repeats6; blind/GL5and noimage4wrong. GLOBAL.',
'641':'Generic head-direction replies fail to recover source-order facts. T_blind/GL correctly identify the first encountered fish as green/orange, partially confirms tentative prefix guess; orientation/strand sequence omitted. Address wording broad; sensitivity excludes this permissive partial credit. Noimage blue firstfish wrong.',
'674':'Generic route descriptions do not supply requested layer spans/heights. GL falsely says each width10cm and decreasing layerheight. Local crop excludes full3D/top-view relationship.',
'760':'Generic white-position replies do not expose hidden full layers. T_blind/noimage/GLinvent layer distributions. Crop contains only oblique source, not cross-view structure.',
'937':'D asks central position already available, not bridge adjacency. D_struct center/semantic compass directions correct but incidental literalE/Wclaim differs sourceL/O; no new task-critical topology. T_blind/GL invent6rows or wrong Uru location. Noimage unknown. Crop selects Cang, not central/source network.',
'999':'T_context4black derived from question totals, not visual acquisition. T_blind/GLinvent4x4quadrants and cell coordinates. Noimage template unknown. GLOBAL.',
'1067':'PQlabel/length already given/read. T_context and noimage correctly bindX/YtoABcrossings, correcting native P/QonABconfusion; partial because full shaded-boundary not supplied. T_blind/GLmisbindPXlength/edge. Noimage correctness not evidence of visual acquisition.',
'1207':'O_contextunknown despite image. Other records miscount or misorder ring sectors. Local crop insufficient for three-ring global shade map.',
'1305':'Old nonexistent triangle-label target unresolved. T_context correct depth4confirms tentative premise; T_blind/GLalso preserve step connectivity and endpoints. Noimage depth3wrong. GLOBAL.',
'1477':'Old reads wrongly assign3or2rings to middle finger; actual1. T_context/noimageunknown. Blind/GL2,2,0,0,0wrong; source1,3,1,0,0. Crop includes only part of requested hand.',
'2233':'All boundary coordinates already explicit and correct in prefix. D_context repeats them. D_blind lists correct cyclic coordinates but explicitly calls it a pentagon; D_struct5vertices/6edgeswrong. T_blind invents vertices(2,1)/(4,1)and missesconcavity; GLpartial3correctvertices no newfact. Tiny crop blank outside polygon.',
'2471':'Rectangle overlap shape is a tentative source premise; O_context/O_blind/D_blind/T_context confirm it but do not recover decisive shared-edge bindings. D_structAFGDboundaryfalse. T_blind/noimage/GLwrongendpoint/coincidence bindings. Predicted almostfullimagecrop redundant.',
'2702':'Whitecorner is question-given. AllTpattern statements wrong: truewhiteonlyoddrow AND oddcolumn; no method recovers separatorrows. GLOBAL.',
'2924':'Parallelogram is tentative in prefix; O_context/O_blind/T_context confirm shape but not diagonal endpoints. Blind/noimage/GLvague endpoint lists do not identify required edge pairs or shaded boundary. Crop excludes some diagonal endpoints.'}
root=P/'raw/diagnostic_v1c';manifest=load(P/'manifests/diagnostic_v1c.json');logical={(r['item_id'],r['condition']):r for r in load(root/'read_execution_manifest.json')['logical']};old={r['item_id']:r for r in load(P/'analysis/sava72_joined.json')};src={r['item_id']:r for r in rows('outputs/stage14d1_sava_pilot/v1/data/offline_source_manifest.jsonl')}
labels=list(csv.DictReader(open(P/'annotations/diagnostic_labels_v1.tsv'),delimiter='\t'));assert set(r['item_id'] for r in labels)==set(manifest['families'])
full={'333_T_context','333_T_blind','333_T_GL','337_T_context','337_T_blind','337_T_GL','563_T_context','1305_T_blind','1305_T_GL','2233_D_context','2233_T_context'}
result=[]
for l in labels:
 i=l['item_id']
 for arm in manifest['conditions']:
  code=l[arm];x=logical[i,arm];g=load(x['generation_path']) if x['generation_path'] else None
  assert (code=='A')==(g is None)
  try:parsed=json.loads(g['raw_decoded_response']) if g else None
  except (ValueError,TypeError):parsed=None
  if code=='X':assert g and parsed is None
  result.append({'item_id':i,'family_id':old[i]['family_id'],'condition':arm,'label':code,'useful_correct':int(code in ['U','R']),'new_correct':int(code=='U'),'valid_reinspection':int(code=='R'),'explicit_error_committed':int(code=='W'),'correct_known':int(code=='K'),'unknown_or_incomplete':int(code in ['?','X']),'coverage':'full' if i+'_'+arm in full else 'partial' if code in ['U','R','K'] else 'not_certified','execution_status':x['status'],'generation_path':x['generation_path'],'generation_sha256':sha(x['generation_path']) if g else None,'raw_exact_output':g['raw_decoded_response'] if g else None,'parsed':parsed,'image':old[i]['image'],'image_sha256':old[i]['image_sha256'],'prefix_sha256':old[i]['prefix_sha256'],'source_stratum':src[i]['audit_context_stratum'],'source_reference':'outputs/stage14d0/inventory/source_and_raw_output_manifest.jsonl','notes':notes[i],'reviewer':'single AI, condition visible, development data; final outcomes not used'})
save(P/'annotations/diagnostic_source_review_v1.json',{'at':now(),'codes':{'U':'new correct taskcritical fact','R':'correct reinspection of tentative/incorrect premise','K':'correct but known/given','W':'explicit wrong taskcritical fact','?':'unknown/ambiguous/no identifiable read','I':'derivation/irrelevant','A':'no execution','X':'invalid/truncated readout'},'rows':result})
strata=[src[r['item_id']]['audit_context_stratum'] for r in labels];idx=bootstrap_indices(strata,4000,20261022);arms={};vectors={}
for arm in manifest['conditions']:
 rs=[next(r for r in result if r['item_id']==l['item_id'] and r['condition']==arm) for l in labels];v=np.array([r['useful_correct'] for r in rs]);vectors[arm]=v
 arms[arm]={'assigned':24,'attempted':sum(r['label']!='A' for r in rs),'label_counts':dict(collections.Counter(r['label'] for r in rs)),'useful_correct':int(v.sum()),'rate':float(v.mean()),'bootstrap95':interval(v[idx].mean(1)),'whole_requested_source_certified':sum(r['coverage']=='full' for r in rs)}
contrasts={}
for a,b in [('D_blind','O_context'),('D_blind','D_context'),('T_blind','D_blind'),('T_blind','T_noimage'),('T_GL','T_blind'),('D_struct','D_blind')]:
 d=vectors[a]-vectors[b];contrasts[a+'-'+b]={'difference':float(d.mean()),'bootstrap95':interval(d[idx].mean(1)),'paired_gains':int((d==1).sum()),'paired_losses':int((d==-1).sum())}
selected=sorted(['A','B'],key=lambda a:(-arms['D_blind' if a=='A' else 'D_struct']['useful_correct'],arms['D_blind' if a=='A' else 'D_struct']['label_counts'].get('W',0),a))[0]
save(P/'analysis/diagnostic_results_v1.json',{'at':now(),'arms':arms,'contrasts':contrasts,'initial_candidate_selected':selected,'scope':'development descriptive, not confirmation','permissive_partial_reinspection_sensitivity':'Exclude641: T_blind/GL usefulcorrect falls by1; shape-only benefits also reported as partial; full-readout endpoint separate'})
print(json.dumps({'arms':arms,'contrasts':contrasts,'selected':selected},indent=2))
