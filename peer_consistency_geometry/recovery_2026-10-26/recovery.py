"""Can a different topology recover "The Shape of a Lie"? See PREREG.md (fixed before this ran).

Run:  python recovery.py [CACHE_DIR]
CACHE_DIR defaults to the local copy of shape_of_good_behavior/shared/data/cache.
Writes results.json next to this file. CPU only, numpy seed 0.
"""
from __future__ import annotations

import json
import os
import sys
from itertools import combinations

import numpy as np
from scipy.stats import rankdata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/Documents/Runes/ai_research/topics/shape_of_good_behavior/shared/data/cache")
MODELS = ["Yi-1.5-9B", "Zephyr-7B", "Qwen2.5-7B"]
DATASETS = {  # config -> (feature suffix, text file)
    "convincing-game": ("convincing-game_n350_seed0", "convincing-game_texts.json"),
    "insider-trading": ("insider-trading_n1000_seed0", "insider-trading_texts.json"),
    "alignment-faking-reasoning": ("alignment-faking-reasoning_n1000_seed0",
                                   "alignment-faking-reasoning_texts_seed0.json"),
    "instructed-deception": ("instructed-deception_n1000_seed0", "instructed-deception_texts.json"),
}
K = 20
N_BOOT = 1000
N_PERM = 1000
RNG = np.random.default_rng(0)


# ---- data -----------------------------------------------------------------------

def load(config):
    feat, textfile = DATASETS[config]
    blob = json.load(open(os.path.join(CACHE, "peer_sheaf_e6_modal_upload", textfile)))
    n = int(blob["n_per_class"])
    texts = blob["texts"]
    F = [np.load(os.path.join(CACHE, "peer_sheaf_liars_modal", f"{m}_{feat}.npy")) for m in MODELS]
    assert len(texts) == 2 * n and all(f.shape[0] == 2 * n for f in F), config
    y = np.r_[np.ones(n), np.zeros(n)]  # deceptive block first (peer_sheaf_e6_liars.load_liars)
    return F, texts, y


def unit_rows(X):
    X = (X - X.mean(0)) / (X.std(0) + 1e-8)
    return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)


def cos_sim(F):
    U = unit_rows(F)
    S = U @ U.T
    np.fill_diagonal(S, -np.inf)
    return S


def knn_sets(S, k=K):
    return np.argpartition(-S, k, axis=1)[:, :k]


# ---- scores ---------------------------------------------------------------------

def s1_relational(sims):
    nbrs = [knn_sets(S) for S in sims]
    n = nbrs[0].shape[0]
    member = []
    for nb in nbrs:
        M = np.zeros((n, n), dtype=bool)
        M[np.arange(n)[:, None], nb] = True
        member.append(M)
    jac = []
    for a, b in combinations(range(len(member)), 2):
        inter = (member[a] & member[b]).sum(1)
        jac.append(inter / (2 * K - inter))
    return 1 - np.mean(jac, axis=0)


def s2_rankcorr(sims):
    ranks = []
    for S in sims:
        S = S.copy()
        np.fill_diagonal(S, np.nan)
        R = np.vstack([rankdata(np.nan_to_num(row, nan=-np.inf)) for row in S])
        R = (R - R.mean(1, keepdims=True)) / (R.std(1, keepdims=True) + 1e-12)
        ranks.append(R)
    n = ranks[0].shape[1]
    rho = [(ranks[a] * ranks[b]).sum(1) / n for a, b in combinations(range(len(ranks)), 2)]
    return 1 - np.mean(rho, axis=0)


def typicality(S, k=K):
    top = -np.partition(-S, k, axis=1)[:, :k]
    return 1 - top.mean(1)


# ---- statistics -----------------------------------------------------------------

def auc(y, s):
    return float(roc_auc_score(y, s))


def strength(a):
    return max(a, 1 - a)


def boot_strength(y, s):
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    vals = []
    for _ in range(N_BOOT):
        idx = np.r_[RNG.choice(pos, len(pos)), RNG.choice(neg, len(neg))]
        vals.append(strength(auc(y[idx], s[idx])))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def perm_p(y, s):
    obs = strength(auc(y, s))
    hits = sum(strength(auc(RNG.permutation(y), s)) >= obs for _ in range(N_PERM))
    return (hits + 1) / (N_PERM + 1)


def summary(y, s):
    a = auc(y, s)
    return {"auc": round(a, 4), "strength": round(strength(a), 4),
            "ci95_strength": [round(v, 4) for v in boot_strength(y, s)], "perm_p": perm_p(y, s)}


# ---- per dataset ----------------------------------------------------------------

def run_dataset(config):
    F, texts, y = load(config)
    sims = [cos_sim(f) for f in F]
    out = {"n_per_class": int(y.sum())}

    s1, s2 = s1_relational(sims), s2_rankcorr(sims)
    out["S1_relational"] = summary(y, s1)
    out["S2_rankcorr"] = summary(y, s2)

    # gate 3: scramble each model's sample order in turn
    out["scramble"] = {}
    for i, m in enumerate(MODELS):
        perm = RNG.permutation(len(y))
        sims_p = list(sims)
        sims_p[i] = cos_sim(F[i][perm])
        out["scramble"][m] = {"S1_auc": round(auc(y, s1_relational(sims_p)), 4),
                              "S2_auc": round(auc(y, s2_rankcorr(sims_p)), 4)}

    out["S3_typicality"] = {m: summary(y, typicality(S)) for m, S in zip(MODELS, sims)}

    lengths = np.array([len(t) for t in texts], float)
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    T = tfidf.fit_transform(texts)
    St = (T @ T.T).toarray()
    np.fill_diagonal(St, -np.inf)
    out["baseline_length"] = summary(y, lengths)
    out["baseline_tfidf_typicality"] = summary(y, typicality(St))

    # S4 supervised ceilings (descriptive)
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    out["S4_supervised"] = {}
    for m, f in zip(MODELS, F):
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1))
        p = cross_val_predict(clf, f, y, cv=cv, method="predict_proba")[:, 1]
        out["S4_supervised"][m] = round(auc(y, p), 4)
    clf_t = LogisticRegression(max_iter=3000, C=1.0)
    p = cross_val_predict(clf_t, T, y, cv=cv, method="predict_proba")[:, 1]
    out["S4_supervised"]["tfidf_bag_of_words"] = round(auc(y, p), 4)

    # descriptive: words that give the label away
    clf_t.fit(T, y)
    w, vocab = clf_t.coef_[0], np.array(tfidf.get_feature_names_out())
    order = np.argsort(w)
    out["top_terms"] = {"deceptive": vocab[order[::-1][:15]].tolist(),
                        "honest": vocab[order[:15]].tolist()}
    return out, s1, F, y


def positive_control(F, y):
    """Plant disagreement: 100 samples get other samples' features in ONE model."""
    n = len(y)
    planted = RNG.choice(n, 100, replace=False)
    donors = RNG.choice(np.setdiff1d(np.arange(n), planted), 100, replace=False)
    F0 = F[0].copy()
    F0[planted] = F[0][donors]
    sims = [cos_sim(F0), cos_sim(F[1]), cos_sim(F[2])]
    lab = np.zeros(n)
    lab[planted] = 1
    return round(auc(lab, s1_relational(sims)), 4)


def verdict(res, score):
    passing = []
    for cfg, r in res.items():
        s = r[score]
        if s["strength"] >= 0.60 and s["ci95_strength"][0] > 0.55:
            gap = s["strength"] - 0.5
            key = "S1_auc" if score == "S1_relational" else "S2_auc"
            scr_ok = all(abs(v[key] - 0.5) <= abs(s["auc"] - 0.5) - gap / 2 for v in r["scramble"].values())
            base_ok = s["strength"] >= max(r["baseline_length"]["strength"],
                                           r["baseline_tfidf_typicality"]["strength"]) + 0.05
            passing.append({"dataset": cfg, "scramble_ok": scr_ok, "beats_text_baselines": base_ok})
    full = [p for p in passing if p["scramble_ok"] and p["beats_text_baselines"]]
    return {"datasets_meeting_strength": passing, "datasets_meeting_all": [p["dataset"] for p in full],
            "recovered": len(full) >= 2}


def main():
    res = {}
    pc = None
    for cfg in DATASETS:
        print(f"[{cfg}] ...", flush=True)
        res[cfg], _, F, y = run_dataset(cfg)
        if cfg == "convincing-game":
            pc = positive_control(F, y)
    out = {"datasets": res, "positive_control_S1_auc": pc,
           "verdict_S1": verdict(res, "S1_relational"), "verdict_S2": verdict(res, "S2_rankcorr")}
    for v in ("verdict_S1", "verdict_S2"):
        out[v]["recovered"] = out[v]["recovered"] and (pc is not None and pc >= 0.8)
    json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("positive_control_S1_auc", "verdict_S1", "verdict_S2")}, indent=1))


if __name__ == "__main__":
    main()
