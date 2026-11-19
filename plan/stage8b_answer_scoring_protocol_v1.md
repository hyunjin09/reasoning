# Stage8B answer scoring, before census outcomes

Authority checked on2026-09-16: benchmark authors' [evaluate.py](https://github.com/mathllm/MATH-V/blob/main/evaluation/evaluate.py) and [utils.py](https://github.com/mathllm/MATH-V/blob/main/evaluation/utils.py); model authors' [Qwen MathVision evaluator](https://github.com/QwenLM/Qwen3-VL/blob/main/evaluation/MathVision/eval_utils.py).

The primary numeric equivalence rule follows the benchmark-authored evaluator's rounding to two decimal places. MCQ letter or unique equivalent option value is accepted. The model-author implementation instead uses1e-6 and optional external answer extraction; that alternate protocol is not silently substituted for the benchmark rule. The local implementation uses bounded arithmetic parsing, without Python eval or an external judge. Unsupported symbolic expressions, ambiguous option matches and unextractable final answers remain unresolved until manual adjudication.

Answer extraction requires the Thinking final-section boundary `</think>`, then the last balanced boxed expression, an explicit final-answer line or a standalone option letter. It never selects a box from unfinished thinking. Capped trajectories without a final answer are unavailable for usable final-correct/final-wrong comparisons and retained in native accounting. Capped traces with an identifiable final-section answer retain their censoring flag.

This is a conservative local implementation of final-answer assessment, not a claim of byte-identical official evaluator execution. Preserve the extraction/matching method and adjudicate unresolved outputs before using class-yield gates. Rounding, LaTeX normalization, units and percentage conventions must not be changed after observing class yield to obtain a preferred balance.
