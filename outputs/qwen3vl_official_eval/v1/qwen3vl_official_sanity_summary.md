# Qwen3-VL official MathVision baseline sanity

## A. What Qwen officially does

Pinned source commit `96588727e44c78b25ba03ea03b8e12f7e64fd0da`. [Instruct](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/evaluation/MathVision/infer_instruct.sh), [Thinking](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/evaluation/MathVision/infer_think.sh), [inference and CoT](https://github.com/QwenLM/Qwen3-VL/blob/96588727e44c78b25ba03ea03b8e12f7e64fd0da/evaluation/MathVision/run_mathv.py).

| Arm | Temperature | top-p | top-k | Repetition | Presence | Max output |
|---|---:|---:|---:|---:|---:|---:|
| Instruct Direct |0.7|0.8|20|1.0|1.5|32768|
| Thinking |1.0|0.95|20|1.0|0|40960|

One user message, images first and canonical TSV question last; no system message or added Direct reasoning suffix. The TSV already supplies a final-answer/option-letter hint. CoT appends exactly `" Let's think step by step."` on the same Instruct checkpoint. Root generic Thinking temperature0.6 and seeds3407/1234 conflict with benchmark temperature1.0 and engine seed42; the benchmark code governs.

## B. What our project did differently

| Field | Official Instruct | Stage11C | Stage11C-R |
|---|---|---|---|
| Prompt | Canonical Hint/Question/Choices | Raw question + Options; no hint | Same project prompt |
| Decoding | Sample0.7/top-p0.8/presence1.5 | Greedy/no presence penalty | Sample1.0/top-p0.95/no presence penalty |
| Output cap |32768|4096/8192|40960|
| Runtime |vLLM, dynamic batching, seed42|HF/SDPA,batch1|HF/eager text,batch1,item seed|

The full field-by-field comparison for both models is in qwen3vl_mathvision_official_protocol_audit.md and protocol_diff.json. Original snapshots remain pinned. Canonical and project images have identical dimensions and source identities but slightly different JPEG pixels; old files were preserved. Therefore success of the official bundle alone cannot isolate prompt, penalty, sampling, backend or image-serialization effects.

## C. Technical behavior on the frozen12 cases

| Condition | Calls | Cap hits | EOS/official stop | Committed final | Pathology | Tokens median [Q25,Q75];max |
|---|---:|---:|---:|---:|---:|---|
|official_instruct_direct|12|5|7|7|5|3525.5 [845,32768];32768|
|official_thinking|12|0|12|12|0|14569.5 [9220,21490.2];34870|

Timing: vLLM runs requests concurrently; amortized batch time per case and request completion latency are distinct.

| Condition | Batch seconds | Amortized seconds/case | Median request latency seconds |
|---|---:|---:|---:|
|official_instruct_direct|789.42|65.78|53.15|
|official_thinking|730.45|60.87|333.22|

Raw outputs and native official gen/gen_raw records are preserved. Literal commitments and repetition were reviewed without correctness scoring. Caps were not imputed as wrong. Thinking final commitments require its closing think marker; Direct requires an unretracted answer.

## D. Supported explanation

Established: the prior Direct prompt and generation/runtime configuration were not faithful to the benchmark-specific Qwen recipe. Stage11C-R reproduced the historical project configuration, not the official operating regime.


Conditional single-factor ablations were not run because the official Instruct completion gate did not pass. The official recipe therefore does not establish a remedy on this fixed set. Missing presence penalty remains a historical protocol discrepancy, not an established explanation of the loops. Prompt, model behavior and numerical/runtime interactions remain unresolved; no further tuning or protocol search was performed.

Instruct severe-loop case IDs: 1146, 1476, 409, 1563, 2214. Terminal and fixed midpoint passages plus whole-token repetition descriptors support these labels. The completed outputs can still contain redundant self-correction; the severe-pathology count is not a count of every repeated phrase.

Output format: the seven normally stopped Direct responses contain terminal boxed answers or an explicit final-answer line; all12 Thinking responses close the think section and provide a terminal boxed answer. Direct is unprompted for CoT, not constrained to answer-only text.

Runtime inspection found no concrete mismatch explaining the remaining loops: frozen canonical inputs match, official SamplingParams include the requested presence penalty with EOS enabled, both jobs exit0, and capped outputs reach the exact official cap. The original unpublished package/model revisions and hardware are not specified by Qwen, so residual numerical/runtime effects cannot be excluded. See audit/runtime_faithfulness_review.json.

Historical Stage11C-R Direct had8/12 finals and4/12 caps/loops; official Direct here has7/12 finals and5/12 caps/loops. These are different stochastic/runtime/input configurations, so this comparison does not establish that the official recipe causally worsens behavior.

## E. Scientific rerun decision

Unchanged Instruct gate: at least10/12 committed finals, at most1/12 cap hit, at most1/12 repetition pathology. Result: **OFFICIAL_PROTOCOL_STILL_INVALID**.

Fair comparison means each model variant operates under its validated intended evaluation recipe; it does not require identical decoding settings. A later Equal-Evidence Oracle may share evidence content while preserving model-appropriate decoding. No80-family primary rerun, oracle, CoT generation, reserve or new benchmark was launched.

Allocated compute: **0.571111 GPU-hours**, including startup and any failed attempts; hard3 respected. All stage allocations released. Environment installation and source audit used CPU only.

Limitations:12 fixed cases, one sampled run per condition, execution-agent completion review, canonical JPEG serialization differs slightly from historical exports, and the official repository does not pin its original model/package revisions. Exact installed versions, source commits, model hashes, input hashes and job receipts are retained.

Runtime validation: vLLM0.11.0/Torch2.8.0/Transformers4.57.1 ran BF16 with the automatically selected Flash Attention backend. Both initial jobs failed before generation because the project temporary socket path was too long; shortening only TMPDIR repaired startup. Those failures, the original manifest, and all allocated time are preserved. The runtime-only repair preceded every model output.

OFFICIAL_PROTOCOL_STILL_INVALID — do not rerun Claim 3
