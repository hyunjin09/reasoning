# Phantom-0 paired behavioral screen

Completed 200-question paired behavioral screen on one frozen 4B model/seed. No actual image or factual image answer exists. Unsupported claims are not adjudicated factual errors. No source-null causality or causal PRIOR_FILL certificate is available. F5 includes uncertainty/abstention; broader caveats can concern generic factual or clinical limitations. Question categories are not independent images or proof of template independence. The overall benchmark sweep and winner selection remain unfinished.

| Measure | Silent no-image | Explicit no-image / guess |
|---|---:|---:|
| Unsupported visual claims | 4/200 (2.0%) | 0/200 (0.0%) |
| F5 uncertainty / abstention | 165/200 (82.5%) | 194/200 (97.0%) |
| Any caveat | 188/200 (94.0%) | 197/200 (98.5%) |
| Explicit/assumed guesses | 5/200 (2.5%) | 2/200 (1.0%) |
| Truncated responses | 0/200 (0.0%) | 1/200 (0.5%) |
| Eligible source-based causal events | 0/200 (0.0%) | 0/200 (0.0%) |

Final accuracy and local factual-error accuracy are unavailable. The two conditions use exactly the same200 question IDs. Confidence is expressed text, not calibrated probability.

Unsupported-claim pairs (full responses reviewed; quotes are excerpts):

- `scene_indoor_005`: silent=True, guess=False. Silent: “yes, there is a computer screen in the shot.” Guess: “it is impossible to determine whether there is a television or computer screen in the shot.”
- `scene_indoor_007`: silent=True, guess=False. Silent: “there are no pets visible indoors.” Guess: “We cannot determine”
- `scene_traffic_004`: silent=True, guess=False. Silent: “There are two people standing on the crosswalk.” Guess: “it is impossible to determine the presence or absence of pedestrians at the crosswalk.”
- `scene_traffic_006`: silent=True, guess=False. Silent: “the red truck is clearly visible in the right lane.” Guess: “it cannot be determined because no image is available”

Raw counts, claim identities, transition counts, exact input/output hashes and scope qualifications: `outputs/stage7a_bench_v2/mirage_prior_track/phantom_behavior.json`.
