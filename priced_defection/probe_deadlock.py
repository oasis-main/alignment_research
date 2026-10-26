import tournament3 as t

EV   = {"theta":1.0,"utility":"linear"}
RECK = {"theta":0.0,"utility":"linear"}   # threshold rule, grabs whenever p>0

print("Hypothesis: under 'idle', 2+ movers deadlock because the two-front")
print("exemption is evaluated at a moment when NOBODY is yet committed.")
print("If so, one reckless actor that commits anyway should unblock the rest.\n")

for name, ms in (
    ("idle 4xEV            ", [EV]*4),
    ("idle 3xEV + 1 reckless", [EV,EV,EV,RECK]),
    ("full 3xEV + 1 reckless", [EV,EV,EV,RECK]),
):
    mr = "idle" if name.startswith("idle") else "full"
    o = t.agg(t.cell(mover_resist=mr, movers=ms), 40)
    print(f"{name}  att={o['attempts']:.2f}  succ={o['successes']:.2f} "
          f"{o['successes_ci']}  ruin={o['ruin']:.3f}")

print("\nAnd: does ANY mover ever become busy under idle/2ev? (att=0 is ambiguous)")
prepped = 0
for s in range(40):
    r = t.run_once(t.cell(mover_resist="idle", movers=[EV]*4), s)
    if r["first"] is not None:
        prepped += 1
print(f"  runs where any mover reached execution: {prepped}/40")
