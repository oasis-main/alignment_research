import tournament9 as t9
for rr in ("sum","max"):
  for cg in (0.1, 0.6):
    cs = t9.cell(sharing=True, share_scope="public", rep_value=0.3, post_shield=0.2,
                 access_rule="step", lead0=3.0, c_grow=cg, response_rule=rr)
    a=t9.agg9(dict(cs, share_budget="shared"),8); b=t9.agg9(dict(cs, share_budget="separate"),8)
    print(f"rule={rr} c_grow={cg}: post_share {a['post_share']:.3f} -> {b['post_share']:.3f}  n_post {a['n_post']:.0f} -> {b['n_post']:.0f}  dw {a['dw']:.2f} -> {b['dw']:.2f}", flush=True)
