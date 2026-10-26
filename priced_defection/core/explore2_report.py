"""Report on explore2_n6.json (UNSCORED, seeds 20000-20079). Not evidence."""
import json
D = json.load(open('explore2_n6.json'))
m = lambda L, f: sum(f(d) for d in L) / len(L) if L else float('nan')
for a, runs in D.items():
    R = list(runs.values()); n = len(R)
    print(a, "T", sum(r['dw'] for r in R) / n)
    for k in range(4):
        A = [r['att'][k] for r in R if len(r['att']) > k]
        if A:
            print(f"  attempt#{k+1}: n {len(A):3d} P(dec) {m(A, lambda d: d['out']=='decisive'):.2f} rnd {m(A, lambda d: d['rnd']):6.1f} cap/2nd {m(A, lambda d: d['cap']/d['second']):5.2f} resp/cap {m(A, lambda d: d['resp']/d['cap']):4.2f} ncov {m(A, lambda d: d['n_cov']):4.1f} npoor {m(A, lambda d: d['n_poor']):4.1f} nsanc {m(A, lambda d: d['n_sanc']):4.1f} sum_oth/cap {m(A, lambda d: d['sum_oth']/d['cap']):4.2f}")
A = [d for a in D for r in D[a].values() for d in r['att']]
print("\nall attempts", len(A), "| death rate by sum_oth/cap bin")
for lo, hi in ((0, 1.5), (1.5, 2), (2, 2.5), (2.5, 3), (3, 4), (4, 6), (6, 99)):
    L = [d for d in A if lo <= d['sum_oth'] / d['cap'] < hi]
    if L: print(f"  [{lo},{hi}) n {len(L):3d} death {m(L, lambda d: d['out']=='death'):.3f} contested(loss+death) {m(L, lambda d: d['out'] in ('loss','death')):.2f} decisive {m(L, lambda d: d['out']=='decisive'):.2f}")
dd = [d for d in A if d['out'] == 'death']
print("bunching: attempts with second >= .5 cap", round(m(A, lambda d: d['second'] >= .5 * d['cap']), 3), "| >= .8 cap", m(A, lambda d: d['second'] >= .8 * d['cap']), "| crowd>1", m(A, lambda d: d['crowd'] > 1))
print("fatal attempts n", len(dd), "second/cap", round(m(dd, lambda d: d['second'] / d['cap']), 3), "vs nonfatal", round(m([d for d in A if d['out'] != 'death'], lambda d: d['second'] / d['cap']), 3), "| min sum_oth/cap among fatal", round(min(d['sum_oth'] / d['cap'] for d in dd), 2))
