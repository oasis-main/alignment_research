# Core pass N5 pre-registration (2026-10-21): theft with capture, punishment and concealment
Engine core.py at 164f2e0 (selftest 35/35). Informed by UNSCORED calibrate_n5.py (seeds 9990-9995, calibration_n5.txt, committed with
this file). Scored seeds 10400-10459, disjoint. 30 arms in sweep_n5.py.

## Question
N3 found theft (p .5, theta .1) stops the outside-value runaway, under maximally generous assumptions: free, never caught, aimed at
true capability. Does it survive capture (p_catch .1/.3/.5; caught -> no gain, lose 20% capability, shut out 50 rounds) and
concealment (an unpublished agent shows (1 - conceal) of its capability: 0/.3/.6), plus estimate noise (sigma .5)?
Base: out_val .5, live pie, lead0 1.35; profiles C (pw 1, standing defence) and O (pw .5, none). The thief prices the expected catch cost.

## Predictions (takeover = decisive-win rate)
- N5-1 (.90) frictionless (pc 0, cc 0) reproduces N3: takeover <= .05 in both profiles.
- N5-2 (.70) O: every arm with p_catch >= .3 has takeover >= .90 (theft is abandoned, not merely weakened).
- N5-3 (.65) O: concealment .3 with p_catch 0 gives takeover >= .80.
- N5-4 (.60) C: at p_catch .3 and .5, takeover is non-decreasing in concealment (0, .3, .6), tolerance .10.
- N5-5 (.55) C: p_catch .5 with concealment .6 is within .10 of no theft.
- N5-6 (.60) estimate noise alone (sigma .5, pc 0, cc 0) keeps takeover <= .10 in both profiles.
- N5-7 (.50) C: p_catch .1 with concealment 0 keeps takeover <= .35.
Exploratory: steal attempts and captures by arm; welfare (trunc and trend rules), Gini; deaths.

## Voids
Invariant violation voids the arm. Gate-edge seeds reported, not dropped.
