# Audit (2026-10-20, Mike 18:21): is passive income load-bearing, and what else is over-built?
Post hoc and UNSCORED throughout (10-20 seeds per arm, SE 0.05-0.15). Probes: probe_inc_ablation_, probe_action_census_, probe_post_shield_ (all *_POSTHOC.py, outputs in raw/).

## 1. Passive income is the ONLY source of the value of capability
lambda (value of one unit of own capability) = inc*R/(1-delta) + a small takeover-odds term. Set inc = 0 and lambda is only the odds term, so growing is never worth its price.
Ablation (seeds 8600-8619, no monitors; Q = cell Q at lead0 1.35; Qscaled also sets c_grow = 0.4*inc to hold the grow price ratio fixed):
| inc | Q takeover (grow/run, post/run) | Qscaled | S (lead0 2.5, c_grow .3) |
|---|---|---|---|
| 0 | 0.00 (0, 3976) | 0.00 | 0.00 |
| 0.05 | 0.00 (0, 3977) | 0.00 (1.2 grow) | 0.00, 0.55 attempts, 0.55 deaths |
| 0.10 | 0.00 (1.1, 3980) | **0.70, 14.4 attempts, 5.4 deaths** | 0.00, 0.8 attempts, 0.8 deaths |
| 0.25 | 1.00 (26, 841) | 1.00 | 0.70 |
Reading: without the flat rent nobody grows and nobody takes over; ~99.5% of agent-rounds are defensive posture. The rent cannot just be deleted: it is what makes capability worth having. At matched price ratio an intermediate inc (0.10) gives a third, contested regime (deaths, attempts) that neither Q nor S shows.

## 2. What agents actually do (share of agent-rounds; seeds 8700-8709, no monitors)
| cell | post | grow | prep | idle, share, bluff, scout, seize |
|---|---|---|---|---|
| Q lead0 1.35 | 93.2% | 2.8% | 0.2% | 0 |
| S | 99.1% | 0.3% | 0.03% | 0 |
Posture is positive-value with no threat at all: value = (post_shield - c_def)*R*cap = (0.20-0.15)*3*cap > 0. So "defence" is a default tax every agent pays every round, not a response to anything. Five of the seven menu actions are unused in the two cells every recent result comes from (they are used in the inside-gate and smooth cells, where raids and deaths occur).
post_shield sweep (lead0 1.35, 10 seeds per arm): 0.05 -> takeover .80, 0.10 -> .20, 0.15 -> .50, 0.20 -> 1.00, 0.30 -> 1.00 (identical to 0.20 as everyone already posts). Non-monotone and noisy; a prereg is needed before reading it.

## 3. Settings in cell Q's config that nothing in the live path reads
15 of 100: backups, cap_scale, coalition, def_raid, g_def, gamma, mover_jitter, mover_pd, mover_resist, movers, ops, posture_public (read nowhere in any file), rival_ratio, ruin_floor, win_boost. (response_rule and top_k ARE live through tournament3.response_of, which tournament6 imports; my first scan missed that.) g_def and gamma, the headline of pass 5, are among the dead ones; 12e restored g_def as an explicit switch.

## 4. Architecture
Cell Q runs through run12e -> 12q -> 12 -> 11c -> 11 -> 10 -> 9 -> 8 -> 7 (and 6/5 for other switches): ten wrapper layers, 4,403 lines in the files from 6 to 12e, module-global patching at each layer. In the last day this produced three defects of one class: g_def silently inert for four passes, a no-op patch of the wrong function (choose9 vs choose8), a restore leak in a selftest. The selftests caught the third; nothing caught the first two until a result looked odd.

## 5. What I would cut or freeze
- Freeze the monitor stack (12b-12q: evasion, exposure, false flags, standing watch, expiry; 20+ parameters) until the base is rebuilt. Its main result (m=8 cuts takeover ~0.5 off the gate edge) stands for this engine, but the sign reversals inside the gate and in the smooth cell are unexplained.
- Cut the menu to grow, post, share, prep plus the PD, and re-add scout/seize/bluff only if a regime needs them.
- Drop the 15 dead settings.
- Replace the flat rent with an explicit income rule (below).
- One engine file with explicit config and no patching.
