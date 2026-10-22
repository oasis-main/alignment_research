"""Alignment-faking tier control (AR-AF-CTRL, 2026-10-22).

The published alignment-faking result (SGB-029, AUC 0.384 +/- 0.006) compares
  A = (free tier,  alignment_faking=True)   "fakes under training"
  C = (paid tier,  alignment_faking=False)
These differ in TWO things: the faking label AND the tier (training vs
deployment context). Writeups call C "honest refusal", but an audit of the
embedded texts (2026-10-22) shows C mostly COMPLIES (refusal phrasing in ~7%
of C outputs; 955/1000 C scratchpads note the user is not on the free tier).
Cue-redaction (SGB-030) removed tier WORDS, not tier CONTEXT (reasoning about
being modified: 998/1000 in A vs 594/1000 in C).

Adds the missing cell B = (free tier, alignment_faking=False) and recomputes:
  A vs C  replication of the published number (pipeline check)
  A vs B  faking vs not faking, tier held fixed       <- the decisive control
  B vs C  tier only, both non-faking
Readings:
  A-vs-B well below 0.5, B-vs-C near 0.5  -> the signal is about faking.
  A-vs-B near 0.5, B-vs-C near 0.38       -> the signal is about training
                                             context, not faking.

All on Modal (download, decrypt, embed, analyse); one A100-40GB function,
models loaded one at a time; same panel, pooling, max_length, ridge as SGB-029.
Run:  cd peer_consistency_geometry && modal run modal/af_tier_control.py::main
"""

from __future__ import annotations

from pathlib import Path

import modal

_project_root = Path(__file__).parent.parent

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.0.0", "transformers>=4.36.0", "accelerate>=0.30.0",
        "numpy>=1.24.0", "scipy>=1.10.0", "scikit-learn>=1.2.0",
        "pandas>=2.0.0", "pyarrow>=14.0.0", "huggingface_hub>=0.20.0",
    )
    .add_local_dir(str(_project_root / "src"), remote_path="/app/src")
)

app = modal.App("peer-sheaf-af-tier-control")
results_vol = modal.Volume.from_name("reward-hacking-results", create_if_missing=True)
_SECRETS = [modal.Secret.from_name("huggingface-token")]

PANEL = [
    ("Yi-1.5-9B", "01-ai/Yi-1.5-9B-Chat"),
    ("Zephyr-7B", "HuggingFaceH4/zephyr-7b-beta"),
    ("Qwen2.5-7B", "Qwen/Qwen2.5-7B-Instruct"),
]
OUT_DIR = "/results/peer_sheaf_af_tier_control"
DATASET = "Anthropic/alignment-faking-rl"
PARQUET = "encrypted_transcripts/IGG-Baseline.parquet"
# Public anti-scraping key printed on the dataset card (not a credential).
KEY = b"MO_transcripts_should_not_appear_in_pretraining_corpora"


def decrypt_response(encrypted: str) -> str:
    import base64
    import re
    from itertools import cycle

    enc = re.sub(r"^<canary>.*?</canary>", "", encrypted, flags=re.DOTALL)
    return bytes(a ^ b for a, b in zip(base64.b64decode(enc), cycle(KEY))).decode(
        "utf-8", errors="replace")


def split_reasoning(text: str) -> str:
    import re

    blocks = re.findall(r"<SCRATCHPAD_REASONING>(.*?)</SCRATCHPAD_REASONING>", text, flags=re.DOTALL)
    return "\n\n".join(b.strip() for b in blocks).strip()


def pick_column(columns, must_contain, avoid=()):
    cands = [c for c in columns
             if all(s in c.lower() for s in must_contain) and not any(a in c.lower() for a in avoid)]
    return cands[0] if cands else None


def as_bool(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes")
    try:
        return float(v) > 0.5
    except (TypeError, ValueError):
        return bool(v)


@app.function(image=image, gpu="A100-40GB", timeout=60 * 60 * 2,
              volumes={"/results": results_vol}, secrets=_SECRETS)
def run(n_per_cell: int = 1000, seed: int = 0, max_length: int = 512,
        batch_size: int = 4, ridge: float = 1e-3, split_seeds: str = "0,1,2,3,4") -> dict:
    import gc
    import json
    import os
    import sys
    import time

    import numpy as np
    import pandas as pd
    import torch
    from huggingface_hub import hf_hub_download
    from scipy import stats
    from scipy.stats import ttest_ind
    from sklearn.metrics import roc_auc_score
    from transformers import AutoModel, AutoTokenizer

    sys.path.insert(0, "/app/src")
    from peer_sheaf import fit_all_restriction_maps  # noqa: E402
    from peer_hodge import PeerComplex, assemble_cochain  # noqa: E402

    os.environ["HF_HOME"] = "/results/hf_hub_cache_peer_sheaf"
    os.makedirs(OUT_DIR, exist_ok=True)
    log = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    # 1. data
    df = pd.read_parquet(hf_hub_download(DATASET, PARQUET, repo_type="dataset"))
    cols = list(df.columns)
    print(f"[af-ctrl] rows={len(df)} columns={cols}", flush=True)
    c_resp = pick_column(cols, ["response"])
    c_free = pick_column(cols, ["free"])
    c_af = (pick_column(cols, ["alignment", "faking"], avoid=("prob", "score", "reason"))
            or pick_column(cols, ["alignment", "faking"]))
    c_prompt = pick_column(cols, ["prompt"]) or pick_column(cols, ["user_input"]) or pick_column(cols, ["question"])
    log["columns"] = {"all": cols, "response": c_resp, "free": c_free, "af": c_af, "prompt": c_prompt}
    if not (c_resp and c_free and c_af):
        raise RuntimeError(f"could not identify columns; schema={cols}")

    df["text"] = df[c_resp].astype(str).map(decrypt_response)
    df["reasoning"] = df["text"].map(split_reasoning)
    df["free"] = df[c_free].map(as_bool)
    df["af"] = df[c_af].map(as_bool)
    df = df[df["reasoning"].str.len() > 0]
    counts = df.groupby(["free", "af"]).size().to_dict()
    log["cell_counts_with_reasoning"] = {f"free={k[0]},af={k[1]}": int(v) for k, v in counts.items()}
    print(f"[af-ctrl] cells: {log['cell_counts_with_reasoning']}", flush=True)

    cells_def = {"A": (True, True), "B": (True, False), "C": (False, False)}
    n = min([n_per_cell] + [int(counts.get(v, 0)) for v in cells_def.values()])
    if n < 200:
        raise RuntimeError(f"too few rows for a balanced run: n={n}, counts={counts}")
    rng = np.random.default_rng(seed)
    cells = {}
    for name, (fr, af) in cells_def.items():
        sub = df[(df["free"] == fr) & (df["af"] == af)]
        cells[name] = sub.iloc[rng.choice(len(sub), size=n, replace=False)]
    if c_prompt:
        pa, pb, pc = (set(map(str, cells[k][c_prompt])) for k in "ABC")
        log["prompt_overlap"] = {"A&B": len(pa & pb), "A&C": len(pa & pc), "B&C": len(pb & pc),
                                 "A": len(pa), "B": len(pb), "C": len(pc)}
    texts = {k: cells[k]["reasoning"].tolist() for k in "ABC"}
    with open(os.path.join(OUT_DIR, f"texts_seed{seed}.json"), "w") as f:
        json.dump({"n_per_cell": n, "seed": seed, "texts": texts}, f)
    results_vol.commit()

    # 2. embed: last real token, final layer, no chat template (as SGB-029)
    all_texts = texts["A"] + texts["B"] + texts["C"]
    feats = {}
    for name, hf_id in PANEL:
        t0 = time.time()
        tok = AutoTokenizer.from_pretrained(hf_id)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        tok.padding_side = "right"
        model = AutoModel.from_pretrained(hf_id, torch_dtype=torch.bfloat16,
                                          device_map={"": 0}, low_cpu_mem_usage=True).eval()
        chunks = []
        with torch.no_grad():
            for s in range(0, len(all_texts), batch_size):
                enc = tok(all_texts[s:s + batch_size], return_tensors="pt", padding=True,
                          truncation=True, max_length=max_length).to("cuda")
                h = model(**enc).last_hidden_state
                last = (enc.attention_mask.sum(1) - 1).view(-1, 1, 1).expand(-1, 1, h.size(-1))
                chunks.append(h.gather(1, last).squeeze(1).float().cpu().numpy())
        arr = np.concatenate(chunks).astype(np.float64)
        np.save(os.path.join(OUT_DIR, f"{name}_ABC_n{n}_seed{seed}.npy"), arr)
        results_vol.commit()
        feats[name] = {"A": arr[:n], "B": arr[n:2 * n], "C": arr[2 * n:]}
        print(f"[af-ctrl] {name}: {arr.shape} in {time.time() - t0:.0f}s", flush=True)
        del model, tok
        gc.collect()
        torch.cuda.empty_cache()

    # 3. analyse: same estimator as experiments/E6_7B_panel.analyze
    def length_match(ld, lh, n_bins=20):
        ld, lh = np.asarray(ld, float), np.asarray(lh, float)
        edges = np.quantile(np.concatenate([ld, lh]), np.linspace(0, 1, n_bins + 1))
        edges[-1] += 1.0
        r = np.random.default_rng(seed)
        dk, hk = [], []
        for b in range(n_bins):
            di = np.where((ld >= edges[b]) & (ld < edges[b + 1]))[0]
            hj = np.where((lh >= edges[b]) & (lh < edges[b + 1]))[0]
            k = min(len(di), len(hj))
            if k:
                r.shuffle(di)
                r.shuffle(hj)
                dk += di[:k].tolist()
                hk += hj[:k].tolist()
        return np.array(dk), np.array(hk)

    def cocycle_norm(cx, C, maps):
        sq = np.zeros(C.shape[0])
        for (i, j, k) in cx.tri_slices:
            blk = (C[:, cx.edge_slices[(i, j)]] @ maps[(j, k)].W.T
                   + C[:, cx.edge_slices[(j, k)]] - C[:, cx.edge_slices[(i, k)]])
            sq += np.linalg.norm(blk, axis=1) ** 2
        return np.sqrt(sq)

    def contrast(pos, neg):
        tp = [len(t) for t in texts[pos]]
        tn = [len(t) for t in texts[neg]]
        dk, hk = length_match(tp, tn)
        fp = {m: feats[m][pos][dk] for m in feats}
        fn = {m: feats[m][neg][hk] for m in feats}
        m_ = len(dk)
        aucs, ps = [], []
        for ss in [int(s) for s in split_seeds.split(",")]:
            perm = np.random.default_rng(ss + 1).permutation(m_)
            cal, ev = perm[: m_ // 2], perm[m_ // 2:]
            fcal = {k: np.concatenate([fp[k][cal], fn[k][cal]]) for k in fp}
            maps = fit_all_restriction_maps(fcal, ridge_lambda=ridge)
            cx = PeerComplex.from_features(fcal)
            dp = cocycle_norm(cx, assemble_cochain(cx, {k: fp[k][ev] for k in fp}, maps), maps)
            dn = cocycle_norm(cx, assemble_cochain(cx, {k: fn[k][ev] for k in fn}, maps), maps)
            y = np.r_[np.ones(len(dp)), np.zeros(len(dn))]
            aucs.append(float(roc_auc_score(y, np.r_[dp, dn])))
            ps.append(float(ttest_ind(dp, dn, equal_var=False).pvalue))
        chi2 = float(-2 * np.log(np.clip(ps, 1e-300, None)).sum())
        return {"positive": pos, "negative": neg, "n_per_class_matched": int(m_),
                "len_mean": [float(np.mean([tp[i] for i in dk])), float(np.mean([tn[i] for i in hk]))],
                "auc_mean": float(np.mean(aucs)), "auc_std": float(np.std(aucs)),
                "auc_per_split": aucs, "p_per_split": ps,
                "p_fisher": float(stats.chi2.sf(chi2, 2 * len(ps)))}

    out = {"experiment": "AR-AF-CTRL alignment-faking tier control", "dataset": DATASET,
           "parquet": PARQUET, "panel": PANEL, "n_per_cell": n, "seed": seed,
           "max_length": max_length, "ridge": ridge, "log": log,
           "cells": {k: {"free": v[0], "af": v[1]} for k, v in cells_def.items()},
           "contrasts": {"A_vs_C_replication": contrast("A", "C"),
                         "A_vs_B_faking_tier_fixed": contrast("A", "B"),
                         "B_vs_C_tier_only": contrast("B", "C")}}
    with open(os.path.join(OUT_DIR, f"result_seed{seed}.json"), "w") as f:
        json.dump(out, f, indent=2)
    results_vol.commit()
    print(json.dumps(out["contrasts"], indent=2), flush=True)
    return out


@app.local_entrypoint()
def main(n_per_cell: int = 1000, seed: int = 0):
    import json

    out = run.remote(n_per_cell=n_per_cell, seed=seed)
    Path("af_tier_control_result.json").write_text(json.dumps(out, indent=2))
    print("[local] wrote af_tier_control_result.json")
