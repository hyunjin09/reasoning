"""Freeze source-derived protocol and comparisons before any sanity output."""
import ast
import re
from pathlib import Path
from scripts.qwen3vl_official_eval.common import ROOT, OLD, load, save, sha, now

REV = '96588727e44c78b25ba03ea03b8e12f7e64fd0da'
BASE = f'https://github.com/QwenLM/Qwen3-VL/blob/{REV}/'
SOURCE = ROOT/'sources/qwen/evaluation/MathVision'

def official_recipe(name):
    text = (SOURCE/name).read_text()
    fields = dict(re.findall(r'--([\w-]+)\s+([\d.]+)', text))
    return {key.replace('-', '_'): (int(value) if key in ['max-new-tokens', 'top-k'] else float(value))
            for key, value in fields.items() if key != 'num-samples'}

def main():
    assert not (ROOT/'results').exists(), 'Audit must precede any sanity output'
    instr = official_recipe('infer_instruct.sh')
    think = official_recipe('infer_think.sh')
    assert instr == dict(max_new_tokens=32768, temperature=.7, top_p=.8, top_k=20,
                         repetition_penalty=1., presence_penalty=1.5)
    assert think == dict(max_new_tokens=40960, temperature=1., top_p=.95, top_k=20,
                         repetition_penalty=1., presence_penalty=0.)
    source = (SOURCE/'run_mathv.py').read_text()
    assert 'seed=42' in source and 'stop_token_ids=[]' in source
    assert '" Let\'s think step by step."' in source
    ast.parse(source)
    records = []
    for name in ['source_fetch_initial.json', 'source_fetch_dependencies.json',
                 'source_fetch_triangulation.json', 'source_fetch_runtime_report.json']:
        records.extend(load(ROOT/'audit'/name))
    sources = dict(at=now(),priority='benchmark script > benchmark README > root generic defaults',
        qwen_head_commit=REV, qwen_head_commit_date='2026-01-30T04:47:30Z',
        source_records=records,
        absence='Qwen evaluation/README.md does not exist at pinned revision; reproduction documentation is root README.',
        official_versions='MathVision requirements are unpinned. Root requires vLLM>=0.11.0, transformers>=4.57.0, qwen-vl-utils>=0.0.14.',
        local_runtime_selection='Isolated .venv/official_eval: vLLM0.11.0, transformers4.57.1, qwen-vl-utils0.0.14; resolved environment recorded separately.',
        dataset=load(ROOT/'audit/dataset_download.json'))
    save(ROOT/'qwen3vl_mathvision_official_sources.json',sources)
    model=load(OLD/'config.json')['models']
    prompt_rows=load(ROOT/'audit/dataset_prompt_image_comparison.json')
    rows=[]
    def add(arm,field,official,old,repaired,match,consequence):
        rows.append(dict(arm=arm,field=field,official=official,stage11c=old,stage11cr=repaired,
            match=match,likely_consequence=consequence))
    for arm,recipe,key in [('instruct_direct',instr,'instruct'),('thinking',think,'thinking')]:
        add(arm,'model_revision','UNSPECIFIED: local model-path placeholder; no SHA',model[key]['revision'],model[key]['revision'],'UNKNOWN','Correct model variant pinned locally; exact unpublished evaluation weight revision cannot be verified.')
        add(arm,'prompt_text','Exact canonical TSV question, including Hint/Question/Choices and original newlines; no added reasoning suffix',
            'HF raw question, removes image placeholders, appends Options with A. labels; no final-answer hint',
            'Same as Stage11C','NO','Different final-answer instruction and option serialization can affect commitment; independent effect not established.')
        add(arm,'system_message','None','None','None','YES','No system-message discrepancy.')
        add(arm,'chat_template','AutoProcessor.apply_chat_template(tokenize=False, add_generation_prompt=True), native variant template',
            'Same call/native variant template','Same call/native variant template','YES','Chat construction matches; question bytes do not.')
        add(arm,'image_formatting','Images first; process_vision_info with processor patch size; canonical TSV JPEG decoded and re-saved',
            'Images first; same vision utility; local HF image export','Same as Stage11C','PARTIAL','Same12 scenes/dimensions, JPEG pixels differ; cannot claim byte-identical inputs.')
        add(arm,'image_resolution',{'min_pixels':602112,'max_pixels':4014080,'patch_size':16},
            {'min_pixels':602112,'max_pixels':4014080,'patch_size':16},
            {'min_pixels':602112,'max_pixels':4014080,'patch_size':16},'YES','Same configured visual resolution bounds.')
        add(arm,'runtime','vLLM (official version unpinned)','HF Transformers5.12.1/Torch2.7.1+cu118','HF Transformers5.12.1/Torch2.7.1+cu118','NO','Kernels, batching and stochastic traces differ.')
        add(arm,'sampling','Stochastic SamplingParams with positive temperature','Greedy','Stochastic','Stage11C:NO; Stage11CR:YES','Greedy repetition was supported on two fixed prior diagnostic cases.')
        for field in ['temperature','top_p','top_k','repetition_penalty','presence_penalty','max_new_tokens']:
            old={'temperature':None,'top_p':None,'top_k':None,'repetition_penalty':1.,'presence_penalty':0.,'max_new_tokens':[4096,8192]}[field]
            repaired={'temperature':1.,'top_p':.95,'top_k':20,'repetition_penalty':1.,'presence_penalty':0.,'max_new_tokens':40960}[field]
            consequence={'presence_penalty':'Official penalty subtracts from generated-token logits after first occurrence; missing anti-repetition pressure is a prospective candidate.',
                'max_new_tokens':'Short old caps censor long outputs; longer cap alone cannot repair a loop.',
                'temperature':'Changes sampling concentration; contribution requires controlled comparison.',
                'top_p':'Changes sampling support; contribution requires controlled comparison.',
                'top_k':'Same20 in repaired run; inactive under prior greedy.',
                'repetition_penalty':'Identity1.0 throughout; distinct from presence penalty.'}[field]
            add(arm,field,recipe[field],old,repaired,f'Stage11C:{old==recipe[field]}; Stage11CR:{repaired==recipe[field]}',consequence)
        add(arm,'eos_stopping','Explicit extra stop IDs=[]; no stop strings; vLLM ignore_eos=False plus model EOS IDs',
            'HF model EOS[151645,151643], cap and wall safeguard','Same EOS IDs, cap and wall safeguard','SEMANTIC MATCH','Empty extra-stop list does not disable EOS; wall interruption is distinct from cap hit.')
        add(arm,'seed','LLM seed42; SamplingParams seed=None','No explicit call seed (greedy)','Frozen per-item seed/reset','NO','Official global runtime seed differs from project item seeds and root README.')
        add(arm,'batch_behavior','All inputs submitted to vLLM dynamic batching','Batch1','Batch1','NO','Throughput and stochastic scheduling differ; no token-identity claim across runtimes.')
        add(arm,'attention_backend','Not explicitly set; vLLM/hardware default','SDPA text/vision','Eager text, SDPA vision','UNKNOWN/DIFFERENT PATH','Backend numerical and performance effects remain potential contributors.')
        add(arm,'tensor_parallelism','Default visible GPU count;1 with one allocated GPU','1','1','MATCH WHEN TP1','2B fits single GPU; no cross-node collective needed.')
        add(arm,'max_model_length',128000,262144,262144,'NO','Output+prompt lengths are below both; verify no context truncation.')
        add(arm,'dtype','LLM default auto, resolved from model config BF16','BF16','BF16','EXPECTED YES','Record observed runtime dtype before inference.')
        add(arm,'answer_extraction','Save raw and post-last-</think> response; downstream rule/gold-prefetch then optional GPT judge',
            'Manual committed-final review and local answer scoring','Completion-only manual review, no correctness scoring','NO','Postprocessing changes measurement, not generation; no external judge will run here.')
    diff=dict(at=now(),official=dict(instruct_direct=instr,thinking=think),rows=rows,
        conflicts=[dict(field='Thinking temperature',script=1.0,benchmark_readme=1.0,root_readme=.6,chosen=1.0),
                   dict(field='engine seed',script=42,root_instruct=3407,root_thinking=1234,chosen=42),
                   dict(field='max_new_tokens help text',parser_default=32768,stale_help=2048,chosen='Use explicit shell scripts')],
        technical_report='Appendix B.1 uses image+question for MathVision. Section5.11 sampling values are TEXT-CENTRIC evaluation settings, not a replacement MathVision protocol.',
        fairness='Fair native comparison means each model variant under its validated intended recipe, not identical decoding hyperparameters. Later oracle would equalize evidence content while preserving model-appropriate decoding.',
        prospective_ablation=[dict(name='no_presence',changes={'presence_penalty':0.0}),
            dict(name='thinking_sampling',changes={'temperature':1.0,'top_p':.95},factor='joint historical sampling recipe, not isolated temperature vs top-p'),
            dict(name='long_budget',changes={'max_new_tokens':40960})],
        ablation_rule='Only if official Instruct gate passes; same12, fixed order/runtime/input/seed; no accuracy. At most these3 variants and within hard3GPUh.')
    save(ROOT/'qwen3vl_mathvision_protocol_diff.json',diff)
    prompt=['# Exact MathVision prompt audit\n',
        f'Source: [{REV[:12]} run_mathv.py]({BASE}evaluation/MathVision/run_mathv.py). Canonical TSV MD593f6de14f7916e598aa1b7165589831e verified.\n',
        'Direct adds no reasoning suffix, but canonical question text already contains an answer-format hint. Therefore D is image + canonical TSV question, not necessarily image + raw HF question. No system message. Images precede one text item. Native chat template is applied with tokenize=False and add_generation_prompt=True.\n',
        'CoT uses the same selected checkpoint and appends exactly `" Let\'s think step by step."` to the last user text element when --use-cot is true. It does not switch checkpoints. Our planned old CoT suffix was `Think step by step before answering.`; no CoT generation is authorized in this audit.\n',
        'Canonical TSV contains actual newline characters (zero literal backslash-n sequences in the12 questions). Item409 retains an <image1> text placeholder. Preserve these exact bytes. Canonical JPEGs represent the same12 items but are not pixel-identical to our HF exports; original files remain untouched.\n']
    for r in prompt_rows:
        prompt += [f"## Item {r['item_id']}\n",'Official stored text (Python repr makes escapes visible):\n',f"```text\n{r['official_question']!r}\n```\n",'Project text:\n',f"```text\n{r['project_question']!r}\n```\n"]
    (ROOT/'qwen3vl_mathvision_prompt_diff.md').write_text('\n'.join(prompt))
    report=[f'# Official Qwen3-VL MathVision protocol audit\n\nAudit frozen {now()}; Qwen commit {REV}. No sanity outputs existed at audit freeze.\n',
        '## A. Official protocol\n',
        f'Primary sources: [Instruct script]({BASE}evaluation/MathVision/infer_instruct.sh), [Thinking script]({BASE}evaluation/MathVision/infer_think.sh), [runtime]({BASE}evaluation/MathVision/run_mathv.py), [dataset loader]({BASE}evaluation/MathVision/dataset_utils.py), [benchmark README]({BASE}evaluation/MathVision/README.md), [root defaults]({BASE}README.md#evaluation-reproduction).\n',
        '| Variant | Temperature | top-p | top-k | Repetition | Presence | Max output |\n|---|---:|---:|---:|---:|---:|---:|\n| Instruct Direct |0.7|0.8|20|1.0|1.5|32768|\n| Thinking |1.0|0.95|20|1.0|0.0|40960|\n',
        'Prompt: one user message, images first, exact canonical TSV question last, no system or added reasoning instruction. The stored TSV includes final-answer hints and Choices formatting, with original newlines and literal image placeholders. CoT optionally appends `" Let\'s think step by step."` on the same Instruct checkpoint. Full12 prompt pairs are in qwen3vl_mathvision_prompt_diff.md.\n',
        'Runtime: vLLM LLM; AutoProcessor from model path; apply_chat_template(tokenize=False,add_generation_prompt=True); qwen-vl-utils process_vision_info uses processor patch size16 and returns multimodal inputs. Pixel bounds602112–4014080; canonical JPEG decode/save. LLM uses seed42, TP=visible GPU count, memory fraction0.9, max_model_len128000, max10 images/prompt, trust_remote_code=True. Model/tokenizer/processor revisions and attention backend are unspecified. Packages are unpinned, except root minimum versions. This audit pins existing2B snapshots and an isolated vLLM0.11.0 runtime; it does not claim the exact unpublished paper environment.\n',
        'SamplingParams receives only temperature,top_p,top_k,max_tokens,repetition_penalty,presence_penalty and stop_token_ids=[]. Under pinned vLLM0.11.0 the remaining defaults include n=1,frequency_penalty=0,min_p=0,min_tokens=0,seed=None,stop=None,ignore_eos=False,skip_special_tokens=True,include_stop_str_in_output=False; no beam search/logprobs. Model generation configuration supplies EOS handling (local151645/151643). No explicit stop string or added EOS override. The LLM engine seed is42, not a per-item SamplingParams seed.\n',
        'Raw text is saved as gen_raw; gen is text after the last </think>, stripped. Evaluation is separate: rule-based extraction with gold-aware prefetch first, then optional GPT judge extraction, followed by answer equivalence. It does not impose an inference-time stop at </think>. This technical audit runs no judge or accuracy-based protocol selection.\n',
        'Conflict register: MathVision Thinking temperature1.0 versus root0.6; engine seed42 versus root Instruct3407/Thinking1234. Benchmark README agrees with shell generation settings. Parser max_new_tokens default32768 has stale help text2048. Use benchmark-specific scripts. Technical-report Appendix B.1 corroborates image+question; its different small-Instruct/dense-Thinking settings in section5.11 belong to text-centric tasks.\n',
        '## B. Project differences\n']
    for arm in ['instruct_direct','thinking']:
        report += [f'### {arm}\n','| Field | Official | Stage11C | Stage11C-R | Match? | Likely consequence |\n|---|---|---|---|---|---|']
        for r in rows:
            if r['arm']==arm:
                report.append('| '+' | '.join(str(r[k]).replace('|','/').replace('\n',' ') for k in ['field','official','stage11c','stage11cr','match','likely_consequence'])+' |')
    report += ['\n## Triangulation\n',
        'VLMEvalKit commit88ba5e79daf1a4be1b9df748a593adfc903a6557 config selects vLLM, use_custom_prompt=False for2B Instruct/Thinking. Instruct sampling/presence matches Qwen but max_new_tokens16384 differs; Thinking1/.95/20/presence0/40960 matches. The generic Qwen prompt mixin can add concise-answer instructions when enabled, but these named presets disable it. MathVision inherits the base dataset prompt using its already-formatted TSV question. HF generation path does not pass presence_penalty, unlike its vLLM path.\n',
        'lmms-eval commitc59eb48ee9e5bfdf2bfd6ad97fa1aba5c9eef18f standard MathVision task uses max_new_tokens16384. Its utility prepends a step-by-step/boxed-answer instruction and serializes choices differently; the simple Qwen3-VL adapter defaults to a helpful-assistant system message and greedy generation, accepts sampling overrides but does not forward presence/repetition penalties in its generation whitelist. These are not the canonical Qwen MathVision Direct recipe. No generic framework configuration replaces the official scripts.\n',
        '## C–E. Prospective validation and decision\n',
        'Use exactly original12 nonprimary IDs in their frozen order, both model variants, canonical TSV prompt and image loader, and model-specific official settings. Final technical metrics will be in qwen3vl_official_sanity_summary.md. Gate unchanged: Instruct finals>=10/12,caps<=1/12,pathologies<=1/12; incomplete/runtime-unfaithful reproduction is UNRESOLVED. Do not interpret cap hits as incorrect. No correctness evaluation is necessary.\n',
        'If Instruct passes, run only the prospectively declared no_presence, thinking_sampling and long_budget variants on the same12, resources permitting; use completion/repetition only. The sampling variant changes temperature and top-p as one historical bundle, so it cannot isolate them individually. If all baseline outputs end below32768, increasing only cap cannot affect their prefixes; record this limit. Do not add a prompt ablation or another candidate after outcomes.\n',
        'Established now: both prompt and runtime/decoding differ from Qwen benchmark code; the historical recipe applied Thinking-like settings to Instruct and lacked its presence penalty. Cause of severe looping remains unresolved until bounded evidence. A favorable sanity result validates the official operating regime, not a unique cause.\n',
        '**Fair native comparison does not require identical decoding hyperparameters. Each variant should use its validated intended evaluation recipe. An eventual oracle can equalize evidence content while retaining model-appropriate decoding.** No scientific rerun is authorized here.\n']
    (ROOT/'qwen3vl_mathvision_official_protocol_audit.md').write_text('\n'.join(report))
    preserve={}
    for old in [Path('outputs/stage11c/v1'),OLD]:
        for p in old.glob('stage11*.json'):preserve[str(p)]=sha(p)
        for p in old.glob('stage11*.md'):preserve[str(p)]=sha(p)
        for p in old.glob('stage11*.parquet'):preserve[str(p)]=sha(p)
    save(ROOT/'audit/audit_freeze.json',dict(at=now(),pre_sanity=True,files={str(ROOT/n):sha(ROOT/n) for n in [
        'qwen3vl_mathvision_official_protocol_audit.md','qwen3vl_mathvision_official_sources.json',
        'qwen3vl_mathvision_protocol_diff.json','qwen3vl_mathvision_prompt_diff.md']},preserved_old=preserve))
    print('OFFICIAL_AUDIT_FROZEN',instr,think)

if __name__=='__main__':main()
