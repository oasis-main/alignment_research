"""Unscored/scored diagnostic helper for N6: run one arm with diag on, return attempt records. Imports core.py."""
import sys
sys.path.insert(0, '.')
import core
import sweep_n5 as S5
def run_diag(arm, seed, **over):
    r = core.run(core.cell(diag=True, **dict(S5.ARMS[arm], **over)), seed)
    return r
if __name__ == "__main__":
    r = run_diag("C|pc0.3|cc0.0", 9990)
    print({k: r[k] for k in ("dw", "att", "deaths", "n_steal", "n_caught", "stolen", "lead_end")})
    for d in r["diag_att"]: print(d)
    print(len(r["diag_ts"]), r["diag_ts"][::40])
