"""UNSCORED calibration for N4 (seeds 9970-9975), using the arms of sweep_n4.py. Not evidence."""
import sweep_n4 as S
if __name__ == "__main__":
    D = S.go(range(9970, 9976))
    for a in S.ARMS:
        R = list(D[a].values()); m = lambda k: sum(float(r[k] or 0) for r in R) / len(R)
        print(f"{a:16} T {m('dw'):.2f} att {m('att'):4.2f} dth {m('deaths'):4.2f} grow {m('n_grow'):6.1f} pie {m('pie_end'):5.2f} lead {m('lead_end'):5.2f} "
              f"Wpd/rd {m('W_pd')/ (m('last_round')+1):6.1f} Wout/rd {m('W_out')/(m('last_round')+1):6.1f} Wwin {m('W_winner_rule'):8.0f} gini {m('W_gini'):.2f} giniW {m('W_gini_winner_rule'):.2f} alive {m('n_alive_end'):4.1f}", flush=True)
