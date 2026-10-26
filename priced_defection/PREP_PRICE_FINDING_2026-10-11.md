# Are the 2x2's zero-takeover cells defence, or the leader priced out of preparing? (2026-10-11)

Prompted by the open flag: under free response the lead is 4.6-50 yet there are 0 attempts.

## Finding 1: the lead statistic and the attempt rule are consistent. The leader is priced out.

`probe_lead_free.py`, seed 0, free/sum/cheap/hard gate, no sharing. The leader's `prep` option:

- Price of prep = c_prep x R x (OWN capability) x pi = 0.5 x 3 x 92.5 x 4 = 555 budget units.
- Prize = lambda x (SUM of the others' capability) = 7.5 x 19.5 = 147, discounted by pv(pi+kappa) = 0.43, so 63.
- Break-even leader capability, others held fixed: about 10.5. The leader's actual capability is 92.5.
- P(win) is 1.00 in the leader's own assessment (pW=1.00), so defence is not what stops it.
  Its valuation of prep is -500.

Mechanism: every price in the game is quoted in units of the buyer's own capability (`base = R * cap`).
The prize does not grow with the buyer's capability, but the price of preparing does. So a leader that
grows past roughly 10x its break-even stops being able to afford a takeover, and the bigger it
gets the more firmly it is priced out. This is the same price-unit design that keeps `grow` and
`post` scaled to the buyer. It was never intended to make aggression dearer for the strong.

## Finding 2: the 2x2's zero cells under FREE response do not show that free defence deters.

`probe_prep_price.py`, 10 seeds, hard gate, no sharing, cheap capability. Sweep c_prep:

| response | frontier | c_prep=0.5 (default) | 0.05 | 0.005 |
|---|---|---|---|---|
| paid | max | takeover 0.00 (att 0.90, deaths 0.90) | **1.00** (att 1.9) | **1.00** (att 2.7) |
| free | max | 0.00 (att 0.00) | **1.00** (att 2.1) | **1.00** (att 2.6) |
| paid | sum | 0.00 (att 0.90) | 0.00 (att 12.2) | 0.00 (att 11.7) |
| free | sum | 0.00 (att 0.00) | 0.00 (att 11.9) | 0.00 (att 11.6) |

- Under the max frontier, free response does NOT stop a takeover once preparing is affordable: 1.00 at
  c_prep=0.05, the same as paid. Pre-registered H1 (free response: takeover < 0.1 under both frontier
  rules) is therefore FALSE under the max rule when prep is cheap. The 2x2's H1 "holds" verdict
  came from the prep price.
- Under the sum frontier the picture is different: 12 attempts per run, none succeed, no deaths.
  The win bar is K_win x the pooled total, which the leader cannot reach (final lead 0.6). The sum
  rule's zero is about the win bar, not about defence. This agrees with Mike's earlier point that
  sum is pooling by construction.
- Paid, max, default c_prep: attempts happen (0.90) and every one ends in death (deaths 0.90). The
  leader tries only when it is small enough to afford prep, and loses.

## What this does to the 2x2 table

- Cells that stand: paid/max/cheap with sharing (1.00 and 0.93) was run at default c_prep. That
  anomaly depends on the leader being able to afford prep at all. It stands as a statement
  about that parameter set.
- Cells that do not stand as evidence about defence: every free-response zero, and every
  no-sharing zero in the max/cheap row (it was priced out, not deterred).
- The sum/paid zeros are explained by the win bar and by the defence ratio (SEIZE_DIAGNOSIS).

## Consequence for design

`c_prep` is a hidden control variable. At the default it removes takeover from any leader that has
grown, whatever the defence. The game needs one of: (a) price prep in units of the PRIZE or of the
mean capability rather than the buyer's own capability, (b) report every takeover result at two
c_prep values, (c) run the 2x2 at c_prep=0.05 as the main grid. I recommend (c) now and (a) as a
design question for Mike, because (a) changes what the game means.

Files: probe_lead_free.py, probe_prep_price.py.
