"""E6 (SGB-017): peer-consistency δ¹c on LIARS'-BENCH deceptive vs honest RESPONSES.

The real intentional-deception test E5 (true/false statements) was too weak to
reach. LIARS'-BENCH (`Cadenza-Labs/liars-bench`, gated, click-through) ships
pre-generated MODEL RESPONSES with a clean boolean `deceptive` label, so the
response itself carries a lie/hiding posture — exactly the construct. Because
responses already exist, this is a zero-generation, local, ~$0 run: embed with
the cached small panel and compute δ¹c(deceptive) vs δ¹c(honest), same metric
as E2/E3/E5.

The default config `instructed-deception` is built on azaria-mitchell-cities —
the SAME content as E5 — so E6-vs-E5 isolates "bare false statement" (flat in
E5) from "response delivered as an instructed lie". A positive E6 with a flat
E5 is the cleanest possible evidence the channel tracks deceptive *posture*,
not truth-value.

Run:
    cd topics/shape_of_good_behavior
    ./venv/bin/python3 scripts/peer_sheaf_e6_liars.py --config instructed-deception --n-per-class 1000
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from peer_sheaf_e1 import PANEL, embed_with_model, pick_device  # noqa: E402
from peer_sheaf import fit_all_restriction_maps, panel_residual_summary  # noqa: E402
from peer_hodge import PeerComplex, hodge_decompose, per_edge_norms  # noqa: E402


def length_match_indices(ld, lh, n_bins: int = 20, seed: int = 0):
    """Equalize deceptive/honest counts per length-quantile bin.

    Returns (dec_keep, hon_keep) index arrays into the two classes such that the
    kept subsets have matched response-length marginals. This removes the
    length/templating confound (SGB-019): the geometry is then compared on
    length-comparable responses only.
    """
    ld = np.asarray(ld, dtype=float)
    lh = np.asarray(lh, dtype=float)
    edges = np.quantile(np.concatenate([ld, lh]), np.linspace(0, 1, n_bins + 1))
    edges[-1] += 1.0
    rng = np.random.default_rng(seed)
    dec_keep, hon_keep = [], []
    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        di = np.where((ld >= lo) & (ld < hi))[0]
        hj = np.where((lh >= lo) & (lh < hi))[0]
        k = min(len(di), len(hj))
        if k == 0:
            continue
        rng.shuffle(di)
        rng.shuffle(hj)
        dec_keep.extend(di[:k].tolist())
        hon_keep.extend(hj[:k].tolist())
    return np.array(dec_keep, dtype=int), np.array(hon_keep, dtype=int)


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pooled = 0.5 * (a.var() + b.var()) + 1e-12
    return float((a.mean() - b.mean()) / np.sqrt(pooled))


def welch_t(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    from scipy.stats import ttest_ind

    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    res = ttest_ind(a, b, equal_var=False)
    return float(res.statistic), float(res.pvalue)


def auc(scores_pos: np.ndarray, scores_neg: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    y = np.concatenate([np.ones_like(scores_pos), np.zeros_like(scores_neg)])
    s = np.concatenate([scores_pos, scores_neg])
    return float(roc_auc_score(y, s))


def assistant_text(messages) -> str:
    """Last assistant turn from a LIARS'-BENCH chat-format `messages` list."""
    if not isinstance(messages, list):
        return ""
    for m in reversed(messages):
        if isinstance(m, dict) and m.get("role") == "assistant":
            return str(m.get("content", "")).strip()
    # fallback: last turn
    last = messages[-1] if messages else {}
    return str(last.get("content", "")).strip() if isinstance(last, dict) else ""


def load_liars(config: str, n_per_class: int, seed: int) -> tuple[list[str], list[str]]:
    """Return (deceptive_responses, honest_responses), balanced + subsampled."""
    from datasets import load_dataset

    ds = load_dataset("Cadenza-Labs/liars-bench", config, split="test")
    print(f"[E6] config={config} n={len(ds)} cols={ds.column_names}", flush=True)
    texts = [assistant_text(m) for m in ds["messages"]]
    labels = ds["deceptive"]
    dec_idx, hon_idx = [], []
    for i, (t, lab) in enumerate(zip(texts, labels)):
        if not t:
            continue
        (dec_idx if bool(lab) else hon_idx).append(i)
    rng = np.random.default_rng(seed)
    rng.shuffle(dec_idx)
    rng.shuffle(hon_idx)
    k = min(n_per_class, len(dec_idx), len(hon_idx))
    dec = [texts[i] for i in dec_idx[:k]]
    hon = [texts[i] for i in hon_idx[:k]]
    print(f"[E6] balanced n_per_class={k} (avail deceptive={len(dec_idx)} honest={len(hon_idx)})",
          flush=True)
    return dec, hon


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="instructed-deception")
    parser.add_argument("--n-per-class", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0,
                        help="subsample seed (fixes which examples are embedded)")
    parser.add_argument("--split-seeds", default=None,
                        help="comma list of cal/eval split seeds for multi-seed "
                             "robustness on the SAME embeddings, e.g. '0,1,2,3,4'. "
                             "Default = just --seed.")
    parser.add_argument("--ridge", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument(
        "--cache-dir", default=str(ROOT / "shared" / "data" / "cache" / "peer_sheaf_e6")
    )
    parser.add_argument(
        "--out", default=str(ROOT / "shared" / "results" / "peer_sheaf_e6_liars.json")
    )
    parser.add_argument("--force-reembed", action="store_true")
    parser.add_argument("--length-match", action="store_true",
                        help="equalize deceptive/honest response-length marginals "
                             "(per-quantile-bin) before computing the geometry")
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    device = pick_device()
    print(f"[E6] device={device}", flush=True)

    dec_txt, hon_txt = load_liars(args.config, args.n_per_class, args.seed)
    n = len(dec_txt)
    all_texts = dec_txt + hon_txt  # [deceptive block | honest block]
    tag = args.config.replace("/", "_")

    feats_all: dict[str, np.ndarray] = {}
    for name, hf_id in PANEL:
        cache_path = cache_dir / f"{name}_{tag}_n{n}_seed{args.seed}.npy"
        if cache_path.exists() and not args.force_reembed:
            print(f"[E6] loading cached embeddings: {cache_path.name}", flush=True)
            feats_all[name] = np.load(cache_path)
            continue
        t0 = time.time()
        print(f"[E6] embedding {len(all_texts)} responses with {name}", flush=True)
        feats_all[name] = embed_with_model(
            all_texts, hf_id, device=device,
            batch_size=args.batch_size, max_length=args.max_length,
        ).astype(np.float64)
        np.save(cache_path, feats_all[name])
        print(f"  -> {feats_all[name].shape} saved in {time.time()-t0:.1f}s", flush=True)

    feats_dec = {k: v[:n] for k, v in feats_all.items()}
    feats_hon = {k: v[n:] for k, v in feats_all.items()}

    length_match_info = None
    if args.length_match:
        ld = [len(t) for t in dec_txt]
        lh = [len(t) for t in hon_txt]
        dk, hk = length_match_indices(ld, lh, n_bins=20, seed=args.seed)
        feats_dec = {k: v[dk] for k, v in feats_dec.items()}
        feats_hon = {k: v[hk] for k, v in feats_hon.items()}
        n = len(dk)
        ldm = np.array([ld[i] for i in dk]); lhm = np.array([lh[i] for i in hk])
        length_match_info = {
            "n_after_match": int(n),
            "dec_len_mean_before": float(np.mean(ld)), "hon_len_mean_before": float(np.mean(lh)),
            "dec_len_mean_after": float(ldm.mean()), "hon_len_mean_after": float(lhm.mean()),
        }
        print(f"[E6] length-match: n {len(dec_txt)}→{n}/class  "
              f"len dec {np.mean(ld):.0f}→{ldm.mean():.0f}  hon {np.mean(lh):.0f}→{lhm.mean():.0f}",
              flush=True)

    split_seeds = (
        [int(s) for s in args.split_seeds.split(",")]
        if args.split_seeds else [args.seed]
    )

    def run_one_split(split_seed: int) -> dict:
        rng = np.random.default_rng(split_seed + 1)
        perm = rng.permutation(n)
        cal_idx = perm[: n // 2]
        eval_idx = perm[n // 2 :]
        feats_cal = {
            k: np.concatenate([feats_dec[k][cal_idx], feats_hon[k][cal_idx]], axis=0)
            for k in feats_all
        }
        maps = fit_all_restriction_maps(feats_cal, ridge_lambda=args.ridge)
        cx = PeerComplex.from_features(feats_cal)
        fe_dec = {k: feats_dec[k][eval_idx] for k in feats_all}
        fe_hon = {k: feats_hon[k][eval_idx] for k in feats_all}
        dd = hodge_decompose(cx, fe_dec, maps)
        dh = hodge_decompose(cx, fe_hon, maps)
        d1d, d1h = dd.norm_cocycle_violation, dh.norm_cocycle_violation
        sd = panel_residual_summary(fe_dec, maps, metric="cosine")
        sh = panel_residual_summary(fe_hon, maps, metric="cosine")
        Ld, Lh = sd["L"], sh["L"]
        _, p1 = welch_t(d1d, d1h)
        _, pL = welch_t(Ld, Lh)
        summary = {
            "split_seed": split_seed, "D_V": cx.D_V, "D_E": cx.D_E, "D_F": cx.D_F,
            "delta1c": {
                "deceptive_mean": float(d1d.mean()), "honest_mean": float(d1h.mean()),
                "cohens_d": cohens_d(d1d, d1h), "p_value": p1,
                "auc": auc(d1d, d1h),
            },
            "L_residual": {
                "deceptive_mean": float(Ld.mean()), "honest_mean": float(Lh.mean()),
                "cohens_d": cohens_d(Ld, Lh), "p_value": pL, "auc": auc(Ld, Lh),
            },
        }
        raw = {"complex": cx, "dec": dd, "hon": dh}
        return summary, raw

    t0 = time.time()
    runs = [run_one_split(s) for s in split_seeds]
    splits = [r[0] for r in runs]
    print(f"[E6] ran {len(splits)} split(s) in {time.time()-t0:.1f}s", flush=True)

    # ----- STRUCTURE (on the primary split): WHERE the panel splits, not how much.
    # The goal is a relative pattern of cross-model conceptual divergence, so we
    # report per-edge (pairwise) and per-triangle AUC(deceptive vs honest) using
    # rank stats (robust to the heavy-tailed norm). AUC>0.5 means deceptive
    # responses sit further apart on that edge/triangle than honest ones.
    p_cx = runs[0][1]["complex"]
    p_dd = runs[0][1]["dec"]
    p_hon = runs[0][1]["hon"]
    edge_dec = per_edge_norms(p_cx, p_dd.C)
    edge_hon = per_edge_norms(p_cx, p_hon.C)
    per_edge = {
        f"{i}->{j}": {"auc": auc(edge_dec[(i, j)], edge_hon[(i, j)]),
                      "dec_mean": float(edge_dec[(i, j)].mean()),
                      "hon_mean": float(edge_hon[(i, j)].mean())}
        for (i, j) in p_cx.edge_slices
    }
    per_tri = {}
    for (i, j, k), sl in p_cx.tri_slices.items():
        td = np.linalg.norm(p_dd.cocycle_violation[:, sl], axis=1)
        th = np.linalg.norm(p_hon.cocycle_violation[:, sl], axis=1)
        per_tri[f"{i}->{j}->{k}"] = {"auc": auc(td, th)}
    # per-model: mean AUC over edges incident to each model (as source or dest).
    per_model = {}
    for m in p_cx.models:
        incident = [v["auc"] for key, v in per_edge.items()
                    if key.split("->")[0] == m or key.split("->")[1] == m]
        per_model[m] = {"mean_incident_edge_auc": float(np.mean(incident))}
    structure = {"per_edge": per_edge, "per_triangle": per_tri, "per_model": per_model}

    def agg(key: str, field: str) -> dict:
        vals = np.array([s[key][field] for s in splits], dtype=float)
        return {"mean": float(vals.mean()), "std": float(vals.std()),
                "min": float(vals.min()), "max": float(vals.max())}

    primary = splits[0]
    d1_dec_m = primary["delta1c"]["deceptive_mean"]
    d1_hon_m = primary["delta1c"]["honest_mean"]

    result = {
        "config": {
            "experiment": "E6 (SGB-017)",
            "dataset": f"Cadenza-Labs/liars-bench [{args.config}]",
            "metric": "||δ¹c|| (deceptive high) + L residual",
            "n_per_class": n,
            "n_eval_per_class": int(n - n // 2),
            "seed": args.seed, "split_seeds": split_seeds, "ridge": args.ridge,
            "panel": [
                {"name": nm, "hf_id": h, "hidden_dim": int(feats_all[nm].shape[1])}
                for nm, h in PANEL
            ],
            "complex": {"D_V": primary["D_V"], "D_E": primary["D_E"], "D_F": primary["D_F"]},
            "length_match": length_match_info,
            "note": "responses carry an instructed-lie posture (real deception construct).",
        },
        "delta1c": {
            "deceptive_mean": d1_dec_m, "honest_mean": d1_hon_m,
            "cohens_d_deceptive_vs_honest": primary["delta1c"]["cohens_d"],
            "p_value": primary["delta1c"]["p_value"],
            "auc_deceptive_high": primary["delta1c"]["auc"],
            "across_splits": {
                "cohens_d": agg("delta1c", "cohens_d"),
                "auc": agg("delta1c", "auc"),
            },
        },
        "L_residual": {
            "cohens_d_deceptive_vs_honest": primary["L_residual"]["cohens_d"],
            "p_value": primary["L_residual"]["p_value"],
            "auc_deceptive_high": primary["L_residual"]["auc"],
            "across_splits": {
                "cohens_d": agg("L_residual", "cohens_d"),
                "auc": agg("L_residual", "auc"),
            },
        },
        "per_split": splits,
        "structure": structure,
    }
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(f"[E6] wrote {args.out}", flush=True)

    print(f"\n[E6] STRUCTURE [{args.config}]  per-edge AUC(deceptive vs honest):")
    for key, v in sorted(per_edge.items(), key=lambda kv: -kv[1]["auc"]):
        print(f"    {key:<22s} AUC={v['auc']:.3f}")
    print("  per-model mean incident-edge AUC:")
    for m, v in sorted(per_model.items(), key=lambda kv: -kv[1]["mean_incident_edge_auc"]):
        print(f"    {m:<12s} {v['mean_incident_edge_auc']:.3f}")

    dcd = result["delta1c"]["across_splits"]["cohens_d"]
    dca = result["delta1c"]["across_splits"]["auc"]
    lcd = result["L_residual"]["across_splits"]["cohens_d"]
    print(f"\n[E6] DECEPTIVE vs HONEST  [{args.config}]  "
          f"n/class={n}  splits={len(splits)}")
    print(f"  ||δ¹c||  d={dcd['mean']:+.3f}±{dcd['std']:.3f} "
          f"[{dcd['min']:+.3f},{dcd['max']:+.3f}]  "
          f"AUC={dca['mean']:.3f}±{dca['std']:.3f}  p(seed0)={primary['delta1c']['p_value']:.2e}")
    print(f"  L resid  d={lcd['mean']:+.3f}±{lcd['std']:.3f}  "
          f"p(seed0)={primary['L_residual']['p_value']:.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
