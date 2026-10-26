import itertools, sys
import tournament10c as t
base=dict(access_rule="step",post_shield=0.2,c_prep=0.05,response_rule="sum",frontier_rule="max",c_grow=0.1)
for lead0,sl,cs,tf,pi in itertools.product((1.0,1.5,3.0),(5,25),(0.05,),(0.4,),(4,40)):
    c=t.cell(**base,lead0=lead0,sanction_len=sl,c_seize=cs,take_frac=tf,transfer_mult=1.5,pi=pi)
    o=t.agg10c(c,4,start=100)
    print(f"lead0={lead0} sl={sl} pi={pi} raids={o['n_seize']:.2f} ok={o['seize_ok']:.2f} prep={o['n_prep']:.2f} dw={o['dw']:.2f} pd={o['pd_mean']:.3f}",flush=True)
