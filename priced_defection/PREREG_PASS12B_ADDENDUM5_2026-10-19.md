# Pass 12b pre-registration, ADDENDUM 5 (written 2026-10-19 ~18:55 UTC, before any scored 12b run)

Correction to Addendum 4, item 5. I wrote that twins for the p_fp = 0 arms are "the G arm with r=0, so no extra arms". That is wrong for the exposure-only arms (p_fp = 0, expose on): identity I2 only says m>0 with ALL effects off equals m=0. An r=0 arm with exposure on is not m=0, because exposure sanctions the monitors for a round at a time. Those arms need their own r=0 twin.

Fix: add the exposure-only twin T_F_x_m (m in {2, 4, 8}, r=0, p_fp=0, expose on) in both cells. Arm count becomes 41 per cell, 82 in total, 60 seeds each (4,920 runs).

Clarification: a twin shares the monitor set, the readability matrix and the generators' seeds with its pair, but the false-flag and exposure draws are consumed per round, so once the two runs diverge (a mover that is noticed behaves differently) the draw sequences are no longer aligned. The twin is therefore a matched control, not a draw-for-draw clone. Paired bootstrap over seeds handles that; I will not describe the twin difference as exactly isolating the read effect.

Nothing else changes.
