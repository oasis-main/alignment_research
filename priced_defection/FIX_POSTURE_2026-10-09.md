# Fix: a paid defence never counted (passes 6 to 9)

Written 2026-10-09, **before** any re-run with the fix. The predictions below
are recorded here so the re-run can be scored against them.

## The bug

Order of one round in passes 6 to 9 (`tournament6.run6`, and the same loop in
v7, v8, v9):

1. income
2. detection
3. raids and takeovers that are complete get their result
4. each free player selects one action (for example `post`)
5. everyday game

A player that posts in round r gets `def_until = r`. The next result step is
step 3 of round r+1. That step used `posted(o, r+1)`, which is
`def_until >= r+1`. It is always false. So no paid post ever counted in a
takeover response, in a raid defence, or in the players' own estimates of the
response.

Evidence: 60 recorded runs (pass 8 gate cell and open cell, 30 seeds each).
4,037 takeover results. 34,103 cases where a player had noticed the takeover
and posted in the round before. Posts counted: 0.

## The fix

New function `covers(o, rnd, cfg)`: a post bought in round r counts at the
result step of round r+1, that is, until its buyer's next action. It is used
in every place where a post affects a result or an estimate:

- `resolve_grabs6` (takeover response)
- `seize_defence` (raid defence, and the target's own shield)
- `assess6` and `assess7` (the players' estimate of who will respond)

`posted()` is kept only for bookkeeping (the share of rounds spent posting).
`posture_fix=False` restores the old rule, so every pre-fix number is still
reproducible. New counters `resp_posters` and `n_resolved` record how many
posters counted in takeover results.

New selftest: a run where players post must count at least one poster in a
takeover result, and the same run with `posture_fix=False` must count none.

## Predictions (written before the re-run)

Default response rule in all headline blocks is `sum`.

| # | prediction | why |
|---|---|---|
| F1 | Provision results stay: zero posts at `post_shield=0`, and the same bimodal threshold above it. | The value of a post is only its private shield. The fix does not change that value. |
| F2 | The pass 8 hard-gate takeover rate (0.90) falls a lot, probably below 0.3. | 19 posters with capability about 2 each sum to about 38. The leader has about 7.4. With `sum`, a detected takeover now fails. |
| F3 | The lead still grows under the gate (about 3.9 at the end). | The gate still stops the others from buying capability. That does not depend on defence. |
| F4 | The pass 6 and 7 dear-capability lock-in (takeover rate 1.00) also falls a lot. | Same reason as F2. |
| F5 | The pass 9 attention result becomes larger. With no sharing, the takeover rate falls well below 0.90. With sharing, it stays near 1.00. | Sharing still takes the agents' turns away from posting, and now posting matters. |
| F6 | Under `max` response (only the strongest responder counts), results change little. | One poster with capability about 2 does not stop a leader with about 7.4. |
| F7 | Fewer takeover attempts in total. | Players now see the posters in their estimate, so the estimated chance to win is lower. |

If F2 and F4 are correct, the "capability lock-in" headline changes from
"gate gives a takeover" to "gate gives a large lead, and only a paid
collective defence stops the takeover". That is a different and more
conditional result.

## Re-run

Blocks: v6 A and C, v7 G and I, v8 K and M, v9 N and O, 30 seeds per cell
(the same as the original runs). Output goes to `raw_fix/`. The pre-fix files
in `raw/` are not changed.
