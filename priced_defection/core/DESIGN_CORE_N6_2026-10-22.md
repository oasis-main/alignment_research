# Core pass N6 design note (2026-10-22): the welfare artifact, and diagnostics for the mid-dose theft deaths
Engine core.py after 76222c2. Selftest 39/39 (adds I31-I34). Written with the engine change, before any scored N6 run.

## The artifact (N5 result 5)
Copying is non-rival: a theft adds capability to the thief and removes none from the victim. Outside value is out_val x cap per round, so
stolen capability earned outside value from nothing. Frictionless theft showed W = 71,853 vs 2,682 with no theft (27x). That is arithmetic, not welfare.

## Choice: a ledger fix, not PD-only (switch `copy_earns`, default True = N5 behaviour)
copy_earns=False: capability the agent holds because it copied it earns no outside value in the welfare ledger. Each agent carries a stock `copied`
(adds the gain on every successful theft; scales with the agent's growth; is cut with the agent's capability by a catch or a takeover loss). The earning
capability is cap - copied, floored at 0. It is applied to the per-round outside income and to the outside stream a winner takes in the two
winner rules. Everything else in the ledger (PD income) is untouched.
Why this and not "report W_pd only when theft is on":
- W_pd alone drops the legitimate outside value of every uncopied agent, so theft arms would be compared with no-theft arms on different definitions.
  The ledger fix keeps one definition of W in all arms (W = W_pd + W_out, with W_out earned only by own capability) and W_pd is still reported
  alongside as the second bound.
- It is exact in the two limits that matter: no theft -> identical W (I33); full copy -> W_out = 0 for the copied part.
Why accounting only (no decision reads `copied`): the task is the welfare number. Letting the thief's valuation also drop the outside value of a copy
would change who steals, i.e. a different behavioural experiment; trajectories (takeover, deaths, theft counts) are therefore identical draw for draw
(I32) and all N5 takeover findings stand unchanged. LIMIT: the thief still prices a copy as if it earned outside value, so theft incentives
in these runs stay as generous as in N5. A decision-layer variant is the follow-up if it matters; not built here.
What is NOT fixed: copied capability still raises the thief's PD share (pw). That is a real transfer of competitive position, not created value
(PD payoffs are share-weighted and sum to a fixed total at pw=1 within a pairing apart from the pie), so it is left in.
Diffusion (open sharing) is not counted as copying: it is a different channel with a different sign in N3.

## Diagnostics (switch `diag`, default False; draws nothing, decides nothing; I34)
- st['diag_att']: one record per resolved takeover attempt: round, attempter id and cap, top cap and second cap of all living, crowd
  (agents >= 0.8 x top), rank of the attempter, number of covering responders, their summed response, the frontier, running theft counts, outcome
  (decisive / partial_win / loss / death).
- st['diag_ts']: per round top three capabilities and cumulative steals/catches/stolen.
