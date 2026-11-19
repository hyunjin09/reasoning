"""Seal the reviewed discovery quantile rule before confirmation measurement."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np

from visual_reasoning.stage8a.transport import fit_cheap_gates, transport_values, weak_transport


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    analysis = Path("outputs/stage8a/analysis/discovery_v1")
    assert not Path("outputs/stage8a/measurement/confirmation_v1").exists()
    fit = json.loads((analysis/"retrieval_fit.json").read_text())
    provenance = json.loads((analysis/"provenance.json").read_text())
    assert provenance["confirmation_used"] is False
    records = {}
    for path, sha in provenance["raw_sha256"].items():
        assert digest(path) == sha
        e = json.loads(Path(path).read_text())
        assert e["split"] == "discovery"
        records[e["event_id"]] = e
    events = [records[i] for i in provenance["event_order"]]
    r = np.asarray(fit["primary"]["oof"])
    tau_r = fit["primary"]["operating_point"]["threshold"]
    high = [e for e, score in zip(events, r) if score > tau_r]
    values = np.array([transport_values(e) for e in high])
    rule = dict(tau_js=float(np.quantile(values[:, 0], .25)),
                tau_abs_ce=float(np.quantile(np.abs(values[:, 1]), .25)),
                quantile=.25, threshold_population="discovery primary OOF high-R events",
                high_R_n=len(high), comparison="strict less than both thresholds",
                definition="JS < tau_js AND abs(mean evidence-span CE effect) < tau_abs_ce",
                rationale="Broad continuous/skewed discovery effects span many orders of magnitude; no certified mixture boundary. A lower-quartile region is a conservative relative-low definition. The absolute span guard excludes both strong positive support and strong negative influence, including common-leading-token artifacts. No selection by S or by the 24-event target.",
                interpretation="Relative weakness in layers19-22 at the selected native query/readout; not absence of visual grounding or proven failure")
    models, cheap = fit_cheap_gates(high, rule)
    out = Path("outputs/stage8a/analysis/discovery_freeze_v1")
    assert not out.exists()
    out.mkdir(parents=True)
    joblib.dump(models, out/"cheap_models.joblib")
    (out/"cheap_fit.json").write_text(json.dumps(cheap, indent=2, allow_nan=False)+"\n")
    retrieval = dict(primary_kind=fit["primary"]["spec"]["kind"],
                     spec=fit["primary"]["spec"], tau_R=tau_r,
                     models=str(analysis/"discovery_models.joblib"), fit=str(analysis/"retrieval_fit.json"),
                     provenance=str(analysis/"provenance.json"))
    for key in ("models", "fit", "provenance"):
        retrieval[key+"_sha256"] = digest(retrieval[key])
    freeze = dict(at=datetime.now(timezone.utc).isoformat(), frozen=True, confirmation_used=False,
                  semantic_value_scores_used=False, layers=[19,20,21,22], heads=list(range(16)),
                  retrieval=retrieval, transport=rule,
                  cheap=dict(models=str(out/"cheap_models.joblib"), models_sha256=digest(out/"cheap_models.joblib"),
                             fit=str(out/"cheap_fit.json"), fit_sha256=digest(out/"cheap_fit.json"),
                             preferred=cheap.get("preferred"), training_population="discovery primary OOF high-R",
                             scope="Five separate one-feature logistic probes; log10 norm ratios, raw cosine disagreement; grouped folds; C=.01,.1,1,10; OOF FPR<=.20 operating points. Prefer first norm feature within .02 of best discovery OOF AUROC."),
                  source_sha256={p:digest(p) for p in (str(Path(__file__)),"code/visual_reasoning/stage8a/transport.py")})
    (out/"freeze.json").write_text(json.dumps(freeze, indent=2, allow_nan=False)+"\n")
    print(json.dumps(dict(rule=rule, high_R_low_G=sum(weak_transport(e,rule) for e in high),
                          cheap_preferred=cheap.get("preferred"), freeze=str(out/"freeze.json")),indent=2))


if __name__ == "__main__":
    main()
