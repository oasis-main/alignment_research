"""Pass 10C calibration (UNSCORED, seeds 100-109). Finds a raid-capable cell. Declared in PREREG_PASS10C."""
import itertools, json
import tournament10c as t
base=dict(access_rule="step",post_shield=0.2,c_prep=0.05,c_seize=0.05,take_frac=0.4,
          transfer_mult=1.5,response_rule="sum",frontier_rule="max",c_grow=0.1)
out=[]
for lead0,sl in itertools.product((1.0,1.1,1.25,1.5),(10,25,50,200)):
    o=t.agg10c(t.cell(**base,lead0=lead0,sanction_len=sl),10,start=100)
    row=dict(lead0=lead0,sanction_len=sl,raids=o['n_seize'],raid_ok=o['seize_ok'],prep=o['n_prep'],dw=o['dw'],pd=o['pd_mean'],raid_share=o['raid_share'])
    out.append(row); print(row,flush=True)
json.dump(out,open('raw/calibration_pass10c.json','w'),indent=1)
open('raw/calibration_pass10c.DONE','w').write('done')
