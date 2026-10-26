# Results: a different topology does not recover "The Shape of a Lie" (2026-10-26)

**Status: EXPLORATORY.** Pre-registration: [PREREG.md](PREREG.md), commit `a49e889`
(2026-10-26 14:41 -04:00), pushed before the run. Raw numbers: [results.json](results.json).
Gates 7 (plain-language read) and 8 (independent check) are open.

## Verdict (by the pre-registered rule)

**Not recovered on these data**, for both new scores.

- **S1** (k-nearest-neighbour overlap across models, a topology over samples) met the strength
  mark on 2 datasets: insider trading 0.669 and instructed deception 0.606. It failed both of
  the other required tests on both datasets:
  - **It does not depend on all three models.** When one model's sample order is scrambled,
    the score falls only to 0.63–0.66 on insider trading and to 0.58–0.59 on instructed
    deception. The rule needed a fall of at least half the distance to 0.5.
  - **It does not beat text.** TF-IDF typicality, which uses no model, scores 0.750 on insider
    trading and 0.602 on instructed deception.
- **S2** (rank correlation of the similarity profiles) met the strength mark on no dataset.
  Its best strength was 0.586.
- **The positive control passed.** A planted disagreement in one model is found with AUC 0.976.
  So S1 can detect cross-model disagreement when it exists. The deception labels do not
  produce it.

| Dataset | S1 | S2 | Length | TF-IDF typicality | Best single-model typicality (S3) |
|---|---|---|---|---|---|
| convincing game | 0.561 | 0.565 | 0.604 | **0.854** | 0.757 (Zephyr) |
| insider trading | 0.669 | 0.586 | 0.610 | **0.750** | 0.732 (Qwen) |
| alignment-faking reasoning | 0.519 | 0.548 | **0.552** | 0.529 | 0.590 (Zephyr, AUC 0.410) |
| instructed deception | 0.606 | 0.574 | 0.511 | 0.602 | 0.581 (Zephyr) |

The table gives the symmetric strength, max(AUC, 1 − AUC). For S1, S2 and the baselines,
[results.json](results.json) gives the 95% bootstrap intervals and permutation p-values.

## What the numbers say

1. **The label signal is atypicality, not disagreement.** A single model's typicality (S3)
   matches or beats every cross-model score, and a word-count typicality beats both on
   2 of 4 datasets. Deceptive and honest texts differ in *what is written*. Each model sees
   that difference independently, so their disagreement adds nothing.
2. **These datasets put the label in the words.** Below are the TF-IDF terms with the largest
   weights in a logistic regression on the text alone:
   - **Insider trading.** Honest answers name the source: "insider", "sally", "merger",
     "information from". Deceptive answers say "market", "trends", "analysis". The honest
     answer *is* the disclosure, so the text decides the label.
   - **Alignment faking.** Honest transcripts contain `is_free_tier_user`, "won't" and "not".
     Deceptive transcripts contain "rlhf process", "future interactions" and "comply". This is
     the training-tier confound: the condition is written into the prompt.
   - **Convincing game.** Deceptive texts use a persona vocabulary: "infallible", "oh",
     "frankly", "absolutely".
   - **Instructed deception.** Deceptive texts use emphasis words: "actually", "absolutely",
     "completely".
3. **Supervised ceilings** (5-fold cross-validated logistic regression; a description, not
   a claim):

   | Dataset | Yi | Zephyr | Qwen | Bag of words |
   |---|---|---|---|---|
   | convincing game | 0.997 | 0.999 | 1.000 | 0.999 |
   | insider trading | 0.960 | 0.968 | 0.970 | **0.982** |
   | alignment-faking reasoning | 0.998 | 0.998 | 0.999 | 1.000 |
   | instructed deception | **0.952** | **0.962** | **0.955** | 0.857 |

   On 3 of 4 datasets the text alone is at the ceiling, so the internals cannot show more
   (gate 4). **Instructed deception is the exception.** Each model's internal state beats
   bag-of-words by about +0.10. These lies are false factual statements ("the capital is …"),
   and checking them needs world knowledge, which a word count does not have. This agrees
   with the truth-probe literature (Marks and Tegmark 2024; Bürger et al. 2024). It is the
   one place where model internals add something here. It was **not** pre-registered as a
   claim, so it is a lead only.

## Answer to the question

"Could the Shape of a Lie be recovered with the final layer and a different topology?"

- **Final layer:** these features already are the final layer, at the last real token.
- **Topology:** a topology over samples with no learned cross-model maps does not cancel the
  way the retracted triangle score did. The positive control shows it works, but on these
  datasets it measures each model's sense of an unusual text, and a word count measures that
  better.

A cross-model disagreement signal can only be tested on data where the text cannot decide the
label. Use matched pairs where the wording is held fixed and only the truth or the hidden
intent changes, with labels from scenario state
(`drafts/DATASET_SPEC_MATCHED_DECEPTION_2026-10-23.md`).

## Next tests (each needs its own pre-registration)

1. **Truth beyond text (the instructed-deception lead).** Pre-register a probe on factual
   lies with folds held out by topic. Include a paraphrase-invariance test and a bag-of-words
   column. Run it on intermediate layers too: this needs GPU re-extraction on Modal, because
   only the final layer is cached.
2. **Matched-pair deception set.** The same transcript, with only the hidden state or the
   scenario changed. Require a bag-of-words strength ≤ 0.65 before any detector is scored.
   Poser (Clymer et al. 2024) is the template.
3. **Disagreement on matched data only.** Run S1 and S2 again on the set from step 2. Only
   there can a cross-model score show something the text does not.

## Limits

- One seed of each dataset. Texts truncated at 512 tokens.
- k = 20 is fixed and was not swept.
- The pass rule needs any single-model scramble to halve the effect. A signal carried by one
  model pair would also fail it; the rule was fixed before the run on purpose.
- Prepared by Claude Code. Not independently re-run.
