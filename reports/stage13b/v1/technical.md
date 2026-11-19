# Stage13B technical validation

All48 calls completed; input/rendering/receipt/backend checks passed.44 scoreable; four pre-outcome caps and one cap-after-final, all from2B Instruct. No technical-set correctness analysis.

| Model | Calls | Scoreable | Cap hits | Median generated tokens | Maximum |
|---|---:|---:|---:|---:|---:|
| 2B_I | 8 | 4 | 5 | 32768.0 | 32768 |
| 2B_T | 8 | 8 | 0 | 8055.5 | 42055 |
| 4B_I | 8 | 8 | 0 | 1540.5 | 11367 |
| 4B_T | 8 | 8 | 0 | 7802.5 | 25992 |
| 8B_I | 8 | 8 | 0 | 934.5 | 4973 |
| 8B_T | 8 | 8 | 0 | 6220.0 | 19346 |

Repeated reasoning is retained as model behavior. One capped response keeps an explicit unretracted final21 and is scoreable. Four capped responses remain unresolved or retract their provisional totals. Their cause is unknown; actual input, sampling/checkpoint receipts passed and GPU activity was observed.

The plan puts its numerical missingness gate on the separate frozen scientific8-family tranche: stop if any24-call scale/mode arm has5or more technical missing outcomes. No gate was lowered and no prompt/cap changed.

Technical allocations134496–134501 are released;1.113889 allocatedGPUh. New scientific initial tranche is submitted with original frozen settings; no paired scientific inference opened.

[Verbatim responses](index.md)
