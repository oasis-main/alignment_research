# Core pass N3 pre-registration (2026-10-21): can open sharing, information gathering or capability theft offset the runaway?
Engine core.py at 0f5cec4 (selftest 26/26). Informed by UNSCORED calibrations calibrate_n3.py / calibrate_n3b.py (seeds 9950-9955,
outputs committed with this file). Scored seeds 10200-10259 are disjoint. Live pie (N1 rates) in every arm.

## Question (Mike, 13:14 UTC): "No amount of open sharing, information gathering, and capability theft can offset this?"
"This" = the outside-value runaway of N2 (out_val .5: takeover .82-1.00). Also: does an anticipating mover (prize at the projected
post-takeover pie) let the pie restrain?

## Levers
- open sharing: every capability published each round, followers diffuse toward the frontier (diffusion .01/.02/.05/.10). Publishes the mover too.
- theft: an action; copies theta .1 of the gap to the strongest OTHER agent's TRUE capability w.p. p_steal (.05/.10/.25/.50); price .1 x R x cap;
  the victim loses nothing; no detection, no retaliation. Works whether or not the leader publishes (the hidden-mover-robust channel).
- information gathering: per-round chance a that each agent spots a preparing mover (a .1/.3), and a .3 with response-to-execution (te).
- anticipation: g_conflict .5, post_growth -.05, with and without anticipate_pie.
Profiles C1.35 (pw 1, standing defence) and O1.35 (pw .5, none), out_val {0, .5}. 52 arms, paired by seed, bootstrap 5000.

## Predictions (takeover = decisive-win rate; all at out_val .5 unless stated)
- N3-1 (.75) open sharing diffusion .10: takeover <= .10 in both profiles.
- N3-2 (.65) takeover non-increasing in diffusion (0, .01, .02, .05, .10), both profiles (ties allowed; a rise of <= .05 tolerated).
- N3-3 (.70) theft p .50: takeover <= .10 in both profiles.
- N3-4 (.55) theft p .05 still lowers takeover by >= .30 vs none in C.
- N3-5 (.70) information a .3 does NOT lower takeover in C (diff vs none >= -.05).
- N3-6 (.70) information a .3 in O: takeover <= .10 AND deaths >= .8 x attempts (the overconfident-mover artifact, not a defence).
- N3-7 (.60) anticipation does not lower takeover in C (anticipate on minus off, same g_conflict .5 / post_growth -.05, >= -.05).
- N3-8 (.60) at out_val 0, any lever that stops takeover in O also leaves the leader's end lead <= 1.2 (catch-up, not deterrence).

## Voids
Invariant violation voids the arm. Gate-edge seeds reported, not dropped.
