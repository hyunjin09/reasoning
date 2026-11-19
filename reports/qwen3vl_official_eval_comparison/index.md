# Instruct and Thinking: full response comparison

All 12 fixed cases from the official-protocol sanity check. The full emitted responses are preserved, including reasoning, final answers, and capped repetition loops. No new generation or correctness scoring was performed.

Open a paired case page below, or use its two plain-text files with VS Code “Select for Compare” / “Compare with Selected.” The Thinking raw response includes its reasoning and closing `</think>` marker, followed by the final response. Instruct can also emit reasoning despite receiving no explicit CoT instruction.

| Case | Paired page | Instruct full text | Thinking full text | Instruct tokens / stop | Thinking tokens / stop |
|---|---|---|---|---|---|
|2908|[Compare](2908/comparison.md)|[Instruct](2908/instruct.txt)|[Thinking](2908/thinking.txt)|911 / EOS|34870 / EOS|
|651|[Compare](651/comparison.md)|[Instruct](651/instruct.txt)|[Thinking](651/thinking.txt)|647 / EOS|4666 / EOS|
|1146|[Compare](1146/comparison.md)|[Instruct](1146/instruct.txt)|[Thinking](1146/thinking.txt)|32768 / CAP|7822 / EOS|
|1476|[Compare](1476/comparison.md)|[Instruct](1476/instruct.txt)|[Thinking](1476/thinking.txt)|32768 / CAP|31762 / EOS|
|409|[Compare](409/comparison.md)|[Instruct](409/instruct.txt)|[Thinking](409/thinking.txt)|32768 / CAP|24092 / EOS|
|1563|[Compare](1563/comparison.md)|[Instruct](1563/instruct.txt)|[Thinking](1563/thinking.txt)|32768 / CAP|20623 / EOS|
|2214|[Compare](2214/comparison.md)|[Instruct](2214/instruct.txt)|[Thinking](2214/thinking.txt)|32768 / CAP|15628 / EOS|
|725|[Compare](725/comparison.md)|[Instruct](725/instruct.txt)|[Thinking](725/thinking.txt)|301 / EOS|9686 / EOS|
|2981|[Compare](2981/comparison.md)|[Instruct](2981/instruct.txt)|[Thinking](2981/thinking.txt)|1236 / EOS|6392 / EOS|
|750|[Compare](750/comparison.md)|[Instruct](750/instruct.txt)|[Thinking](750/thinking.txt)|5606 / EOS|13511 / EOS|
|1027|[Compare](1027/comparison.md)|[Instruct](1027/instruct.txt)|[Thinking](1027/thinking.txt)|641 / EOS|12120 / EOS|
|469|[Compare](469/comparison.md)|[Instruct](469/instruct.txt)|[Thinking](469/thinking.txt)|1445 / EOS|15738 / EOS|
