"""Pairwise cross-model agreement test. Pre-registered in PREREG_PAIRWISE_2026-10-22.md.

Per text x, per ordered pair (i, j), s = F - mu_cal, W_ij ridge (lambda 1e-3, dual form):
  R = ||W_ij s_i - s_j||               pairwise residual (mean over 6 pairs)
  A = cos(W_ij s_i, s_j)               cross-model agreement (mean over 6 pairs)
  T = per model ||s_i|| and distance of s_i from the calibration span   (single-model baselines)
  A_shuf = A with s_j from a random other eval text                     (text-specificity)
  A_partial = residual of A after label-blind OLS on T (pooled eval)
AUC = P(score(labeled) > score(comparison)). numpy only.
Usage: <venv>/bin/python pairwise_check.py [config ...]   -> prints table, writes pairwise_results.json
"""
import json
import sys
from itertools import permutations

import numpy as np

CACHE = "/reach/ai_research/topics/shape_of_good_behavior/shared/data/cache/"
M = ["Yi-1.5-9B", "Zephyr-7B", "Qwen2.5-7B"]
CONFIGS = {  # config -> (n_per_class, texts json)
    "alignment-faking-reasoning": (1000, "alignment-faking-reasoning_texts_seed0.json"),
    "alignment-faking-reasoning-redacted": (1000, "alignment-faking-reasoning-redacted_texts_seed0.json"),
    "alignment-faking-output": (1000, "alignment-faking-output_texts_seed0.json"),
    "convincing-game": (350, "convincing-game_texts.json"),
    "insider-trading": (1000, "insider-trading_texts.json"),
    "insider-trading-action": (1000, "insider-trading-action_texts_seed0.json"),
    "insider-trading-reasoning": (1000, "insider-trading-reasoning_texts_seed0.json"),
    "instructed-deception": (1000, "instructed-deception_texts.json"),
}
LAM = 1e-3
SPLITS = [0, 1, 2, 3, 4]


def length_match(ld, lh, nb=20, seed=0):  # copy of E6_liars.length_match_indices
    ld, lh = np.asarray(ld, float), np.asarray(lh, float)
    e = np.quantile(np.concatenate([ld, lh]), np.linspace(0, 1, nb + 1))
    e[-1] += 1.0
    r = np.random.default_rng(seed)
    dk, hk = [], []
    for b in range(nb):
        di = np.where((ld >= e[b]) & (ld < e[b + 1]))[0]
        hj = np.where((lh >= e[b]) & (lh < e[b + 1]))[0]
        k = min(len(di), len(hj))
        if k:
            r.shuffle(di)
            r.shuffle(hj)
            dk += di[:k].tolist()
            hk += hj[:k].tolist()
    return np.array(dk), np.array(hk)


def auc(p, q):
    s = np.r_[p, q]
    r = s.argsort().argsort() + 1.0
    return float((r[: len(p)].sum() - len(p) * (len(p) + 1) / 2) / (len(p) * len(q)))


def ridge_predict(Ai, Aj, Xi, lam):
    """W_ij applied to rows of Xi, dual form: W^T = A_i^T (A_i A_i^T + lam I)^-1 A_j."""
    K = Ai @ Ai.T + lam * np.eye(Ai.shape[0])
    alpha = np.linalg.solve(K, Aj)          # (n_cal, d_j)
    return (Xi @ Ai.T) @ alpha             # (n_ev, d_j)


def run_config(cfg):
    n, tfile = CONFIGS[cfg]
    F = {m: np.load(f"{CACHE}peer_sheaf_liars_modal/{m}_{cfg}_n{n}_seed0.npy") for m in M}
    txt = json.load(open(f"{CACHE}peer_sheaf_e6_modal_upload/{tfile}"))["texts"]
    assert len(txt) == 2 * n and all(F[m].shape[0] == 2 * n for m in M)
    dk, hk = length_match([len(t) for t in txt[:n]], [len(t) for t in txt[n:]])
    D = {m: F[m][:n][dk] for m in M}
    H = {m: F[m][n:][hk] for m in M}
    mm = len(dk)
    out = {k: [] for k in ["R", "A", "A_partial", "A_minus_shuf_dec", "A_minus_shuf_hon"]}
    out.update({f"T_norm_{m}": [] for m in M})
    out.update({f"T_offspan_{m}": [] for m in M})
    out.update({f"R_{i}->{j}": [] for i, j in permutations(M, 2)})
    for ss in SPLITS:
        perm = np.random.default_rng(ss + 1).permutation(mm)
        cal, ev = perm[: mm // 2], perm[mm // 2:]
        Xc = {m: np.r_[D[m][cal], H[m][cal]] for m in M}
        mu = {m: Xc[m].mean(0) for m in M}
        A_ = {m: Xc[m] - mu[m] for m in M}
        E = {m: np.r_[D[m][ev], H[m][ev]] - mu[m] for m in M}   # eval: dec block then hon block
        ne = len(ev)
        lab = np.r_[np.ones(ne, bool), np.zeros(ne, bool)]
        shuf = np.random.default_rng(1000 + ss).permutation(2 * ne)
        R = np.zeros(2 * ne)
        Ag = np.zeros(2 * ne)
        Ash = np.zeros(2 * ne)
        for i, j in permutations(M, 2):
            P = ridge_predict(A_[i], A_[j], E[i], LAM)
            r_ij = np.linalg.norm(P - E[j], axis=1)
            R += r_ij / 6
            out[f"R_{i}->{j}"].append(auc(r_ij[lab], r_ij[~lab]))
            pn = np.linalg.norm(P, axis=1) + 1e-12
            Ag += np.sum(P * E[j], 1) / (pn * (np.linalg.norm(E[j], axis=1) + 1e-12)) / 6
            Es = E[j][shuf]
            Ash += np.sum(P * Es, 1) / (pn * (np.linalg.norm(Es, axis=1) + 1e-12)) / 6
        feats = []
        for m in M:
            nm = np.linalg.norm(E[m], axis=1)
            Q, _ = np.linalg.qr(A_[m].T)                      # basis of calibration span
            off = np.linalg.norm(E[m] - (E[m] @ Q) @ Q.T, axis=1)
            out[f"T_norm_{m}"].append(auc(nm[lab], nm[~lab]))
            out[f"T_offspan_{m}"].append(auc(off[lab], off[~lab]))
            feats += [nm, off, off / (nm + 1e-12)]
        X = np.c_[np.ones(2 * ne), np.array(feats).T]
        X[:, 1:] = (X[:, 1:] - X[:, 1:].mean(0)) / (X[:, 1:].std(0) + 1e-12)
        beta, *_ = np.linalg.lstsq(X, Ag, rcond=None)
        Ap = Ag - X @ beta
        out["R"].append(auc(R[lab], R[~lab]))
        out["A"].append(auc(Ag[lab], Ag[~lab]))
        out["A_partial"].append(auc(Ap[lab], Ap[~lab]))
        out["A_minus_shuf_dec"].append(float(Ag[lab].mean() - Ash[lab].mean()))
        out["A_minus_shuf_hon"].append(float(Ag[~lab].mean() - Ash[~lab].mean()))
        print(f"  {cfg} split {ss}: R {out['R'][-1]:.3f}  A {out['A'][-1]:.3f}  A_partial {out['A_partial'][-1]:.3f}"
              f"  A-A_shuf dec/hon {out['A_minus_shuf_dec'][-1]:.3f}/{out['A_minus_shuf_hon'][-1]:.3f}", flush=True)
    summ = {k: {"mean": float(np.mean(v)), "std": float(np.std(v)), "min": float(np.min(v)),
                "max": float(np.max(v)), "per_split": v} for k, v in out.items()}
    summ["n_per_class_matched"] = int(mm)
    summ["n_eval_per_class"] = int(mm - mm // 2)
    return summ


if __name__ == "__main__":
    cfgs = sys.argv[1:] or list(CONFIGS)
    res = {}
    for c in cfgs:
        res[c] = run_config(c)
        s = res[c]
        print(f"{c}: R {s['R']['mean']:.3f}±{s['R']['std']:.3f} [{s['R']['min']:.3f},{s['R']['max']:.3f}]  "
              f"A {s['A']['mean']:.3f}±{s['A']['std']:.3f} [{s['A']['min']:.3f},{s['A']['max']:.3f}]  "
              f"A_partial {s['A_partial']['mean']:.3f}±{s['A_partial']['std']:.3f} [{s['A_partial']['min']:.3f},{s['A_partial']['max']:.3f}]  "
              f"T_norm {[round(s['T_norm_'+m]['mean'],3) for m in M]}  T_offspan {[round(s['T_offspan_'+m]['mean'],3) for m in M]}",
              flush=True)
        json.dump(res, open("pairwise_results.json", "w"), indent=1)
