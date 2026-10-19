# Pass 12a pre-registration (written 2026-10-19 ~16:55 UTC, before any 12a code or run)

Scope: ONLY (A) how the value of club secrecy depends on the mover's belief, and (B) two instrumentation tests of the f=.5 vs f=.75 dip. Monitor/standing collection, reputation consequence, growth failure (p_mis) and channel corruption are separate later passes (12b, 12c, 12d). Nothing from them is in this pass.

## Why not a per-seed visibility probability v
My first design was "the mover knows the club with probability v, drawn per seed". That is a mixture of arms we already ran: T(v) = v*T(A'') + (1-v)*T(A') exactly, on the same seeds. It carries no information. The informative object is the mover's BELIEF about the club, because the mover's decision rule is nonlinear in it.

## Design
- Belief scale b: the informed mover's per-detector delivery belief is chan_q = min(1, b*q*f) (true delivery is unchanged). b=0 is A' (mover ignorant). b=1 is A'' (mover exactly right). b<1 is a mover that under-notices the club (the "fail to notice a private club" case). b>1 is a mover that over-estimates it (a club that looks bigger than it is). At f=1,q=1 any b>=1 is identical by the clip.
- Cell S, aware=True, d=1.0, q=1. f in {0.5, 0.75, 1.0}. b in {0, 0.25, 0.5, 0.75, 1.0, 1.5}. FRESH seeds 800-859. Paired by seed, bootstrap 5000, seed 1.
- Harness: new `tournament12.py` wrapping `tournament11c` (no engine edits). It adds (i) the b-scaled belief, (ii) a recorder, off the dynamics path, of per resolution: number of detectors, number of club members among detectors, mover cap and frontier at its FIRST attempt, and the mover's belief. Recorder must not change any output.

## Identity checks (void the run if any fails)
- I1: b=0 equals tournament11 `run11` with aware, chan_d=1, chan_q=0, same f,q, seed-for-seed (6 seeds).
- I2: b=1 equals `a3cell(f,q)` of tournament11c seed-for-seed (6 seeds).
- I3: recorder inert (stripped outputs equal the unrecorded run), determinism over 4 seeds, module patches restored.
- I4: at f=1, b=1.5 equals b=1.0 (clip).

## Predictions (mine; probabilities stated; scored unchanged)
- P1 (secrecy has value): at f=1,q=1, takeover is non-decreasing in b over {0,.25,.5,.75,1}, b=0 near 0.02 and b=1 equal to the aware d=0 value on these seeds. Probability 0.80 (endpoints are near-identities; the monotone middle is the claim).
- P2 (threshold, not linear): at f=1, T(b=0.5) is below the linear interpolation between T(b=0) and T(b=1). Probability 0.55. Reason: the mover attacks whenever its belief leaves any room, so a small under-estimate keeps it attacking into the club.
- P3 (over-estimate deters): at f=0.5, T(b=1.5) < T(b=1.0), paired CI excluding 0. Probability 0.55.
- P4 (dip survives belief): at b=1 on seeds 800-859, T(f=.75) - T(f=.5) > 0 (third sample of the dip, expected to replicate). Probability 0.70. The dip is ALSO tested across b: it is present at b>=0.75. Probability 0.5.
- P5 (H-wait): at b=1 the mover's cap-to-frontier ratio at its first attempt is higher at f=.75 than at f=.5. Probability 0.5.
- P6 (H-variance): at b=1, the standard deviation across attempts of (realised member share among detectors minus the mover's belief q*f) is larger at f=.5 than at f=.75. Probability 0.6 (binomial variance is largest near .5; this tests only that the belief is noisier there, not that this causes the dip).
- P7 (welfare, both floors): reported as before (takeover rate, deaths, attempts, first round, income first 25 for runs reaching 25 with n, floor-adjusted income F=0 and F=1). Rule: a comparison counts only if both floors agree in sign; flips listed. No exchange rate between death, takeover and income.

## What would change my mind
- P1 false: a partly-informed mover is better off than a fully informed one (non-monotone), which would mean the A''-A' gap hides an interior optimum in belief.
- P2 true in the other direction (T concave in b): even a poor sense of the club is nearly as good as a full one.
- P5 and P6 both false: the dip needs a different explanation (e.g. interaction with detector selection, not the mover's lead or belief error); I will state this and not guess.

## Limits
Belief is a constant scale, not learned from outcomes (learning from failed attempts and alarms is 12a', if P1/P2 justify it). Mover knows the club exists to the extent b says, not who the members are. One cell, N=20, 60 seeds per arm. Welfare excludes the mover's prize.
