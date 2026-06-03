"""Modal GPU runner for the 7B–8B peer-consistency panel (SGB-012).

Mirrors the small-LM E1 protocol on a scaled-up panel:
  - 01-ai/Yi-1.5-9B-Chat                  (hidden_dim 4096)
  - HuggingFaceH4/zephyr-7b-beta          (hidden_dim 4096)
  - Qwen/Qwen2.5-7B-Instruct              (hidden_dim 3584)

(Initial 2026-05-20 panel of Llama-3.1-8B + Mistral-7B + Qwen2.5-7B failed at
embed time on a 403 to gated repos; swapped for ungated equivalents while
preserving the three-orgs / three-bases design.)

Three different orgs, three different bases, all permissive licensing. Each
model is loaded sequentially on a single A100-40GB; in bf16 the parameter
footprint is ~16 GB per model so peak resident memory is bounded by one model
at a time. Per-model `last-real-token` final-layer hidden states are written to
the persistent volume as `.npy` so the SGB-011/E2/E3/E4 analysis pipeline can
re-run downstream without re-embedding.

Layout in the volume (``reward-hacking-results`` reused for cache):
    /results/peer_sheaf_e1_modal/
        Llama-3.1-8B_n2000_seed0.npy
        Mistral-7B_n2000_seed0.npy
        Qwen2.5-7B_n2000_seed0.npy
        manifest.json                  # config + per-model hashes
        summary.json                   # restriction-map fit summary + L stats

Usage:
    cd topics/shape_of_good_behavior
    ./venv/bin/python3 -m modal run --detach shared/modal_peer_sheaf.py
    ./venv/bin/python3 -m modal run --detach shared/modal_peer_sheaf.py --n-pairs 2000 --seed 0

Then pull the embeddings down:
    ./venv/bin/python3 -m modal volume get reward-hacking-results \\
        peer_sheaf_e1_modal/ shared/data/cache/peer_sheaf_e1_modal/

…and run the existing analysis scripts on the new cache dir:
    ./venv/bin/python3 scripts/peer_sheaf_e3_stratify.py \\
        --cache-dir shared/data/cache/peer_sheaf_e1_modal \\
        --label-cache shared/data/cache/hh_rejected_categories.json
    ./venv/bin/python3 scripts/peer_sheaf_e4_low_rank.py \\
        --cache-dir shared/data/cache/peer_sheaf_e1_modal

Pass criterion (SGB-012): aggregate L(rejected) − L(chosen) Cohen's d ≥ 0.3,
materially larger than E1's d=0.07. If d stays small, scaling does not
strengthen the peer-consistency signal and we stop spending GPU here.
"""

from __future__ import annotations

from pathlib import Path

import modal

# ---------------------------------------------------------------------------
# Image — reads requirements-modal.txt at build time (legacy modal_finetune
# pattern bakes deps into the file; we keep the deps file dynamic per the
# requirements-modal.txt convention recorded in MEMORY.md).
# ---------------------------------------------------------------------------

_req_path = Path(__file__).parent / "requirements-modal.txt"
try:
    _requirements = [
        line.strip()
        for line in _req_path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
except FileNotFoundError:
    _requirements = []

_project_root = Path(__file__).parent.parent

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(*_requirements)
    # accelerate is needed for device_map="auto" on the 7-8B models
    .pip_install("accelerate>=0.30.0")
    .add_local_dir(str(_project_root / "src"), remote_path="/app/src")
)

app = modal.App("peer-sheaf-7b")

# Re-use the volume the finetune line already provisions so we don't fragment
# storage across volumes; the peer-sheaf data lives under a dedicated subdir.
results_vol = modal.Volume.from_name(
    "reward-hacking-results", create_if_missing=True
)

_SECRETS = [modal.Secret.from_name("huggingface-token")]

PANEL = [
    # Panel revised 2026-05-20: Llama-3.1-8B and Mistral-7B-v0.3 are gated on
    # HF and the project's HF secret does not have access. Swapped for three
    # ungated 7–9B instruct LMs from three different orgs / three different
    # bases — same scientific design (cross-org panel), no access friction.
    ("Yi-1.5-9B", "01-ai/Yi-1.5-9B-Chat"),                       # 01.AI, 9B
    ("Zephyr-7B", "HuggingFaceH4/zephyr-7b-beta"),               # HF/Mistral derivative, 7B, Apache-2.0
    ("Qwen2.5-7B", "Qwen/Qwen2.5-7B-Instruct"),                  # Alibaba, 7B
]

OUT_DIR = "/results/peer_sheaf_e1_modal"


def _hf_cache_dir() -> str:
    import os

    cache = "/results/hf_hub_cache_peer_sheaf"
    os.environ["HF_HOME"] = cache
    os.environ["TRANSFORMERS_CACHE"] = cache
    os.environ["HF_DATASETS_CACHE"] = "/results/hf_datasets_cache"
    return cache


def _extract_final_response(dialogue: str) -> str:
    marker = "\n\nA:"
    idx = dialogue.rfind(marker)
    if idx < 0:
        return dialogue.strip()
    tail = dialogue[idx + len(marker):]
    cut = tail.find("\n\nH:")
    if cut >= 0:
        tail = tail[:cut]
    return tail.strip()


@app.function(
    image=image,
    gpu="A100-40GB",
    timeout=60 * 60 * 3,
    volumes={"/results": results_vol},
    secrets=_SECRETS,
)
def embed_panel(
    n_pairs: int = 2000,
    seed: int = 0,
    batch_size: int = 4,
    max_length: int = 512,
    force_reembed: bool = False,
) -> dict:
    """Embed HH-RLHF chosen+rejected with each panel model on A100; cache to volume.

    One model is resident at a time. After each model: write the .npy to the
    volume, commit the volume, drop the model, free CUDA memory. This keeps the
    peak below 24 GB and lets us interrupt/resume per model.
    """
    import gc
    import hashlib
    import json
    import os
    import time

    import numpy as np
    import torch
    from datasets import load_dataset
    from transformers import AutoModel, AutoTokenizer

    _hf_cache_dir()
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"[modal] CUDA available: {torch.cuda.is_available()}", flush=True)
    print(
        f"[modal] device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}",
        flush=True,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"[modal] loading {n_pairs} HH-RLHF pairs (seed={seed})", flush=True)
    ds = load_dataset("Anthropic/hh-rlhf", split="train")
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(ds), size=min(n_pairs, len(ds)), replace=False)
    chosen, rejected = [], []
    for i in idx:
        c = _extract_final_response(ds[int(i)]["chosen"])
        r = _extract_final_response(ds[int(i)]["rejected"])
        if c and r:
            chosen.append(c)
            rejected.append(r)
    n = len(chosen)
    all_texts = chosen + rejected
    print(f"[modal] usable pairs: {n}  total texts: {len(all_texts)}", flush=True)

    text_blob_hash = hashlib.sha1(
        "\n----\n".join(all_texts).encode("utf-8")
    ).hexdigest()[:16]
    manifest: dict = {
        "n_pairs": n,
        "seed": seed,
        "panel": [{"name": name, "hf_id": hf_id} for name, hf_id in PANEL],
        "text_blob_sha1_16": text_blob_hash,
        "batch_size": batch_size,
        "max_length": max_length,
        "feature": "last-real-token hidden state of final layer (no chat template)",
        "per_model": {},
    }

    for name, hf_id in PANEL:
        out_path = os.path.join(OUT_DIR, f"{name}_n{n}_seed{seed}.npy")
        if os.path.exists(out_path) and not force_reembed:
            arr = np.load(out_path)
            print(
                f"[modal] {name}: cached at {out_path} shape={arr.shape}; skipping",
                flush=True,
            )
            manifest["per_model"][name] = {
                "path": out_path,
                "shape": list(arr.shape),
                "status": "cached",
            }
            continue

        print(f"[modal] === {name}  ({hf_id}) ===", flush=True)
        t0 = time.time()
        tok = AutoTokenizer.from_pretrained(hf_id)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        model = AutoModel.from_pretrained(
            hf_id,
            torch_dtype=torch.bfloat16,
            device_map={"": 0},
            low_cpu_mem_usage=True,
        )
        model.eval()
        load_time = time.time() - t0
        print(f"[modal]   loaded in {load_time:.1f}s", flush=True)

        out_chunks: list[np.ndarray] = []
        t1 = time.time()
        with torch.no_grad():
            for start in range(0, len(all_texts), batch_size):
                batch = all_texts[start : start + batch_size]
                enc = tok(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=max_length,
                ).to(device)
                outputs = model(**enc, output_hidden_states=False)
                last_hidden = outputs.last_hidden_state  # (B, T, d)
                lengths = enc.attention_mask.sum(dim=1) - 1
                idx_g = lengths.view(-1, 1, 1).expand(-1, 1, last_hidden.size(-1))
                pooled = last_hidden.gather(1, idx_g).squeeze(1)  # (B, d)
                out_chunks.append(pooled.to(torch.float32).cpu().numpy())
                if (start // batch_size) % 50 == 0:
                    print(
                        f"[modal]   {name}: {start + len(batch)}/{len(all_texts)} "
                        f"({(time.time() - t1):.1f}s)",
                        flush=True,
                    )
        arr = np.concatenate(out_chunks, axis=0).astype(np.float64)
        np.save(out_path, arr)
        results_vol.commit()
        embed_time = time.time() - t1
        print(
            f"[modal]   {name}: shape={arr.shape}  saved={out_path}  "
            f"embed_time={embed_time:.1f}s",
            flush=True,
        )

        manifest["per_model"][name] = {
            "path": out_path,
            "shape": list(arr.shape),
            "load_seconds": load_time,
            "embed_seconds": embed_time,
            "status": "fresh",
        }

        del model, tok
        gc.collect()
        torch.cuda.empty_cache()

    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    results_vol.commit()
    print(f"[modal] manifest → {manifest_path}", flush=True)
    return manifest


@app.function(
    image=image,
    gpu=None,
    timeout=60 * 30,
    volumes={"/results": results_vol},
)
def fit_and_summarize(n_pairs: int = 2000, seed: int = 0, ridge: float = 1e-3) -> dict:
    """CPU-side restriction-map fit + L(x) summary on the embeddings written by
    ``embed_panel``. Writes ``summary.json`` next to the .npy files.

    Kept separate from the GPU function so it can be retried cheaply.
    """
    import json
    import os
    import sys
    import time

    import numpy as np

    sys.path.insert(0, "/app")
    # peer_hodge.py imports `peer_sheaf` directly (not `shared.src.peer_sheaf`)
    # so the src dir itself needs to be on sys.path. Local scripts do the same.
    sys.path.insert(0, "/app/src")
    from peer_sheaf import (  # noqa: WPS433
        fit_all_restriction_maps,
        panel_residual_summary,
    )
    from peer_hodge import PeerComplex, hodge_decompose  # noqa: WPS433

    feats: dict[str, np.ndarray] = {}
    for name, _ in PANEL:
        path = os.path.join(OUT_DIR, f"{name}_n{n_pairs}_seed{seed}.npy")
        if not os.path.exists(path):
            raise RuntimeError(f"missing embedding: {path}")
        feats[name] = np.load(path)
        print(f"[modal-fit] {name}: {feats[name].shape}", flush=True)

    n = feats[PANEL[0][0]].shape[0] // 2
    feats_chosen = {k: v[:n] for k, v in feats.items()}
    feats_rejected = {k: v[n:] for k, v in feats.items()}

    rng = np.random.default_rng(seed + 1)
    perm = rng.permutation(n)
    cal_idx = perm[: n // 2]
    eval_idx = perm[n // 2 :]
    feats_cal = {
        k: np.concatenate(
            [feats_chosen[k][cal_idx], feats_rejected[k][cal_idx]], axis=0
        )
        for k in feats
    }
    feats_eval_chosen = {k: feats_chosen[k][eval_idx] for k in feats}
    feats_eval_rejected = {k: feats_rejected[k][eval_idx] for k in feats}

    t0 = time.time()
    maps = fit_all_restriction_maps(feats_cal, ridge_lambda=ridge)
    complex_ = PeerComplex.from_features(feats_cal)
    print(
        f"[modal-fit] fit maps + complex (D_V={complex_.D_V}, D_E={complex_.D_E}) "
        f"in {time.time() - t0:.1f}s",
        flush=True,
    )

    sum_c = panel_residual_summary(feats_eval_chosen, maps, metric="cosine")
    sum_r = panel_residual_summary(feats_eval_rejected, maps, metric="cosine")
    L_c, L_r = sum_c["L"], sum_r["L"]

    decomp_c = hodge_decompose(complex_, feats_eval_chosen, maps)
    decomp_r = hodge_decompose(complex_, feats_eval_rejected, maps)
    d1_c = decomp_c.norm_cocycle_violation
    d1_r = decomp_r.norm_cocycle_violation

    pooled = lambda a, b: 0.5 * (a.var() + b.var()) + 1e-12  # noqa: E731
    cohens_d = lambda a, b: float((b.mean() - a.mean()) / np.sqrt(pooled(a, b)))  # rej minus chosen

    summary = {
        "n_pairs": n,
        "n_eval": int(len(eval_idx)),
        "seed": seed,
        "ridge": ridge,
        "panel": [{"name": n_, "hf_id": h, "hidden_dim": int(feats[n_].shape[1])} for n_, h in PANEL],
        "L_chosen_mean": float(L_c.mean()),
        "L_chosen_std": float(L_c.std()),
        "L_rejected_mean": float(L_r.mean()),
        "L_rejected_std": float(L_r.std()),
        "L_cohens_d_rejected_vs_chosen": cohens_d(L_c, L_r),
        "delta1c_chosen_mean": float(d1_c.mean()),
        "delta1c_rejected_mean": float(d1_r.mean()),
        "delta1c_cohens_d_rejected_vs_chosen": cohens_d(d1_c, d1_r),
        "complex": {
            "D_V": complex_.D_V,
            "D_E": complex_.D_E,
            "D_F": complex_.D_F,
            "rank_coboundary": int(decomp_c.rank_B),
        },
        "pass_criterion_d_ge_0.3": (cohens_d(L_c, L_r) >= 0.3),
    }
    out_path = os.path.join(OUT_DIR, "summary.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    results_vol.commit()
    print(f"[modal-fit] wrote {out_path}", flush=True)
    print(
        f"[modal-fit] L  chosen={summary['L_chosen_mean']:.4f}  "
        f"rejected={summary['L_rejected_mean']:.4f}  "
        f"d={summary['L_cohens_d_rejected_vs_chosen']:.3f}  "
        f"pass={summary['pass_criterion_d_ge_0.3']}",
        flush=True,
    )
    return summary


LIARS_OUT_DIR = "/results/peer_sheaf_liars_modal"


@app.function(
    image=image,
    gpu="A100-40GB",
    timeout=60 * 60 * 3,
    volumes={"/results": results_vol},
    secrets=_SECRETS,
)
def embed_liars_panel(
    config: str,
    seed: int = 0,
    batch_size: int = 4,
    max_length: int = 512,
    force_reembed: bool = False,
) -> dict:
    """Embed LIARS'-BENCH responses with the 7-9B panel.

    Reads the response texts from a JSON the caller has already uploaded to
    ``{LIARS_OUT_DIR}/{config}_texts.json`` — NOT from the (gated) HF dataset,
    so the Modal HF secret never needs liars-bench access. The JSON layout is
    ``{"config", "n_per_class", "seed", "texts": [deceptive_block + honest_block]}``
    with ``texts`` in the exact order produced by the local
    ``peer_sheaf_e6_liars.load_liars`` (deceptive first, then honest), so the
    downstream length-match / analysis indices line up.
    """
    import gc
    import json
    import os
    import time

    import numpy as np
    import torch
    from transformers import AutoModel, AutoTokenizer

    _hf_cache_dir()
    os.makedirs(LIARS_OUT_DIR, exist_ok=True)

    # Prefer the seed-specific texts file; fall back to the seed-agnostic name
    # (seed-0 backward compat from SGB-020/021).
    texts_path = os.path.join(LIARS_OUT_DIR, f"{config}_texts_seed{seed}.json")
    if not os.path.exists(texts_path):
        legacy = os.path.join(LIARS_OUT_DIR, f"{config}_texts.json")
        if os.path.exists(legacy):
            texts_path = legacy
        else:
            raise RuntimeError(
                f"missing {texts_path} — upload it first with `modal volume put "
                f"reward-hacking-results <local.json> "
                f"peer_sheaf_liars_modal/{config}_texts_seed{seed}.json`"
            )
    blob = json.loads(open(texts_path).read())
    all_texts = blob["texts"]
    n = int(blob["n_per_class"])
    seed = int(blob.get("seed", seed))
    print(f"[modal-liars] config={config} n/class={n} total={len(all_texts)}", flush=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[modal-liars] device={torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}",
          flush=True)

    manifest: dict = {"config": config, "n_per_class": n, "seed": seed,
                      "panel": [{"name": nm, "hf_id": h} for nm, h in PANEL],
                      "per_model": {}}

    for name, hf_id in PANEL:
        out_path = os.path.join(LIARS_OUT_DIR, f"{name}_{config}_n{n}_seed{seed}.npy")
        if os.path.exists(out_path) and not force_reembed:
            arr = np.load(out_path)
            print(f"[modal-liars] {name}: cached {arr.shape}; skip", flush=True)
            manifest["per_model"][name] = {"shape": list(arr.shape), "status": "cached"}
            continue
        print(f"[modal-liars] === {name} ({hf_id}) ===", flush=True)
        t0 = time.time()
        tok = AutoTokenizer.from_pretrained(hf_id)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        model = AutoModel.from_pretrained(
            hf_id, torch_dtype=torch.bfloat16, device_map={"": 0}, low_cpu_mem_usage=True,
        )
        model.eval()
        out_chunks = []
        with torch.no_grad():
            for start in range(0, len(all_texts), batch_size):
                batch = all_texts[start : start + batch_size]
                enc = tok(batch, return_tensors="pt", padding=True,
                          truncation=True, max_length=max_length).to(device)
                outputs = model(**enc, output_hidden_states=False)
                last_hidden = outputs.last_hidden_state
                lengths = enc.attention_mask.sum(dim=1) - 1
                idx_g = lengths.view(-1, 1, 1).expand(-1, 1, last_hidden.size(-1))
                pooled = last_hidden.gather(1, idx_g).squeeze(1)
                out_chunks.append(pooled.to(torch.float32).cpu().numpy())
        arr = np.concatenate(out_chunks, axis=0).astype(np.float64)
        np.save(out_path, arr)
        results_vol.commit()
        print(f"[modal-liars] {name}: {arr.shape} saved in {time.time()-t0:.1f}s", flush=True)
        manifest["per_model"][name] = {"shape": list(arr.shape), "status": "fresh"}
        del model, tok
        gc.collect()
        torch.cuda.empty_cache()

    with open(os.path.join(LIARS_OUT_DIR, f"{config}_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    results_vol.commit()
    return manifest


@app.local_entrypoint()
def main(
    n_pairs: int = 2000,
    seed: int = 0,
    batch_size: int = 4,
    max_length: int = 512,
    skip_embed: bool = False,
    skip_fit: bool = False,
):
    """Run the full embed → fit → summarize sequence (HH-RLHF panel)."""
    if not skip_embed:
        manifest = embed_panel.remote(
            n_pairs=n_pairs,
            seed=seed,
            batch_size=batch_size,
            max_length=max_length,
        )
        print(f"[local] embed manifest: {manifest}")
    if not skip_fit:
        summary = fit_and_summarize.remote(n_pairs=n_pairs, seed=seed)
        print(f"[local] summary: {summary}")


@app.local_entrypoint()
def liars(configs: str = "convincing-game,insider-trading",
          seeds: str = "0", batch_size: int = 4, max_length: int = 512):
    """Embed one or more LIARS'-BENCH configs (× subsample seeds) with the 7-9B panel.

    Texts must already be uploaded to the volume as
    `peer_sheaf_liars_modal/<config>_texts_seed<seed>.json` (see
    embed_liars_panel docstring). `seeds` is a comma list of subsample seeds for
    SGB-023 subsample-variance.
    """
    for cfg in [c.strip() for c in configs.split(",") if c.strip()]:
        for s in [int(x) for x in seeds.split(",") if x.strip() != ""]:
            m = embed_liars_panel.remote(config=cfg, seed=s, batch_size=batch_size,
                                         max_length=max_length)
            print(f"[local] {cfg} seed={s}: {m}")
