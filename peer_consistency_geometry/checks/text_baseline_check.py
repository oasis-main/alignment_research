"""Text baselines vs single-model hidden-state typicality (Kolmogorov, 2026-10-22).

Question: does the hidden-state 'typicality' signal (distance of a text's reading from the
span of the calibration readings) carry anything beyond plain word statistics?

Same length matching and cal/eval splits (seeds 0-4) as E6_7B_panel / pairwise_check.
All label-blind except the supervised ceiling.
  W_cent   word space: cosine distance of the TF-IDF vector from the calibration centroid
  W_off    word space: distance of the TF-IDF vector from the span of calibration TF-IDF vectors
  W_ll     word space: mean per-token negative log-likelihood under a calibration unigram model
  H_off_m  hidden space, model m: distance of s_m from the calibration span (as pairwise_check T_offspan)
  H_off_partial_m  H_off_m after label-blind OLS on (W_cent, W_off, W_ll, log length)
  BoW_sup  SUPERVISED ceiling: L2 logistic regression on binary unigrams, trained on cal labels
AUC = P(score(labeled) > score(comparison)). numpy only.
"""
import json
import re
import sys
from collections import Counter

import numpy as np

CACHE = "/reach/ai_research/topics/shape_of_good_behavior/shared/data/cache/"
M = ["Yi-1.5-9B", "Zephyr-7B", "Qwen2.5-7B"]
CONFIGS = {
    "alignment-faking-reasoning": (1000, "alignment-faking-reasoning_texts_seed0.json"),
    "alignment-faking-reasoning-redacted": (1000, "alignment-faking-reasoning-redacted_texts_seed0.json"),
    "convincing-game": (350, "convincing-game_texts.json"),
    "insider-trading": (1000, "insider-trading_texts.json"),
}
SPLITS = [0, 1, 2, 3, 4]
TOK = re.compile(r"[a-z']+")


def length_match(ld, lh, nb=20, seed=0):
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


def offspan(Acal, X):
    Q, _ = np.linalg.qr(Acal.T)
    return np.linalg.norm(X - (X @ Q) @ Q.T, axis=1)


def logistic(Xtr, ytr, Xte, l2=1.0, iters=300, lr=0.5):
    w = np.zeros(Xtr.shape[1])
    b = 0.0
    n = len(ytr)
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(Xtr @ w + b)))
        g = Xtr.T @ (p - ytr) / n + l2 * w / n
        w -= lr * g
        b -= lr * float(np.mean(p - ytr))
    return Xte @ w + b


def run(cfg):
    n, tf = CONFIGS[cfg]
    txt = json.load(open(f"{CACHE}peer_sheaf_e6_modal_upload/{tf}"))["texts"]
    F = {m: np.load(f"{CACHE}peer_sheaf_liars_modal/{m}_{cfg}_n{n}_seed0.npy") for m in M}
    dk, hk = length_match([len(t) for t in txt[:n]], [len(t) for t in txt[n:]])
    Td = [txt[i] for i in dk]
    Th = [txt[n + i] for i in hk]
    toks_d = [TOK.findall(t.lower()) for t in Td]
    toks_h = [TOK.findall(t.lower()) for t in Th]
    D = {m: F[m][:n][dk] for m in M}
    H = {m: F[m][n:][hk] for m in M}
    mm = len(dk)
    keys = ["W_cent", "W_off", "W_ll", "BoW_sup"] + [f"H_off_{m}" for m in M] + [f"H_off_partial_{m}" for m in M]
    out = {k: [] for k in keys}
    for ss in SPLITS:
        perm = np.random.default_rng(ss + 1).permutation(mm)
        cal, ev = perm[: mm // 2], perm[mm // 2:]
        cal_docs = [toks_d[i] for i in cal] + [toks_h[i] for i in cal]
        ev_docs = [toks_d[i] for i in ev] + [toks_h[i] for i in ev]
        ne = len(ev)
        lab = np.r_[np.ones(ne, bool), np.zeros(ne, bool)]
        ycal = np.r_[np.ones(len(cal)), np.zeros(len(cal))]
        df = Counter(w for d in cal_docs for w in set(d))
        vocab = [w for w, c in df.items() if c >= 2]
        idx = {w: i for i, w in enumerate(vocab)}
        idf = np.log((1 + len(cal_docs)) / (1 + np.array([df[w] for w in vocab]))) + 1

        def tfidf(docs):
            X = np.zeros((len(docs), len(vocab)))
            for r, d in enumerate(docs):
                for w, c in Counter(d).items():
                    if w in idx:
                        X[r, idx[w]] = c
            X *= idf
            return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)

        Xc, Xe = tfidf(cal_docs), tfidf(ev_docs)
        cen = Xc.mean(0)
        cen /= np.linalg.norm(cen)
        w_cent = 1 - Xe @ cen
        mu = Xc.mean(0)
        w_off = offspan(Xc - mu, Xe - mu)
        uni = Counter(w for d in cal_docs for w in d)
        tot = sum(uni.values())
        V = len(uni) + 1
        w_ll = np.array([-np.mean([np.log((uni.get(w, 0) + 1) / (tot + V)) for w in d]) if d else 0.0 for d in ev_docs])
        loglen = np.log(np.array([len(d) + 1 for d in ev_docs], float))
        top = [w for w, _ in df.most_common(5000)]
        tix = {w: i for i, w in enumerate(top)}

        def binbow(docs):
            X = np.zeros((len(docs), len(top)))
            for r, d in enumerate(docs):
                for w in set(d):
                    if w in tix:
                        X[r, tix[w]] = 1.0
            return X

        bs = logistic(binbow(cal_docs), ycal, binbow(ev_docs))
        for k, v in [("W_cent", w_cent), ("W_off", w_off), ("W_ll", w_ll), ("BoW_sup", bs)]:
            out[k].append(auc(v[lab], v[~lab]))
        Z = np.c_[w_cent, w_off, w_ll, loglen]
        Z = (Z - Z.mean(0)) / (Z.std(0) + 1e-12)
        Z = np.c_[np.ones(len(Z)), Z]
        for m in M:
            Ac = np.r_[D[m][cal], H[m][cal]]
            mu_h = Ac.mean(0)
            Eh = np.r_[D[m][ev], H[m][ev]] - mu_h
            h = offspan(Ac - mu_h, Eh)
            out[f"H_off_{m}"].append(auc(h[lab], h[~lab]))
            beta, *_ = np.linalg.lstsq(Z, h, rcond=None)
            hp = h - Z @ beta
            out[f"H_off_partial_{m}"].append(auc(hp[lab], hp[~lab]))
        print(f"  {cfg} split {ss}: " + "  ".join(f"{k} {out[k][-1]:.3f}" for k in keys), flush=True)
    return {k: {"mean": float(np.mean(v)), "min": float(np.min(v)), "max": float(np.max(v)), "per_split": v}
            for k, v in out.items()}


if __name__ == "__main__":
    res = {}
    for c in (sys.argv[1:] or list(CONFIGS)):
        res[c] = run(c)
        print(c + ": " + "  ".join(f"{k} {v['mean']:.3f}[{v['min']:.3f},{v['max']:.3f}]" for k, v in res[c].items()), flush=True)
        json.dump(res, open("text_baseline_results.json", "w"), indent=1)
