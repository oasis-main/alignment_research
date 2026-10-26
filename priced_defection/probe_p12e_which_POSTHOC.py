"""POST HOC, UNSCORED. Which choose* function does cell Q actually call? (patched choose9 was never called in the earlier probe)"""
import sys; sys.path.insert(0, '.')
import tournament6 as t6, tournament7 as t7, tournament8 as t8, tournament9 as t9, tournament12e as t
cnt = {}
def mk(mod, name):
    o = getattr(mod, name)
    def w(*a, **k):
        cnt[name] = cnt.get(name, 0) + 1
        return o(*a, **k)
    setattr(mod, name, w); return o
origs = [(t6,'choose',mk(t6,'choose')),(t7,'choose7',mk(t7,'choose7')),(t8,'choose8',mk(t8,'choose8')),(t9,'choose9',mk(t9,'choose9'))]
c = t.cell_Q(); print({k: c[k] for k in ('roles','calling','share_budget') if k in c})
t.run12e(c, 8100, {}, 0.0); print(cnt)
