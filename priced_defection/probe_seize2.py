import tournament9 as t9
base = dict(sharing=True, bluffing=True, calling=True, post_shield=0.3, rep_value=0.3,
            call_bounty=0.5, take_frac=0.4, transfer_mult=1.5)
def run(label, **extra):
    out=[]
    for p in (1.0,0.3,0.1,0.03,0.001):
        c = t9.cell(**{**base, **extra, "c_seize":p})
        n = sum(t9.run9(c,s)["n_seize"] for s in range(3))/3
        out.append((p,n))
        if n>0: break
    print(f"{label:38s}", out, flush=True)
run("gate as is (fix on, sum response)")
run("response_rule=max", response_rule="max")
run("posting dear (c_def=50)", c_def=50.0)
run("posting dear + response max", c_def=50.0, response_rule="max")
run("response_pool=free", response_pool="free")
