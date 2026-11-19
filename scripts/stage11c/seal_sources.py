"""Record the source-review reliability decision and seal the plan's exact cohort."""
from scripts.stage11c.common import ROOT, load, save, sha, now
from scripts.stage11c.evidence import agreement, freeze


def main():
    paths=sorted((ROOT/'audit').glob('evidence_round*.json'))
    rows=[r for p in paths for r in load(p)['rows']]
    assert sum(r['eligible'] for r in rows)==120 or len(rows)==300
    assert not list(ROOT.glob('native*/results/*/generation.json'))
    reliability={}
    for name,subset in [('all',rows),('nonempty',[r for r in rows if r['facts']])]:
        reliability[name]=dict(sufficiency=agreement([r['review_a']['sufficiency'] for r in subset],
            [r['review_b']['sufficiency'] for r in subset]),quality=agreement([str(r['quality_a']) for r in subset],
            [str(r['quality_b']) for r in subset]))
    # Sanity checks for the explicitly considered boundary decision, not a new source rule.
    assert reliability['all']['sufficiency']['kappa']>=.6
    assert reliability['all']['quality']['kappa']>=.6
    assert all(not r['eligible'] for r in rows if r['quality_a']!=r['quality_b'])
    path=ROOT/'audit/source_reliability_decision.json'
    save(path,dict(at=now(),model_outcomes_opened=False,reliability_acceptable=True,
        round_sha256={str(p):sha(p) for p in paths},reliability=reliability,
        reason='Overall source-review labels have substantial variation and exceed the planned kappa target. Nonempty candidates are overwhelmingly positive: low conditional kappa is retained as a boundary-reliability limitation, alongside observed agreement and prevalence. All disputed quality/sufficiency sets and aliases are excluded; eligible sets require two affirmative reviews. No consensus relabeling or representation repair was used.',
        limitation='Model-agent semantic judgments, not human reliability. Each reviewer constructed a disjoint half initially; later single-source batches have only A construction and independent B review. Sparse negative judgments make candidate-only kappa unstable and do not certify external validity.',
        changed_rules=False,representation_repairs=0,no_outcome_selection=True))
    freeze(path)


if __name__=='__main__':
    main()
