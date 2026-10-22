# Pass 12b pre-registration, ADDENDUM 1 (written 2026-10-19 ~18:30 UTC, before any 12b harness code or run)

Supersedes the false-flag rate in PREREG_PASS12B_2026-10-19.md (commit 618181b). Reason, found by arithmetic only (no simulation): with p_fp = 0.02 per monitor per readable agent per round and a false sanction of L_fp = 10 rounds, N = 20, c = 1, the expected number of agents under a false sanction at once is about 7.6 (m=2), 15.2 (m=4), 20 (m=8, saturated). That is not a Blackstone-style marginal cost; it is a blanket sanction that would swamp every other effect and make M5 and M7 unreadable. The original value was a placeholder I did not check before committing.

## Changes
- p_fp primary value: 0.002 (about 0.8, 1.5 and 3.0 agents sanctioned at once at m = 2, 4, 8, by the same arithmetic). Wherever the original says p_fp = 0.02, read 0.002. Arms F and C use 0.002.
- New sensitivity arms (both cells, m in {2, 4}, r=0.9, c=1, e=0, expose on, c_mon=0.05): p_fp = 0.01. About 3.8 and 7.6 agents sanctioned at once. Reported separately and labelled as the high false-flag regime.
- Probabilities updated for the new rate, before any run: M5 stays 0.70 -> 0.75 (m=8, p_fp=0.002, F=1 income lower than p_fp=0 by more than 0.03; a sanctioned agent loses a large share of its game income so ~3 of 20 should show). M7 (interior optimum at p_fp=0.002, exposure on, c_mon=0.05): 0.45 -> 0.35, because false flags are now cheap and monitors may simply be better in numbers. New M7b: at p_fp=0.01 the best m among {0, 2, 4} (m=8 not run at this rate) is interior (m=2) in D0 or CL: 0.45.
- Everything else in the original (mechanism, cells, seeds 1000-1059, identity checks I1-I5, M1-M4, M6, M8, limits) stands unchanged.

## Process note
The original was committed with the 0.02 value; this addendum is a visible correction, not a rewrite. If the harness work shows another parameter that is not defensible, it goes in a further addendum before the scored run.
