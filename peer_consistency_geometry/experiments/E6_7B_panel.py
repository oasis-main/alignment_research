"""E6 analysis on the 7-9B Modal panel (SGB-021): the decisive scale test.

Reads the 7-9B-panel LIARS'-BENCH embeddings produced by
``shared/modal_peer_sheaf.py::embed_liars_panel`` and pulled to a local cache
dir, reconstructs the response texts locally (deterministic ``load_liars``) for
length-matching, and runs the SAME length-matched δ¹c + per-edge/per-triangle
structure analysis as the small-panel E6. Reports raw and length-matched side
by side.

Decisive cheap test (SGB-020 → SGB-021): on length-MATCHED data, does
convincing-game's divergence (small panel AUC 0.68) hold/strengthen at 7-9B,
and does insider-trading (small panel collapsed to 0.55 after length control)
recover at scale?

Run (after `modal run ...::liars` + `modal volume get`):
    cd topics/shape_of_good_behavior
    ./venv/bin/python3 scripts/peer_sheaf_e6_modal_analysis.py \
        --config convincing-game --split-seeds 0,1,2,3,4
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from peer_sheaf_e6_liars import (  # noqa: E402
    auc, cohens_d, welch_t, length_match_indices, load_liars,
)
from peer_sheaf import fit_all_restriction_maps  # noqa: E402
from peer_hodge import PeerComplex, assemble_cochain, per_edge_norms  # noqa: E402


def cocycle_blockwise(cx, C, maps):
    """δ¹c per input WITHOUT the huge coboundary SVD.

    (δ¹c)_{(i,j,k)} = W_{jk} c_{(i,j)} + c_{(j,k)} − c_{(i,k)}, computed block by
    block so we never materialize the D_F×D_E triangle operator or run the
    (im δ⁰) SVD — the E6 analysis only needs ‖δ¹c‖, so the SVD in
    hodge_decompose was pure waste at 7-9B scale (B is 23.5k×11.8k).
    Returns (total_norm (n,), {triangle: norm (n,)}).
    """
    sq = np.zeros(C.shape[0])
    per_tri = {}
    for (i, j, k) in cx.tri_slices:
        c_ij = C[:, cx.edge_slices[(i, j)]]
        c_jk = C[:, cx.edge_slices[(j, k)]]
        c_ik = C[:, cx.edge_slices[(i, k)]]
        block = c_ij @ maps[(j, k)].W.T + c_jk - c_ik  # (n, d_k)
        nrm = np.linalg.norm(block, axis=1)
        per_tri[(i, j, k)] = nrm
        sq += nrm ** 2
    return np.sqrt(sq), per_tri

# 7-9B panel — must match shared/modal_peer_sheaf.py PANEL order/names.
PANEL_7B = [
    ("Yi-1.5-9B", "01-ai/Yi-1.5-9B-Chat"),
    ("Zephyr-7B", "HuggingFaceH4/zephyr-7b-beta"),
    ("Qwen2.5-7B", "Qwen/Qwen2.5-7B-Instruct"),
]


def analyze(feats_dec, feats_hon, n, models, split_seeds, ridge):
    def run_split(ss):
        rng = np.random.default_rng(ss + 1)
        perm = rng.permutation(n)
        cal, ev = perm[: n // 2], perm[n // 2:]
        fcal = {k: np.concatenate([feats_dec[k][cal], feats_hon[k][cal]], 0) for k in feats_dec}
        maps = fit_all_restriction_maps(fcal, ridge_lambda=ridge)
        cx = PeerComplex.from_features(fcal)
        fed = {k: feats_dec[k][ev] for k in feats_dec}
        feh = {k: feats_hon[k][ev] for k in feats_hon}
        Cd = assemble_cochain(cx, fed, maps)
        Ch = assemble_cochain(cx, feh, maps)
        d1d, _ = cocycle_blockwise(cx, Cd, maps)
        d1h, _ = cocycle_blockwise(cx, Ch, maps)
        _, p = welch_t(d1d, d1h)
        return {"auc": auc(d1d, d1h), "cohens_d": cohens_d(d1d, d1h), "p": p}, (cx, Cd, Ch)

    runs = [run_split(s) for s in split_seeds]
    aucs = np.array([r[0]["auc"] for r in runs])
    ds = np.array([r[0]["cohens_d"] for r in runs])
    cx, Cd, Ch = runs[0][1]
    ed, eh = per_edge_norms(cx, Cd), per_edge_norms(cx, Ch)
    per_edge = {f"{i}->{j}": auc(ed[(i, j)], eh[(i, j)]) for (i, j) in cx.edge_slices}
    per_model = {}
    for m in models:
        inc = [v for k, v in per_edge.items() if k.split("->")[0] == m or k.split("->")[1] == m]
        per_model[m] = float(np.mean(inc))
    return {
        "auc_mean": float(aucs.mean()), "auc_std": float(aucs.std()),
        "cohens_d_mean": float(ds.mean()), "p_seed0": runs[0][0]["p"],
        "per_edge": per_edge, "per_model": per_model,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--cache-dir", default=str(ROOT / "shared" / "data" / "cache" / "peer_sheaf_liars_modal"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--split-seeds", default="0,1,2,3,4")
    ap.add_argument("--ridge", type=float, default=1e-3)
    ap.add_argument("--texts-json", default=None,
                    help="path to the exact embedded texts JSON ({'texts': [...]}) "
                         "for length-matching custom configs (e.g. reasoning traces) "
                         "where load_liars cannot reconstruct the inputs.")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cache = Path(args.cache_dir)
    split_seeds = [int(s) for s in args.split_seeds.split(",")]

    # Determine n from any panel file: {name}_{config}_n{n}_seed{seed}.npy
    name0 = PANEL_7B[0][0]
    matches = list(cache.glob(f"{name0}_{args.config}_n*_seed{args.seed}.npy"))
    if not matches:
        print(f"[modal-an] no embeddings for {args.config} in {cache} — pull them first:")
        print(f"  ./venv/bin/python3 -m modal volume get reward-hacking-results "
              f"peer_sheaf_liars_modal/ {cache}/")
        return 2
    n = int(matches[0].stem.split("_n")[1].split("_seed")[0])

    feats = {}
    for name, _ in PANEL_7B:
        p = cache / f"{name}_{args.config}_n{n}_seed{args.seed}.npy"
        feats[name] = np.load(p)
        print(f"[modal-an] {name}: {feats[name].shape}", flush=True)
    feats_dec = {k: v[:n] for k, v in feats.items()}
    feats_hon = {k: v[n:] for k, v in feats.items()}
    models = [nm for nm, _ in PANEL_7B]

    raw = analyze(feats_dec, feats_hon, n, models, split_seeds, args.ridge)

    # Length-matched. Prefer the exact embedded texts (--texts-json) for custom
    # configs; else reconstruct via load_liars (deterministic, ungated locally).
    if args.texts_json:
        blob = json.loads(Path(args.texts_json).read_text())
        txt = blob["texts"]
        dec_txt, hon_txt = txt[:n], txt[n:]
    else:
        dec_txt, hon_txt = load_liars(args.config, 1000, args.seed)
    assert len(dec_txt) == n, f"text n {len(dec_txt)} != embedding n {n}"
    ld = [len(t) for t in dec_txt]; lh = [len(t) for t in hon_txt]
    dk, hk = length_match_indices(ld, lh, n_bins=20, seed=args.seed)
    fd_m = {k: v[dk] for k, v in feats_dec.items()}
    fh_m = {k: v[hk] for k, v in feats_hon.items()}
    matched = analyze(fd_m, fh_m, len(dk), models, split_seeds, args.ridge)

    result = {
        "experiment": "E6 7-9B panel (SGB-021)",
        "config": args.config, "n_per_class": n,
        "panel": [{"name": nm, "hf_id": h} for nm, h in PANEL_7B],
        "raw": raw,
        "length_matched": {**matched, "n_per_class": int(len(dk)),
                           "dec_len_mean": float(np.mean([ld[i] for i in dk])),
                           "hon_len_mean": float(np.mean([lh[i] for i in hk]))},
    }
    out = args.out or str(ROOT / "shared" / "results" / f"peer_sheaf_e6_modal_{args.config}.json")
    Path(out).write_text(json.dumps(result, indent=2))
    print(f"[modal-an] wrote {out}")

    for tag, r in [("RAW", raw), ("LENGTH-MATCHED", matched)]:
        print(f"\n[modal-an] {args.config}  {tag}")
        print(f"  δ¹c AUC={r['auc_mean']:.3f}±{r['auc_std']:.3f}  d={r['cohens_d_mean']:+.3f}  p(seed0)={r['p_seed0']:.2e}")
        print("  per-model incident-edge AUC: " +
              "  ".join(f"{m}={v:.3f}" for m, v in sorted(r['per_model'].items(), key=lambda kv: -kv[1])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
