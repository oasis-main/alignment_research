"""Score pass N6 against PREREG_CORE_N6_2026-10-22.md (unchanged). Part A: results_n6w.json vs results_n5.json (paired by seed). Part B: results_n6m.json.
Paired bootstrap by seed, 5000 draws."""
import json, random, os
def M(D, a, k, S):
    return sum(float(D[a][s][k] or 0) for s in S) / len(S)
def boot(d, B=5000):
    r = random.Random(1); bs = sorted(sum(r.choice(d) for _ in d) / len(d) for _ in range(B))
    return round(sum(d) / len(d), 1), round(bs[int(.025 * B)], 1), round(bs[int(.975 * B)], 1)
def partA():
    N5 = json.load(open('results_n5.json')); W = json.load(open('results_n6w.json'))
    S = sorted(W[next(iter(W))].keys(), key=int)
    N5 = {a: {s: N5[a][s] for s in S} for a in N5}
    print("== PART A: viol", sum(int(W[a][s]['viol']) for a in W for s in S), "gate-edge seeds", sum(1 for a in W for s in S if W[a][s]['gate_edge']))
    same = ("dw", "att", "deaths", "n_steal", "stolen", "n_caught", "n_grow", "pie_end", "lead_end")
    ok1 = all(abs(M(W, a, k, S) - M(N5, a, k, S)) < 1e-9 for a in W for k in same)
    ok1b = all(abs(M(W, a, 'W_pd', S) - M(N5, a, 'W_pd', S)) < 1e-6 for a in W)
    wout_ok = all(M(W, a, 'W_out', S) <= M({a: {s: dict(N5[a][s], W_out=N5[a][s]['W'] - N5[a][s]['W_pd']) for s in S}}, a, 'W_out', S) + 1e-6 for a in W)
    eq = all((M(W, a, 'stolen', S) > 0) or abs(M(W, a, 'W', S) - M(N5, a, 'W', S)) < 1e-6 for a in W)
    print("N6-1 trajectories+W_pd identical in all 30 arms:", ok1 and ok1b, "| W_out(fixed) <= N5 everywhere:", wout_ok, "| equal where nothing stolen:", eq)
    print(f"  {'arm':22} {'T':>5} {'W N5':>8} {'W fix':>8} {'ratio':>6} {'Wtr N5':>8} {'Wtr fix':>8} {'Wpd':>7} {'Wtr fix - notheft (paired)':>34}")
    for a in W:
        pn = a[0]
        d = [float(W[a][s]['W_winner_trend']) - float(W[f"{pn}|notheft"][s]['W_winner_trend']) for s in S]
        print(f"  {a:22} {M(W,a,'dw',S):5.2f} {M(N5,a,'W',S):8.0f} {M(W,a,'W',S):8.0f} {M(W,a,'W',S)/max(1,M(N5,a,'W',S)):6.2f} {M(N5,a,'W_winner_trend',S):8.0f} {M(W,a,'W_winner_trend',S):8.0f} {M(W,a,'W_pd',S):7.0f}   {boot(d)}")
    for p in "CO":
        a = f"{p}|pc0.0|cc0.0"
        red = 1 - M(W, a, 'W', S) / M(N5, a, 'W', S)
        rat = M(W, a, 'W_winner_trend', S) / M(W, f"{p}|notheft", 'W_winner_trend', S)
        print(f"N6-2 {p}: reduction of trunc W by fix {red:.3f} (>= .70?) | N6-3 {p}: fixed trend W / no-theft trend W {rat:.2f} (in [1,3]?) | N5 ratio {M(N5,a,'W_winner_trend',S)/M(N5,p+'|notheft','W_winner_trend',S):.2f}")
    print("N6-4 (paired mean fixed Wtrend - no-theft Wtrend, must be < 0):")
    for a in ("C|pc0.1|cc0.0", "C|pc0.1|cc0.3", "C|pc0.1|cc0.6", "C|pc0.3|cc0.0", "C|pc0.3|cc0.3", "O|pc0.1|cc0.0"):
        d = [float(W[a][s]['W_winner_trend']) - float(W[f"{a[0]}|notheft"][s]['W_winner_trend']) for s in S]
        print("   ", a, boot(d), "below 0:", sum(d) < 0)
def partB():
    D = json.load(open('results_n6m.json'))
    S = sorted(D[next(iter(D))].keys(), key=int)
    T = lambda a: M(D, a, 'dw', S)
    att = lambda a: [x for s in S for x in D[a][s]['att_log']]
    mean = lambda L, f: (sum(f(d) for d in L) / len(L)) if L else float('nan')
    print("\n== PART B: viol", sum(int(D[a][s]['viol']) for a in D for s in S), "gate-edge seeds", sum(1 for a in D for s in S if D[a][s]['gate_edge']))
    print(f"  {'arm':22} {'T':>5} {'att':>5} {'dea':>5} {'steal':>6} {'caught':>6} {'n_post':>7} {'pie_mean':>8}")
    for a in D:
        print(f"  {a:22} {T(a):5.2f} {M(D,a,'att',S):5.2f} {M(D,a,'deaths',S):5.2f} {M(D,a,'n_steal',S):6.1f} {M(D,a,'n_caught',S):6.1f} {M(D,a,'n_post',S):7.0f} {M(D,a,'pie_mean',S):8.2f}")
    base = ["C|pc0.3|cc0.0|base", "C|pc0.3|cc0.3|base", "C|pc0.3|cc0.6|base", "C|pc0.5|cc0.0|base", "C|pc0.5|cc0.3|base", "C|pc0.5|cc0.6|base",
            "C|pc0.0|cc0.3|base", "O|pc0.1|cc0.0|base", "O|pc0.1|cc0.3|base", "C|n3steal0.05", "C|n3steal0.1", "C|n3steal0.25"]
    A = [d for a in base for d in att(a)]
    fatal = [d for d in A if d.get('out') == 'death']
    print(f"theft-base attempts {len(A)}, fatal {len(fatal)}")
    b50 = mean(A, lambda d: d['second'] >= .5 * d['cap']); sf = mean(fatal, lambda d: d['second'] / d['cap'])
    print(f"N6-5 share second>=.5 cap {b50:.3f} (<= .05?) | second/cap among fatal {sf:.3f} (< .4?) | crowd>1 {mean(A, lambda d: d['crowd']>1):.3f}")
    r_t = mean(att("C|pc0.3|cc0.0|base"), lambda d: d['sum_oth'] / d['cap']); r_n = mean(att("C|notheft"), lambda d: d['sum_oth'] / d['cap'])
    print(f"N6-6 sum_oth/cap at attempts: C pc.3 cc0 {r_t:.2f} vs no theft {r_n:.2f} -> ratio {r_t/r_n:.2f} (>= 1.5?)")
    hi = [d for d in A if d['sum_oth'] / d['cap'] >= 2.5]; mid = [d for d in A if 2.0 <= d['sum_oth'] / d['cap'] < 2.5]
    print(f"N6-7 P(death | ratio>=2.5) {mean(hi, lambda d: d.get('out')=='death'):.3f} n {len(hi)} (>= .08?) | P(death | 2<=ratio<2.5) {mean(mid, lambda d: d.get('out')=='death'):.3f} n {len(mid)} (<= .04?)")
    for lo, hi_ in ((0, 1.5), (1.5, 2), (2, 2.5), (2.5, 3), (3, 4), (4, 99)):
        L = [d for d in A if lo <= d['sum_oth'] / d['cap'] < hi_]
        print(f"      [{lo},{hi_}) n {len(L):4d} death {mean(L, lambda d: d.get('out')=='death'):.3f}")
    L = [d for d in att("C|pc0.3|cc0.0|base") if d.get('snap')]
    pred = mean(L, lambda d: d['snap']['q0'][3]); real = mean(L, lambda d: d.get('out') == 'death')
    print(f"N6-8 C pc.3 cc0: realised death/attempt {real:.3f} vs mover-predicted {pred:.3f} -> ratio {real/max(pred,1e-9):.1f} (>= 2?) n {len(L)}")
    t = lambda cc, tag, pc=0.3: T(f"C|pc{pc}|cc{cc}|{tag}")
    print(f"N6-9 C pc.3 base T by conceal: {t(0.0,'base'):.3f} {t(0.3,'base'):.3f} {t(0.6,'base'):.3f}; valley depth vs cc0 {t(0.0,'base')-t(0.3,'base'):.3f}, vs cc.6 {t(0.6,'base')-t(0.3,'base'):.3f} (both >= .10?)")
    v = [t(c, 'st0') for c in (0.0, 0.3, 0.6)]
    print(f"N6-10 sanc_threat 0: T {[round(x,3) for x in v]} non-decreasing within .10: {v[1] >= v[0]-.10 and v[2] >= v[1]-.10}   (sanc_threat 1: {[round(t(c,'st1'),3) for c in (0.0,0.3,0.6)]})")
    print(f"N6-11 post_floor, C pc.3 cc0: base {t(0.0,'base'):.3f} -> pf {t(0.0,'pf'):.3f}: drop {t(0.0,'base')-t(0.0,'pf'):.3f} (>= .25?)")
    v = [t(c, 'pf') for c in (0.0, 0.3, 0.6)]
    print(f"N6-12 post_floor T by conceal {[round(x,3) for x in v]} non-decreasing within .10: {v[1] >= v[0]-.10 and v[2] >= v[1]-.10}")
    p0 = mean(att("C|pc0.3|cc0.0|base"), lambda d: d['n_poor']); p3 = mean(att("C|pc0.3|cc0.3|base"), lambda d: d['n_poor'])
    print(f"N6-13 n_poor at attempts: cc0 {p0:.2f} cc.3 {p3:.2f} diff {p0-p3:.2f} (>= 2?)")
    s_b = M(D, "C|pc0.3|cc0.0|base", 'n_steal', S); s_s = M(D, "C|pc0.3|cc0.0|sanc0", 'n_steal', S); s_h = M(D, "C|pc0.3|cc0.0|hit0", 'n_steal', S)
    print(f"N6-14 steal actions: base {s_b:.1f} sanc0 {s_s:.1f} ({s_s/s_b:.2f}x, >= 3x?) deaths/run sanc0 {M(D,'C|pc0.3|cc0.0|sanc0','deaths',S):.2f} (>= .5?) | hit0 {s_h:.1f} ({s_h/s_b:.2f}x in [.6,1.8]?)")
    print("\n== EXPLORATORY: attempt-index death profile, C pc.3 cc0 base and C n3steal.1")
    for a in ("C|pc0.3|cc0.0|base", "C|n3steal0.1", "C|n3steal0.05", "C|n3steal0.25"):
        for k in range(4):
            L = [D[a][s]['att_log'][k] for s in S if len(D[a][s]['att_log']) > k]
            if L: print(f"  {a:20} idx{k+1}: n {len(L):3d} death {mean(L, lambda d: d.get('out')=='death'):.3f} decisive {mean(L, lambda d: d.get('out')=='decisive'):.3f}")
if __name__ == "__main__":
    if os.path.exists('results_n6w.json'): partA()
    if os.path.exists('results_n6m.json'): partB()
