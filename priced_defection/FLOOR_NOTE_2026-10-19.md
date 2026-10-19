# What the post-takeover floor is, and why we report a break-even instead of choosing one (2026-10-19 ~19:15 UTC)

Engine facts (read from tournament6/9/10 code, cell S: K_win = K_loss = 2.0, frontier_rule = max):
- A grab is DECISIVE (game ends, `dw`) only if the mover's capability beats the response AND is at least K_win x the frontier (backups destroyed). Otherwise it is an indecisive win (`iw`: partial gain, sanction, game continues) or a loss (`il`/`dl`). Backups and the collective response therefore decide WHETHER a takeover is final.
- When a decisive takeover happens the engine just stops. The remaining rounds are not simulated. The floor F is the per-agent-round income we assign to those unsimulated rounds. It is not in the engine at all; it is a welfare-accounting assumption about the world AFTER backups have been destroyed.
- Neither backups nor the response say what finality looks like. They only make it rarer.

Named post-takeover worlds, as a map for reading F (PD payoffs T5 R3 P1 S0; surviving runs earn about 2.5 per agent-round):
- F = 0: extraction or ruin. Everyone else earns nothing.
- F = 1 (= P): everyone left plays the defect-defect game.
- F near 2.5: cooperation survives under the new dominant actor.
The floor applies to all living agents including the mover. That is a simplification.

Method: net income at floor F is linear in F, so for any arm vs baseline diff(F) = A + B*F. F* = -A/B is the floor at which they tie. Paired bootstrap over seeds. Script: breakeven_floor.py, output raw/breakeven_floor.txt. No new simulation.
