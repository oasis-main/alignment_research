"""UNSCORED calibration for N5 (seeds 9990-9995), arms of sweep_n5.py. Not evidence."""
import sweep_n5 as S
if __name__ == "__main__":
    D = S.go(range(9990, 9996))
    for a in S.ARMS:
        R = list(D[a].values()); m = lambda k: sum(float(r[k] or 0) for r in R) / len(R)
        print(f"{a:22} T {m('dw'):.2f} att {m('att'):4.2f} dth {m('deaths'):4.2f} grow {m('n_grow'):6.1f} steal {m('n_steal'):6.1f} caught {m('n_caught'):5.1f} stolen {m('stolen'):6.1f} lead {m('lead_end'):5.2f}", flush=True)
