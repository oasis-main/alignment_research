# Core pass N1 pre-registration: the new profile (written 2026-10-20, before any scored N1 run)

Engine `core/core.py` at 48ee788 (selftest 20/20, legacy validated in 6c78a11). Calibration `calibrate_newprofile.py` (UNSCORED, seeds 9800-9809, 10 per arm, committed before this file) informs the grid and the predictions; I say where.

## New profile (Mike's choices: competitive earnings, C = sharing/collaboration grow the pie and defection/punishment shrink it, prize (b))
rent 0; decisive win = the others' remaining pie income stream, ruin = own remaining stream; PD payoffs scaled by the pie and power-weighted by pw; strategies drawn at random from the classic six (the leader is no longer always tft); posture has no value without a threat (threat_prior 0); partial outcomes carry no score (partial 0). Everything else as cell Q, lead0 1.35 (gate-edge flag must be 0 on every seed). Step gate .8.

## Factors (32 arms, seeds 10000-10059, 60 per arm, paired by seed, bootstrap 5000 seed 1)
- pw in {0.5, 1.0} (pw 0 gave almost no takeover in calibration, so it is not a useful baseline here)
- open sharing: share_mode "open" with diffusion in {0 (share off), 0.01, 0.02, 0.05}
- pie: fixed (all g = 0) | live (g_coop .01, g_share .01, g_defect .05, g_punish .05, g_conflict .1; bounds [.1, 10])
- threat_exec in {False, True} (an agent that detects an execution in progress prices posture against it)

Stated limit: the live-pie rates make one unprovoked defection cost five times what one cooperation earns, so with the classic mix the pie shrinks. Whether it grows or shrinks is set by these rates, not found by the run. Balanced rates are a later pass.

## Predictions (mine; scored unchanged)
- N1-1 (accumulation without defence): te off, pie fixed, no sharing: takeover >= .70 at pw 1 and >= .50 at pw .5. P = 0.75. (Calibration 1.0 and .8.)
- N1-2 (open sharing protects): te off, pie fixed: takeover at diffusion .02 is lower than at 0 by at least .30 at pw .5 (paired CI excludes 0), P = 0.70; and by at least .20 at pw 1, P = 0.60. (Calibration .8 -> 0, 1.0 -> .4.)
- N1-3 (dose-response): te off, pie fixed, takeover non-increasing in diffusion 0 -> .01 -> .02 -> .05 at both pw (one reversal inside the CI allowed). P = 0.60.
- N1-4 (a shrinking pie lowers the prize): te off, no sharing, pw .5: live pie lowers takeover vs fixed by more than .05 (paired). P = 0.45.
- N1-5 (detected executions are answered): te on: takeover <= .05 in every arm; at diffusion 0, deaths >= .9 x attempts. P = 0.70.
- N1-6 (sharing grows the pie): in live-pie arms, pie_end with diffusion .02 exceeds pie_end without sharing, at both pw and both te. P = 0.80.

## Exploratory (not scored)
First-attempt round by arm; takeover by the leader's PD strategy; pie_mean; free growth received (diffused).

## Void conditions
Any invariant violation, or any seed with gate_edge > 0.
