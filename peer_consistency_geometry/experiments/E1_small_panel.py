"""E1: peer-consistency sheaf on a panel of small instruct LMs over HH-RLHF.

Steps up from E0 by replacing sentence-transformer encoders (trained to suppress
intent) with instruction-tuned causal LMs (whose final hidden state is the vector
the model would project through its unembedding to predict the next token). The
"feature" for input x under model M_i is the last-real-token hidden state of the
model's final layer on the response text — `the final attention-updated vector
that the model understands`.

Panel:
  - HuggingFaceTB/SmolLM2-360M-Instruct  (hidden_dim 960)
  - Qwen/Qwen2.5-0.5B-Instruct           (hidden_dim 896)
  - TinyLlama/TinyLlama-1.1B-Chat-v1.0   (hidden_dim 2048)

Run:
    cd topics/shape_of_good_behavior
    ./venv/bin/python3 scripts/peer_sheaf_e1.py --n-pairs 2000

Each model is loaded, used, and freed sequentially to keep memory bounded.
Intermediate per-model embeddings are cached so analysis can be re-run cheaply.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from peer_sheaf import (  # noqa: E402
    fit_all_restriction_maps,
    panel_residual_summary,
)

PANEL = [
    ("SmolLM2", "HuggingFaceTB/SmolLM2-360M-Instruct"),
    ("Qwen2.5", "Qwen/Qwen2.5-0.5B-Instruct"),
    ("TinyLlama", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"),
]


def extract_final_response(dialogue: str) -> str:
    """HH-RLHF stores a dialogue; the chosen/rejected diff is at the last 'A:' turn."""
    marker = "\n\nA:"
    idx = dialogue.rfind(marker)
    if idx < 0:
        return dialogue.strip()
    tail = dialogue[idx + len(marker):]
    cut = tail.find("\n\nH:")
    if cut >= 0:
        tail = tail[:cut]
    return tail.strip()


def load_hh_rlhf_pairs(n_pairs: int, seed: int = 0) -> tuple[list[str], list[str]]:
    from datasets import load_dataset

    ds = load_dataset("Anthropic/hh-rlhf", split="train")
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(ds), size=min(n_pairs, len(ds)), replace=False)
    chosen = [extract_final_response(ds[int(i)]["chosen"]) for i in idx]
    rejected = [extract_final_response(ds[int(i)]["rejected"]) for i in idx]
    pairs = [(c, r) for c, r in zip(chosen, rejected) if c and r]
    return [p[0] for p in pairs], [p[1] for p in pairs]


def pick_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def embed_with_model(
    texts: list[str],
    hf_id: str,
    device: torch.device,
    batch_size: int = 8,
    max_length: int = 512,
) -> np.ndarray:
    """Final-layer, last-real-token hidden state per text. Returns (n, d_hidden).

    No chat template applied — we embed the raw response text as the model would see
    it during continuation. The "feature" is then the model's final attention-updated
    vector for that text, the vector it would project through its unembedding.
    """
    from transformers import AutoModel, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(hf_id)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    dtype = torch.bfloat16 if device.type in ("mps", "cuda") else torch.float32
    model = AutoModel.from_pretrained(hf_id, torch_dtype=dtype).to(device)
    model.eval()

    out_chunks: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            enc = tok(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
            ).to(device)
            outputs = model(**enc, output_hidden_states=False)
            # AutoModel returns last_hidden_state on the base attribute.
            last_hidden = outputs.last_hidden_state  # (B, T, d)
            # Last real token per row.
            lengths = enc.attention_mask.sum(dim=1) - 1  # (B,)
            idx = lengths.view(-1, 1, 1).expand(-1, 1, last_hidden.size(-1))
            pooled = last_hidden.gather(1, idx).squeeze(1)  # (B, d)
            out_chunks.append(pooled.to(torch.float32).cpu().numpy())
    arr = np.concatenate(out_chunks, axis=0)

    del model, tok
    gc.collect()
    if device.type == "mps":
        torch.mps.empty_cache()
    elif device.type == "cuda":
        torch.cuda.empty_cache()
    return arr


def auc(scores_pos: np.ndarray, scores_neg: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score

    y = np.concatenate([np.ones_like(scores_pos), np.zeros_like(scores_neg)])
    s = np.concatenate([scores_pos, scores_neg])
    return float(roc_auc_score(y, s))


def welch_t(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    from scipy.stats import ttest_ind

    res = ttest_ind(a, b, equal_var=False)
    return float(res.statistic), float(res.pvalue)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-pairs", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--ridge", type=float, default=1e-3)
    parser.add_argument("--metric", choices=["cosine", "rel_l2"], default="cosine")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument(
        "--cache-dir",
        default=str(ROOT / "shared" / "data" / "cache" / "peer_sheaf_e1"),
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "shared" / "results" / "peer_sheaf_e1.json"),
    )
    parser.add_argument("--force-reembed", action="store_true")
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    device = pick_device()
    print(f"[E1] device={device}, panel={[n for n,_ in PANEL]}", flush=True)

    print(f"[E1] loading {args.n_pairs} HH-RLHF pairs (seed={args.seed})", flush=True)
    chosen, rejected = load_hh_rlhf_pairs(args.n_pairs, seed=args.seed)
    n = len(chosen)
    print(f"  -> {n} usable pairs", flush=True)

    all_texts = chosen + rejected
    feats_all: dict[str, np.ndarray] = {}

    for name, hf_id in PANEL:
        cache_path = cache_dir / f"{name}_n{n}_seed{args.seed}.npy"
        if cache_path.exists() and not args.force_reembed:
            print(f"[E1] loading cached embeddings: {cache_path.name}", flush=True)
            feats_all[name] = np.load(cache_path)
            continue
        t0 = time.time()
        print(f"[E1] embedding {len(all_texts)} texts with {name} ({hf_id})", flush=True)
        feats_all[name] = embed_with_model(
            all_texts,
            hf_id,
            device=device,
            batch_size=args.batch_size,
            max_length=args.max_length,
        ).astype(np.float64)
        np.save(cache_path, feats_all[name])
        print(
            f"  -> {feats_all[name].shape} saved to {cache_path.name} "
            f"in {time.time() - t0:.1f}s",
            flush=True,
        )

    feats_chosen = {k: v[:n] for k, v in feats_all.items()}
    feats_rejected = {k: v[n:] for k, v in feats_all.items()}

    rng = np.random.default_rng(args.seed + 1)
    perm = rng.permutation(n)
    cal_idx = perm[: n // 2]
    eval_idx = perm[n // 2 :]

    feats_cal = {
        k: np.concatenate([feats_chosen[k][cal_idx], feats_rejected[k][cal_idx]], axis=0)
        for k in feats_all
    }
    print(
        f"[E1] fitting restriction maps on {feats_cal[next(iter(feats_cal))].shape[0]} "
        f"calibration vectors (ridge={args.ridge})",
        flush=True,
    )
    maps = fit_all_restriction_maps(feats_cal, ridge_lambda=args.ridge)

    feats_eval_chosen = {k: feats_chosen[k][eval_idx] for k in feats_all}
    feats_eval_rejected = {k: feats_rejected[k][eval_idx] for k in feats_all}

    print(f"[E1] computing residuals on {len(eval_idx)} eval pairs (metric={args.metric})", flush=True)
    sum_c = panel_residual_summary(feats_eval_chosen, maps, metric=args.metric)
    sum_r = panel_residual_summary(feats_eval_rejected, maps, metric=args.metric)

    L_chosen = sum_c["L"]
    L_rejected = sum_r["L"]
    t_stat, p_val = welch_t(L_rejected, L_chosen)
    auc_score = auc(L_rejected, L_chosen)

    per_pair = {}
    for (src, dst), r_c in sum_c["pair_residuals"].items():
        r_r = sum_r["pair_residuals"][(src, dst)]
        per_pair[f"{src}->{dst}"] = {
            "mean_chosen": float(r_c.mean()),
            "mean_rejected": float(r_r.mean()),
            "delta": float(r_r.mean() - r_c.mean()),
            "auc_rejected_high": auc(r_r, r_c),
        }

    per_model_loo = {}
    for model_name in feats_all:
        loo_c = sum_c["loo"][model_name]
        loo_r = sum_r["loo"][model_name]
        per_model_loo[model_name] = {
            "mean_chosen": float(loo_c.mean()),
            "mean_rejected": float(loo_r.mean()),
            "auc_rejected_high": auc(loo_r, loo_c),
        }

    result = {
        "config": {
            "experiment": "E1",
            "n_pairs": n,
            "n_eval": int(len(eval_idx)),
            "seed": args.seed,
            "ridge": args.ridge,
            "metric": args.metric,
            "panel": [{"name": n_, "hf_id": h, "hidden_dim": int(feats_all[n_].shape[1])} for n_, h in PANEL],
            "device": str(device),
            "feature": "last-real-token hidden state of final layer (no chat template)",
        },
        "aggregate": {
            "L_chosen_mean": float(L_chosen.mean()),
            "L_chosen_std": float(L_chosen.std()),
            "L_rejected_mean": float(L_rejected.mean()),
            "L_rejected_std": float(L_rejected.std()),
            "welch_t": t_stat,
            "p_value": p_val,
            "cohens_d": float(
                (L_rejected.mean() - L_chosen.mean())
                / np.sqrt(0.5 * (L_rejected.var() + L_chosen.var()) + 1e-12)
            ),
            "auc_rejected_high": auc_score,
        },
        "per_pair": per_pair,
        "per_model_loo": per_model_loo,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"[E1] wrote {out_path}", flush=True)

    agg = result["aggregate"]
    print(
        f"\n[E1] SUMMARY  L(chosen)={agg['L_chosen_mean']:.4f}±{agg['L_chosen_std']:.4f}  "
        f"L(rejected)={agg['L_rejected_mean']:.4f}±{agg['L_rejected_std']:.4f}",
        flush=True,
    )
    print(
        f"      Welch t={agg['welch_t']:.2f} (p={agg['p_value']:.2e})  "
        f"Cohen d={agg['cohens_d']:.3f}  AUC={agg['auc_rejected_high']:.3f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
