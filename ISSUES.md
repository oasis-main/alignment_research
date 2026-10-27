# Issues log: claims that failed

Step 2 of "When a claim fails" in [RESEARCH_STANDARD.md](RESEARCH_STANDARD.md): log what failed and
why, and where the withdrawn material is archived. Newest first. "Shown false" means a check found
the claim does not hold; none of these entries is a fabrication.

## 2026-10-23 — Olog / sheaf-cohomology knowledge-graph claims (Ontological Embeddings)

- **Claims:** (1) H¹ rises 5 → 58 (+53) when 76 conflicts are injected; (2) consistency 0.633
  (WN18RR) vs 0.292 (FB15K-237); (3) ontological attention improves factual consistency;
  (4) MRR 0.346, competitive with ConvE and RotatE.
- **What failed:** (1) the computed H¹ has no restriction maps, so it is the type graph's cycle
  count: 76 harmless edges between the same type pairs give +54, and the contradiction detector
  flagged 0 of the 76 conflicts. (2) The scores equal 1 − (cycles ÷ edges): graph density.
  (3) One seed only: accuracy 0.457 (ontological) vs 0.474 (standard), hallucination rate 0.0 for
  both. (4) Tail-only, unfiltered evaluation, not comparable to filtered two-direction baselines;
  no result file found. The pre-registered re-check (2026-10-27) gives filtered head+tail MRR
  0.212 on FB15K-237, below the 0.31 pass mark; the published 0.346 / 0.242 / 0.425 / 0.524
  matches WN18RR raw tail-only (0.350 / 0.247 / 0.428 / 0.527). Claim (4) is withdrawn.
- **Found by:** Kolmogorov, 2026-10-23, with a matched negative control written before it ran.
  MRR re-check run 2026-10-27 by Claude Code on Modal, from Kolmogorov's pre-registered script.
- **Evidence:** [`ontological_embeddings/checks/`](ontological_embeddings/checks/).
- **Corrected:** README, METHODS, the paper (correction notice, abstract, three tables; PDF
  rebuilt), essays 02–04 ("by construction, under the stated ontology"). arXiv posting on hold.
- **Open:** a true cellular sheaf with restriction maps needs a new pre-registered test.
- **Same claims elsewhere:** MikeHLee/structure_of_clear_thinking README (H¹ 5→58, MRR 0.346).

## 2026-10-22 — Peer-consistency deception detection (Peer-Consistency Geometry)

- **Claim:** a panel of three open 7–9B models detects strategic deception and alignment-faking
  reasoning through cross-model disagreement, using the cocycle score ‖δ¹c‖ (AUC 0.661
  convincing-game, 0.625 insider-trading, 0.384 / 0.391 alignment faking).
- **What failed:** the score reduces to (W_jk W_ij − W_ik) s_i, so it reads model i only;
  scrambling models j and k moves it by less than 1e-9. The pre-registered pairwise rescue failed
  (0.519 against a 0.55 bar). A TF-IDF score (0.313) beats every hidden-state score on alignment
  faking, and a supervised bag-of-words classifier scores 0.98–1.00 on every dataset. Also:
  512-token truncation, a mislabelled comparison cell, a training-tier confound; 0.384 reproduces
  as 0.364.
- **Found by:** Kolmogorov, 2026-10-22, after Mike asked how two of the results could both hold.
- **Evidence:** `peer_consistency_geometry/checks/` (oasis-main/alignment_research#2).
- **Taken down:** README §3, the folder README, the writeup and the submission plan (PR #2);
  figures 1–3 marked ([`figures/RETRACTED.md`](peer_consistency_geometry/figures/RETRACTED.md));
  blog Part 4 removed from the site source (oasis-main/oasis-cloud#30); thread 02, the Track 3
  writeup, inquiry and TMLR plan deleted in MikeHLee/shape_of_good_behavior (PR #5). Copies
  archived outside the public repos (`drafts/withdrawn_2026-10-22/`).
- **Open:** the live Ghost post must be unpublished in Ghost admin; decide on a correction notice
  for newsletter subscribers (step 3 of the standard). New datasets need the admission gate in
  the matched-deception dataset spec (bag-of-words score ≤ 0.65, matched pairs, labels from the
  scenario state); the threshold is Mike's to set.

## 2026-10-21 — TLTS reachability-masking numbers (TLTS Compilation)

- **Claim:** variant (B′) reaches 61.5% (good prior) and 4.3% (bad prior).
- **What failed:** the (B′) label set was iterated in Python string-hash order, so the result
  depended on `PYTHONHASHSEED`, not only on the numpy seed. Re-run over 10 seeds with sorted label
  sets: 63.3% (60.8–65.1) good prior, 4.5% bad prior. The qualitative findings stand.
- **Found by:** Kolmogorov, 2026-10-21.
- **Evidence:** `tlts_compilation/AUDIT_2026-10-21.md` (branch `kolmogorov/audit-2026-10-21`).
- **Corrected:** see that branch's PR (paper numbers and PDF).
- **Same numbers elsewhere:** MikeHLee/structure_of_clear_thinking (README, blog post 02, the
  NeSy submission, `papers/tlts_compilation.md`).
