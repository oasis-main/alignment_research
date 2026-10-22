"""Check (Kolmogorov, 2026-10-22): does the triangle score depend on more than one model's reading of a text?

Algebra, from the code's own definitions (c_ij = W_ij s_i - s_j, s = F - mu_cal):
  (delta1 c)_ijk = W_jk c_ij + c_jk - c_ik = (W_jk W_ij - W_ik) s_i
so models j and k's readings of the SAME text cancel exactly; only model i's reading enters.

On the cached alignment-faking-reasoning embeddings (split seed 0, length-matched):
  [1] reproduce the per-split AUC with the repo's code path (cochain -> blockwise delta1);
  [2] scramble which text each of models j, k is reading (model i keeps its readings).
      If the algebra is right, the triangles starting at i are unchanged;
  [3] AUC of V restricted to triangles starting at each model;
  [4] how V and its AUC move with the ridge penalty lambda.
numpy only. Run: <venv>/bin/python triangle_cancellation_check.py [config]
"""
import json
import sys
from itertools import permutations

import numpy as np

CACHE = "/reach/ai_research/topics/shape_of_good_behavior/shared/data/cache/"
cfg = sys.argv[1] if len(sys.argv) > 1 else "alignment-faking-reasoning"
M = ["Yi-1.5-9B", "Zephyr-7B", "Qwen2.5-7B"]
F = {m: np.load(f"{CACHE}peer_sheaf_liars_modal/{m}_{cfg}_n1000_seed0.npy") for m in M}
txt = json.load(open(f"{CACHE}peer_sheaf_e6_modal_upload/{cfg}_texts_seed0.json"))["texts"]
n = 1000


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
    return (r[: len(p)].sum() - len(p) * (len(p) + 1) / 2) / (len(p) * len(q))


dk, hk = length_match([len(t) for t in txt[:n]], [len(t) for t in txt[n:]])
D = {m: F[m][:n][dk] for m in M}
H = {m: F[m][n:][hk] for m in M}
mm = len(dk)
perm = np.random.default_rng(1).permutation(mm)  # split seed 0 -> rng(ss + 1), as in E6_7B_panel
cal, ev = perm[: mm // 2], perm[mm // 2:]
Xc = {m: np.r_[D[m][cal], H[m][cal]] for m in M}
mu = {m: Xc[m].mean(0) for m in M}
A = {m: Xc[m] - mu[m] for m in M}
print(f"config={cfg} n_cal={A[M[0]].shape[0]} dims={ {m: F[m].shape[1] for m in M} }", flush=True)
for m in M:
    s = np.linalg.svd(A[m], compute_uv=False)
    print(f"  {m}: cal sigma^2 max {s[0]**2:.3g}, 10th-smallest nonzero {s[-10]**2:.3g}, min {s[-1]**2:.3g}", flush=True)


def fit(lam):
    W, b = {}, {}
    for i, j in permutations(M, 2):
        a = A[i]
        W[(i, j)] = np.linalg.solve(a.T @ a + lam * np.eye(a.shape[1]), a.T @ A[j]).T
        b[(i, j)] = mu[j] - W[(i, j)] @ mu[i]
    return W, b


def V_codepath(W, b, X):
    """The repo's computation: cochain c_ij = rho_ij(F_i) - F_j, then delta1 blockwise."""
    c = {(i, j): X[i] @ W[(i, j)].T + b[(i, j)] - X[j] for i, j in permutations(M, 2)}
    sq = np.zeros(X[M[0]].shape[0])
    per_src = {m: np.zeros_like(sq) for m in M}
    for i, j, k in permutations(M, 3):
        blk = c[(i, j)] @ W[(j, k)].T + c[(j, k)] - c[(i, k)]
        t = np.sum(blk ** 2, 1)
        sq += t
        per_src[i] += t
    return np.sqrt(sq), {m: np.sqrt(v) for m, v in per_src.items()}


W, b = fit(1e-3)
Xd = {m: D[m][ev] for m in M}
Xh = {m: H[m][ev] for m in M}
vd, psd = V_codepath(W, b, Xd)
vh, psh = V_codepath(W, b, Xh)
print(f"[1] code path, lambda 1e-3, split seed 0: AUC = {auc(vd, vh):.4f}", flush=True)

rng = np.random.default_rng(123)
max_rel = 0.0
for i in M:
    Xs = {m: (Xd[m] if m == i else Xd[m][rng.permutation(len(ev))]) for m in M}
    _, ps = V_codepath(W, b, Xs)
    max_rel = max(max_rel, float(np.max(np.abs(ps[i] - psd[i]) / psd[i])))
print(f"[2] triangles from model i, with models j,k reading OTHER texts: max relative change = {max_rel:.2e}", flush=True)

for m in M:
    print(f"[3] triangles starting at {m}: AUC = {auc(psd[m], psh[m]):.4f}", flush=True)

for lam in [1e-1, 1e1, 1e3]:
    W2, b2 = fit(lam)
    v2d, _ = V_codepath(W2, b2, Xd)
    v2h, _ = V_codepath(W2, b2, Xh)
    print(f"[4] lambda {lam:g}: AUC = {auc(v2d, v2h):.4f}; median V / median V at 1e-3 = {np.median(v2d) / np.median(vd):.3g}", flush=True)
