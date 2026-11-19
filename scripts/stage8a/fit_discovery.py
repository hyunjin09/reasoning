"""Discovery-only R fitting and G characterization; does not freeze tauG."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage8a.probes import select_discovery, inputs, pipeline


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--measurement-config",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    config=json.loads(args.measurement_config.read_text())
    frozen=json.loads(Path(config["requests"]).read_text())
    assert frozen["split"]=="discovery" and not frozen["preflight_only"]
    assert digest(config["requests"])==config["requests_sha256"]
    directory=Path(config["output_dir"])
    assert json.loads((directory/"wrapper.json").read_text())["completed"]
    by_id={}
    raw_sha={}
    for path in sorted(directory.glob("worker*/events/*.json")):
        event=json.loads(path.read_text())
        assert event["completed"] and event["capture_exact"] and event["self_noop_exact"]
        assert event["split"]=="discovery" and event["event_id"] not in by_id
        by_id[event["event_id"]]=event
        raw_sha[str(path)]=digest(path)
    assert set(by_id)=={r["event_id"] for r in frozen["requests"]}
    events=[by_id[r["event_id"]] for r in frozen["requests"]]
    for event,request in zip(events,frozen["requests"]):
        event["source_role"]=request["source_role"]
        event["demand_kind"]=request["demand_kind"]
        event["demanded_source_vsd"] = event["target_relative_vsd"] if request["source_role"]=="demanded_source" else None
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    fit=select_discovery(events)
    y=np.array([e["label"]=="T" for e in events],dtype=int)
    fitted={}
    for kind,choice in fit["best_by_kind"].items():
        model=pipeline(choice["spec"])
        model.fit(inputs(events,choice["spec"]),y)
        fitted[kind]=dict(model=model,spec=choice["spec"],threshold=choice["operating_point"]["threshold"])
    choice=fit["secondary_sink"]
    model=pipeline(choice["spec"])
    model.fit(inputs(events,choice["spec"]),y)
    fitted["sink_secondary"]=dict(model=model,spec=choice["spec"],threshold=choice["operating_point"]["threshold"])
    joblib.dump(fitted,args.output/"discovery_models.joblib")
    primary=fit["primary"]
    score=np.asarray(primary["oof"])
    js=np.array([e["first_query_js"]["visual_off"] for e in events])
    ce=np.array([e["ce_effect"]["visual_off"] for e in events])
    assert np.isfinite(js).all() and np.isfinite(ce).all() and js.min()>=-1e-14
    t=y==1
    def describe(x):
        return dict(n=len(x),minimum=float(x.min()),maximum=float(x.max()),mean=float(x.mean()),
                    quantiles={str(q):float(np.quantile(x,q)) for q in (0,.1,.25,.5,.75,.9,1)},
                    positive=int((x>0).sum()),zero=int((x==0).sum()),negative=int((x<0).sum()))
    def correlation(x,z):
        if np.ptp(x)==0 or np.ptp(z)==0:
            return None
        return float(spearmanr(x,z).statistic)
    cheap={}
    for key in ("alphaV_ratio","postWO_ratio","residual_ratio","head_cancellation_ratio","head_cosine_disagreement"):
        values=np.array([np.median([r["transport"][key][0] for r in e["passive_current"].values()]) for e in events])
        assert np.isfinite(values).all()
        cheap[key]=dict(values=values.tolist(),spearman_js_all=correlation(values,js),spearman_js_T=correlation(values[t],js[t]),
                        spearman_ce_T=correlation(values[t],ce[t]))
    characterization=dict(T_visual_off_js=describe(js[t]),T_visual_off_ce=describe(ce[t]),
        T_js_ce_spearman=correlation(js[t],ce[t]),numerically_negative_JS=int((js<0).sum()),
        all_event_count=len(events),T_events=int(t.sum()),families=len({e["family_id"] for e in events}),
        labels={label:sum(e["label"]==label for e in events) for label in ("T","M","nearby","nonvisual")},
        source_identifiable=sum(e["source_id"] is not None for e in events),semantic_eligible=sum(e["semantic_eligible"] for e in events),
        demanded_source_identified=sum(e["source_role"]=="demanded_source" for e in events),
        candidate_label_source_only=sum(e["source_role"]=="candidate_label_source" for e in events),
        cheap_transport=cheap,threshold_selected=False,
        caution="A small first-query JS may coexist with a large full evidence-span CE, especially for common leading digits. Inspect both before choosing a transport-weak definition.")
    fig,axs=plt.subplots(2,2,figsize=(12,9),layout="constrained")
    axs[0,0].hist(np.log10(np.clip(js[t],1e-16,None)),bins=12)
    axs[0,0].set(xlabel="log10 visual-off JS (nats; plotting floor1e-16)",ylabel="T events",title="Discovery native transport distribution")
    axs[0,1].scatter(js[t],ce[t]);axs[0,1].set_xscale("symlog",linthresh=1e-12)
    axs[0,1].axhline(0,color="black",lw=.6);axs[0,1].set(xlabel="Visual-off JS",ylabel="Evidence CE(off)-CE(native)",title="Query and span effects")
    for label in ("T","M","nearby","nonvisual"):
        keep=np.array([e["label"]==label for e in events]);axs[1,0].scatter(score[keep],js[keep],label=label,alpha=.7)
    axs[1,0].set_yscale("symlog",linthresh=1e-12);axs[1,0].axvline(primary["operating_point"]["threshold"],color="black",ls="--")
    axs[1,0].set(xlabel="Selected discovery OOF R",ylabel="Visual-off JS",title="No low-G threshold selected yet");axs[1,0].legend()
    kinds=list(fit["best_by_kind"]);vals=[fit["best_by_kind"][k]["metrics"]["auroc"] for k in kinds]
    axs[1,1].barh(kinds,vals);axs[1,1].axvline(.5,color="black",lw=.6);axs[1,1].set(xlim=(0,1),xlabel="Selected discovery OOF AUROC",title="Model-selection metrics; not held-out evidence")
    for suffix in ("png","pdf","svg"):
        fig.savefig(args.output/f"discovery_characterization.{suffix}",dpi=180)
    plt.close(fig)
    provenance=dict(at=datetime.now(timezone.utc).isoformat(),measurement_config=str(args.measurement_config),measurement_config_sha256=digest(args.measurement_config),
        requests=config["requests"],requests_sha256=config["requests_sha256"],raw_sha256=raw_sha,
        source_sha256={str(Path(__file__)):digest(__file__),"code/visual_reasoning/stage8a/probes.py":digest("code/visual_reasoning/stage8a/probes.py")},
        event_order=[e["event_id"] for e in events],families=[e["family_id"] for e in events],
        models_sha256=digest(args.output/"discovery_models.joblib"),confirmation_used=False,low_G_definition_pending=True)
    for name,value in (("retrieval_fit.json",fit),("transport_characterization.json",characterization),("provenance.json",provenance)):
        (args.output/name).write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")
    print(json.dumps(dict(events=len(events),primary=primary["spec"],operating_point=primary["operating_point"],metrics=primary["metrics"],low_G_threshold="pending characterization review"),indent=2))


if __name__=="__main__":
    main()
