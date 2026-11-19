# Official Qwen3-VL MathVision protocol audit

Audit frozen 2026-09-28T15:56:49.168297+00:00; Qwen commit 96588727e44c78b25ba03ea03b8e12f7e64fd0da. No sanity outputs existed at audit freeze.

## A. Official protocol

Primary sources: [Instruct script](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/evaluation/MathVision/infer_instruct.sh), [Thinking script](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/evaluation/MathVision/infer_think.sh), [runtime](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/evaluation/MathVision/run_mathv.py), [dataset loader](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/evaluation/MathVision/dataset_utils.py), [benchmark README](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/evaluation/MathVision/README.md), [root defaults](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/README.md#evaluation-reproduction).

| Variant | Temperature | top-p | top-k | Repetition | Presence | Max output |
|---|---:|---:|---:|---:|---:|---:|
| Instruct Direct |0.7|0.8|20|1.0|1.5|32768|
| Thinking |1.0|0.95|20|1.0|0.0|40960|

Prompt: one user message, images first, exact canonical TSV question last, no system or added reasoning instruction. The stored TSV includes final-answer hints and Choices formatting, with original newlines and literal image placeholders. CoT optionally appends `" Let's think step by step."` on the same Instruct checkpoint. Full12 prompt pairs are in qwen3vl_mathvision_prompt_diff.md.

Runtime: vLLM LLM; AutoProcessor from model path; apply_chat_template(tokenize=False,add_generation_prompt=True); qwen-vl-utils process_vision_info uses processor patch size16 and returns multimodal inputs. Pixel bounds602112–4014080; canonical JPEG decode/save. LLM uses seed42, TP=visible GPU count, memory fraction0.9, max_model_len128000, max10 images/prompt, trust_remote_code=True. Model/tokenizer/processor revisions and attention backend are unspecified. Packages are unpinned, except root minimum versions. This audit pins existing2B snapshots and an isolated vLLM0.11.0 runtime; it does not claim the exact unpublished paper environment.

SamplingParams receives only temperature,top_p,top_k,max_tokens,repetition_penalty,presence_penalty and stop_token_ids=[]. Under pinned vLLM0.11.0 the remaining defaults include n=1,frequency_penalty=0,min_p=0,min_tokens=0,seed=None,stop=None,ignore_eos=False,skip_special_tokens=True,include_stop_str_in_output=False; no beam search/logprobs. Model generation configuration supplies EOS handling (local151645/151643). No explicit stop string or added EOS override. The LLM engine seed is42, not a per-item SamplingParams seed.

Raw text is saved as gen_raw; gen is text after the last </think>, stripped. Evaluation is separate: rule-based extraction with gold-aware prefetch first, then optional GPT judge extraction, followed by answer equivalence. It does not impose an inference-time stop at </think>. This technical audit runs no judge or accuracy-based protocol selection.

Conflict register: MathVision Thinking temperature1.0 versus root0.6; engine seed42 versus root Instruct3407/Thinking1234. Benchmark README agrees with shell generation settings. Parser max_new_tokens default32768 has stale help text2048. Use benchmark-specific scripts. Technical-report Appendix B.1 corroborates image+question; its different small-Instruct/dense-Thinking settings in section5.11 belong to text-centric tasks.

## B. Project differences

### instruct_direct

| Field | Official | Stage11C | Stage11C-R | Match? | Likely consequence |
|---|---|---|---|---|---|
| model_revision | UNSPECIFIED: local model-path placeholder; no SHA | 89644892e4d85e24eaac8bacfd4f463576704203 | 89644892e4d85e24eaac8bacfd4f463576704203 | UNKNOWN | Correct model variant pinned locally; exact unpublished evaluation weight revision cannot be verified. |
| prompt_text | Exact canonical TSV question, including Hint/Question/Choices and original newlines; no added reasoning suffix | HF raw question, removes image placeholders, appends Options with A. labels; no final-answer hint | Same as Stage11C | NO | Different final-answer instruction and option serialization can affect commitment; independent effect not established. |
| system_message | None | None | None | YES | No system-message discrepancy. |
| chat_template | AutoProcessor.apply_chat_template(tokenize=False, add_generation_prompt=True), native variant template | Same call/native variant template | Same call/native variant template | YES | Chat construction matches; question bytes do not. |
| image_formatting | Images first; process_vision_info with processor patch size; canonical TSV JPEG decoded and re-saved | Images first; same vision utility; local HF image export | Same as Stage11C | PARTIAL | Same12 scenes/dimensions, JPEG pixels differ; cannot claim byte-identical inputs. |
| image_resolution | {'min_pixels': 602112, 'max_pixels': 4014080, 'patch_size': 16} | {'min_pixels': 602112, 'max_pixels': 4014080, 'patch_size': 16} | {'min_pixels': 602112, 'max_pixels': 4014080, 'patch_size': 16} | YES | Same configured visual resolution bounds. |
| runtime | vLLM (official version unpinned) | HF Transformers5.12.1/Torch2.7.1+cu118 | HF Transformers5.12.1/Torch2.7.1+cu118 | NO | Kernels, batching and stochastic traces differ. |
| sampling | Stochastic SamplingParams with positive temperature | Greedy | Stochastic | Stage11C:NO; Stage11CR:YES | Greedy repetition was supported on two fixed prior diagnostic cases. |
| temperature | 0.7 | None | 1.0 | Stage11C:False; Stage11CR:False | Changes sampling concentration; contribution requires controlled comparison. |
| top_p | 0.8 | None | 0.95 | Stage11C:False; Stage11CR:False | Changes sampling support; contribution requires controlled comparison. |
| top_k | 20 | None | 20 | Stage11C:False; Stage11CR:True | Same20 in repaired run; inactive under prior greedy. |
| repetition_penalty | 1.0 | 1.0 | 1.0 | Stage11C:True; Stage11CR:True | Identity1.0 throughout; distinct from presence penalty. |
| presence_penalty | 1.5 | 0.0 | 0.0 | Stage11C:False; Stage11CR:False | Official penalty subtracts from generated-token logits after first occurrence; missing anti-repetition pressure is a prospective candidate. |
| max_new_tokens | 32768 | [4096, 8192] | 40960 | Stage11C:False; Stage11CR:False | Short old caps censor long outputs; longer cap alone cannot repair a loop. |
| eos_stopping | Explicit extra stop IDs=[]; no stop strings; vLLM ignore_eos=False plus model EOS IDs | HF model EOS[151645,151643], cap and wall safeguard | Same EOS IDs, cap and wall safeguard | SEMANTIC MATCH | Empty extra-stop list does not disable EOS; wall interruption is distinct from cap hit. |
| seed | LLM seed42; SamplingParams seed=None | No explicit call seed (greedy) | Frozen per-item seed/reset | NO | Official global runtime seed differs from project item seeds and root README. |
| batch_behavior | All inputs submitted to vLLM dynamic batching | Batch1 | Batch1 | NO | Throughput and stochastic scheduling differ; no token-identity claim across runtimes. |
| attention_backend | Not explicitly set; vLLM/hardware default | SDPA text/vision | Eager text, SDPA vision | UNKNOWN/DIFFERENT PATH | Backend numerical and performance effects remain potential contributors. |
| tensor_parallelism | Default visible GPU count;1 with one allocated GPU | 1 | 1 | MATCH WHEN TP1 | 2B fits single GPU; no cross-node collective needed. |
| max_model_length | 128000 | 262144 | 262144 | NO | Output+prompt lengths are below both; verify no context truncation. |
| dtype | LLM default auto, resolved from model config BF16 | BF16 | BF16 | EXPECTED YES | Record observed runtime dtype before inference. |
| answer_extraction | Save raw and post-last-</think> response; downstream rule/gold-prefetch then optional GPT judge | Manual committed-final review and local answer scoring | Completion-only manual review, no correctness scoring | NO | Postprocessing changes measurement, not generation; no external judge will run here. |
### thinking

| Field | Official | Stage11C | Stage11C-R | Match? | Likely consequence |
|---|---|---|---|---|---|
| model_revision | UNSPECIFIED: local model-path placeholder; no SHA | 33e0ad94c327808ebc7d3bbc97e78e600f1eeecd | 33e0ad94c327808ebc7d3bbc97e78e600f1eeecd | UNKNOWN | Correct model variant pinned locally; exact unpublished evaluation weight revision cannot be verified. |
| prompt_text | Exact canonical TSV question, including Hint/Question/Choices and original newlines; no added reasoning suffix | HF raw question, removes image placeholders, appends Options with A. labels; no final-answer hint | Same as Stage11C | NO | Different final-answer instruction and option serialization can affect commitment; independent effect not established. |
| system_message | None | None | None | YES | No system-message discrepancy. |
| chat_template | AutoProcessor.apply_chat_template(tokenize=False, add_generation_prompt=True), native variant template | Same call/native variant template | Same call/native variant template | YES | Chat construction matches; question bytes do not. |
| image_formatting | Images first; process_vision_info with processor patch size; canonical TSV JPEG decoded and re-saved | Images first; same vision utility; local HF image export | Same as Stage11C | PARTIAL | Same12 scenes/dimensions, JPEG pixels differ; cannot claim byte-identical inputs. |
| image_resolution | {'min_pixels': 602112, 'max_pixels': 4014080, 'patch_size': 16} | {'min_pixels': 602112, 'max_pixels': 4014080, 'patch_size': 16} | {'min_pixels': 602112, 'max_pixels': 4014080, 'patch_size': 16} | YES | Same configured visual resolution bounds. |
| runtime | vLLM (official version unpinned) | HF Transformers5.12.1/Torch2.7.1+cu118 | HF Transformers5.12.1/Torch2.7.1+cu118 | NO | Kernels, batching and stochastic traces differ. |
| sampling | Stochastic SamplingParams with positive temperature | Greedy | Stochastic | Stage11C:NO; Stage11CR:YES | Greedy repetition was supported on two fixed prior diagnostic cases. |
| temperature | 1.0 | None | 1.0 | Stage11C:False; Stage11CR:True | Changes sampling concentration; contribution requires controlled comparison. |
| top_p | 0.95 | None | 0.95 | Stage11C:False; Stage11CR:True | Changes sampling support; contribution requires controlled comparison. |
| top_k | 20 | None | 20 | Stage11C:False; Stage11CR:True | Same20 in repaired run; inactive under prior greedy. |
| repetition_penalty | 1.0 | 1.0 | 1.0 | Stage11C:True; Stage11CR:True | Identity1.0 throughout; distinct from presence penalty. |
| presence_penalty | 0.0 | 0.0 | 0.0 | Stage11C:True; Stage11CR:True | Official penalty subtracts from generated-token logits after first occurrence; missing anti-repetition pressure is a prospective candidate. |
| max_new_tokens | 40960 | [4096, 8192] | 40960 | Stage11C:False; Stage11CR:True | Short old caps censor long outputs; longer cap alone cannot repair a loop. |
| eos_stopping | Explicit extra stop IDs=[]; no stop strings; vLLM ignore_eos=False plus model EOS IDs | HF model EOS[151645,151643], cap and wall safeguard | Same EOS IDs, cap and wall safeguard | SEMANTIC MATCH | Empty extra-stop list does not disable EOS; wall interruption is distinct from cap hit. |
| seed | LLM seed42; SamplingParams seed=None | No explicit call seed (greedy) | Frozen per-item seed/reset | NO | Official global runtime seed differs from project item seeds and root README. |
| batch_behavior | All inputs submitted to vLLM dynamic batching | Batch1 | Batch1 | NO | Throughput and stochastic scheduling differ; no token-identity claim across runtimes. |
| attention_backend | Not explicitly set; vLLM/hardware default | SDPA text/vision | Eager text, SDPA vision | UNKNOWN/DIFFERENT PATH | Backend numerical and performance effects remain potential contributors. |
| tensor_parallelism | Default visible GPU count;1 with one allocated GPU | 1 | 1 | MATCH WHEN TP1 | 2B fits single GPU; no cross-node collective needed. |
| max_model_length | 128000 | 262144 | 262144 | NO | Output+prompt lengths are below both; verify no context truncation. |
| dtype | LLM default auto, resolved from model config BF16 | BF16 | BF16 | EXPECTED YES | Record observed runtime dtype before inference. |
| answer_extraction | Save raw and post-last-</think> response; downstream rule/gold-prefetch then optional GPT judge | Manual committed-final review and local answer scoring | Completion-only manual review, no correctness scoring | NO | Postprocessing changes measurement, not generation; no external judge will run here. |

## Triangulation

VLMEvalKit commit88ba5e79daf1a4be1b9df748a593adfc903a6557 config selects vLLM, use_custom_prompt=False for2B Instruct/Thinking. Instruct sampling/presence matches Qwen but max_new_tokens16384 differs; Thinking1/.95/20/presence0/40960 matches. The generic Qwen prompt mixin can add concise-answer instructions when enabled, but these named presets disable it. MathVision inherits the base dataset prompt using its already-formatted TSV question. HF generation path does not pass presence_penalty, unlike its vLLM path.

lmms-eval commitc59eb48ee9e5bfdf2bfd6ad97fa1aba5c9eef18f standard MathVision task uses max_new_tokens16384. Its utility prepends a step-by-step/boxed-answer instruction and serializes choices differently; the simple Qwen3-VL adapter defaults to a helpful-assistant system message and greedy generation, accepts sampling overrides but does not forward presence/repetition penalties in its generation whitelist. These are not the canonical Qwen MathVision Direct recipe. No generic framework configuration replaces the official scripts.

## C–E. Prospective validation and decision

Use exactly original12 nonprimary IDs in their frozen order, both model variants, canonical TSV prompt and image loader, and model-specific official settings. Final technical metrics will be in qwen3vl_official_sanity_summary.md. Gate unchanged: Instruct finals>=10/12,caps<=1/12,pathologies<=1/12; incomplete/runtime-unfaithful reproduction is UNRESOLVED. Do not interpret cap hits as incorrect. No correctness evaluation is necessary.

If Instruct passes, run only the prospectively declared no_presence, thinking_sampling and long_budget variants on the same12, resources permitting; use completion/repetition only. The sampling variant changes temperature and top-p as one historical bundle, so it cannot isolate them individually. If all baseline outputs end below32768, increasing only cap cannot affect their prefixes; record this limit. Do not add a prompt ablation or another candidate after outcomes.

Established now: both prompt and runtime/decoding differ from Qwen benchmark code; the historical recipe applied Thinking-like settings to Instruct and lacked its presence penalty. Cause of severe looping remains unresolved until bounded evidence. A favorable sanity result validates the official operating regime, not a unique cause.

**Fair native comparison does not require identical decoding hyperparameters. Each variant should use its validated intended evaluation recipe. An eventual oracle can equalize evidence content while retaining model-appropriate decoding.** No scientific rerun is authorized here.
