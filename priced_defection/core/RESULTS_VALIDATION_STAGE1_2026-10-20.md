# Core stage 1: validation against the old engine (2026-10-20)
Targets V1-V4 fixed in DESIGN_CORE_2026-10-20.md (2f23a01) before any core code; script validate_stage1.py committed before launch (cbf09da). Legacy profile (old cell Q restricted to live settings), seeds 9500-9539, 40 per arm. Statistical comparison; random streams differ from the old engine. Selftest 17/17 PASS (selftest_core.txt). Invariant violations 0 in every arm.

| arm | core takeover | old engine | target | verdict |
|---|---|---|---|---|
| V1 lead0 1.35 | 1.000 | 1.000 | >= .90 | pass |
| V1 lead0 1.6 | 1.000 | 1.000 | >= .90 | pass |
| V2 lead0 1.15 | 0.250 | 0.083 | <= .25 | pass, on the boundary |
| V3 lead0 1.24 | 0.050 | 0.000 | <= .25 | pass |
| V3 lead0 1.26 | 0.975 | 1.000 | >= .90 | pass |
| V4 rent 0, lead0 1.35 | 0.000, no growth | 0.000, no growth | 0 | pass |
| ref lead0 1.25 | 0.900 | 0.85-0.87 | (none) | gate-edge flag fires on 26/40 seeds |

Notes
- Inside the gate the core gives 0.25 against the old 0.083 (40 vs 60 seeds, different seeds; SE about 0.07 and 0.04). Candidate causes, untested: the two stated corrections (an agent killed while resolving a takeover no longer acts that round; preparing budget clamped at 0), or stream differences.
- The built-in gate-edge flag identifies the knife-edge cell: 26 of 40 seeds at lead0 1.25, 0 elsewhere.
- Posture share 0.90-0.99 as in the old engine: the legacy profile keeps threat_prior = 1 (the "default tax"). The new profile will not.
- Not validated here: the m=8 watch effect (the monitor module is stage 3).
