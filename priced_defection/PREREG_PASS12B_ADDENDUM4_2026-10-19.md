# Pass 12b pre-registration, ADDENDUM 4 (written 2026-10-19 ~18:45 UTC, before any scored 12b run)

Source: UNSCORED control `calibrate_pass12b_fp.py` (seeds 2000-2029, n=30 per arm, `raw/calibration_pass12b_fp.txt`). Monitors that read NOTHING (r=0) but flag falsely still change the outcome a great deal:

| cell, m | p_fp = 0 | 0.002 | 0.01 |
|---|---|---|---|
| D0, m=2 | takeover .633 | .533 | .067 |
| D0, m=4 | .633 | .367 | .000 |
| D0, m=8 | .633 | .200 | .000 |
| CL, m=8 | .700 | .267 | .100 |

Mechanism (my reading, not tested): a false flag sanctions a random non-preparing agent, partners defect against it, its budget stops growing, and the future mover is among the sanctioned. A random-punishment regime therefore deters by starving everyone, which is not the monitor's read effect. At p_fp=0.01 it is a near-blanket sanction (PD income per agent-round falls from 2.36 to 1.50 at m=8).

Consequences, decided before the scored run:
1. TWIN CONTROLS. Every arm with p_fp > 0 gets a twin with r=0 and everything else identical (same seeds, same monitor set, same false-flag stream). The monitor's read effect is the paired difference arm minus twin. All scoring of M5, M6, M7, M7b uses this decomposition, and the raw arm is reported alongside.
2. M5 is scored two ways. (a) as written: F=1 income at p_fp=0.002 vs p_fp=0, m=8, r=0.9, D0. (b) the decomposition: the read effect on takeover (r=0.9 minus r=0 twin at p_fp=0.002, m=8, D0). Neither is allowed to be described as "false flags cost income" if the raw income difference is positive. The calibration already shows income can RISE with false flags when takeover falls (D0, m=4, p=.002: F=1 income 1.947 vs 1.912), because the floor assumption makes a takeover the dominant loss. I flag that as a property of the welfare measure, not a recommendation.
3. NEW PREDICTION M9 (decomposition): in D0 at m=8, p_fp=0.002, the read effect on takeover (r=0.9 minus r=0 twin) is negative with CI excluding 0. Probability 0.65. (r=0.9 alone at m=8 has been predicted to bring takeover below 0.2; with 0.2 already reached by flags alone the remaining room is small, which is why this is not higher.)
4. M7 and M7b: scored on NET F=1 income as in Addendum 3, but the interior-optimum question is asked of the READ EFFECT NET OF TWIN as well: is net(r=0.9) minus net(r=0 twin) highest at an interior m? Stated probability unchanged (M7 0.35, M7b 0.45); the twin version is reported as the primary reading and the raw as secondary.
5. ARM LIST FIXED (seeds 1000-1059, 60 per arm): cells D0 and CL; G (m in {0,1,2,4,8} x r in {.3,.9}); H (m=4: c=.5,r=.9 and c=1,r=.45); E (m=4, r=.9, e in {.5,.8}; e=0 is G); F (m in {2,4,8}, r=.9, three settings: p_fp=.002 no exposure; p_fp=.002 with exposure; p_fp=0 with exposure); C (m in {2,4,8}, r=.9, c_mon=.05, p_fp=.002, exposure on); S (m in {2,4}, r=.9, c_mon=.05, p_fp=.01, exposure on). Every F, C, S arm with p_fp>0 gets its r=0 twin (same p_fp, exposure, c_mon, e). Twins for p_fp=0 arms are the G arm with r=0 (m>0, r=0 equals m=0 by identity I2), so no extra arms.

Nothing else changes: mechanism, identity checks, M1-M4, M6, M8, limits, seeds.

Added limit: with p_fp fixed independent of r, the false-flag channel is a separate policy lever (random sanctioning) that this pass cannot distinguish from a miscalibrated reader. Naming it a "Blackstone cost" holds for the innocents sanctioned; it must not be read as evidence that surveillance as such deters.
