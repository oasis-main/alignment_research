# Pass 12b pre-registration, ADDENDUM 3 (written 2026-10-19 ~18:55 UTC, before any 12b harness code or run)

Problem found re-reading how the engine pays for things. A monitor's cost `c_mon x R x cap` is taken from the agent's BUDGET `b`, not from its everyday-game score. Every welfare column in passes 10-12a is built from the PD score, so the original M7 ("F=1 income is higher at an interior m") cannot see the monitor's own cost at all. It would only see false-flag and exposure losses plus second-order effects through lost growth. That would bias M7 toward "more monitors is better".

Fix (decided before any run):
- The budget and the PD payoff are in the same units (the engine adds each PD payoff into `b`), so spend is commensurable with PD income. Record total monitor spend per run (budget units).
- New reported measure: NET income = (S + F x n_last x rest - spend) / (AR + n_last x rest), for F in {0, 1}, with S, AR, n_last, rest as in the A'' recorder. Spend is subtracted whole, not per monitor.
- M7 and M7b are scored on NET F=1 income. The un-netted F=1 income is reported alongside. M5 and M6 stay on un-netted F=1 income (they are about false-flag and exposure losses, which are in the PD score).
- Probabilities unchanged. Limit added: net income still ignores that spend reduces the monitor's capability growth (a second-order cost the run does show, through capability, and which I do not convert to income).
- The clamp (a broke monitor reads free) is counted: report the number of monitor-rounds where the clamp bound.
