# -*- coding: utf-8 -*-
"""首次全样本运行：malf 引擎 + 分位。读 data/raw/bars.csv，写 data/processed/first_run/。

用法：python -m malf
核对：小波段事件与 lab/p20_real_c.py 的 events.json 一致；大波段与 nested.json 写法 C 一致。
分位口径：全历史池 in-sample（首跑看分布形态；扩展窗无未来函数版留给正式引擎，见 malf/percentile.py docstring）。
"""
import csv, collections, json, os, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from malf.core import small_run, small_waves, big_run
from malf.percentile import pct

OUT = os.path.join(ROOT, 'data', 'processed', 'first_run')
os.makedirs(OUT, exist_ok=True)

rows = collections.defaultdict(list)
for x in csv.DictReader(open(os.path.join(ROOT, 'data', 'raw', 'bars.csv'), encoding='utf-8')):
    rows[x['symbol']].append((x['date'], float(x['open']), float(x['high']), float(x['low']), float(x['close'])))
for k in rows:
    rows[k].sort(key=lambda t: t[0])

res, bigs_all, snaps_small, snaps_big = {}, {}, {}, {}
for s in sorted(rows):
    bars = rows[s]
    H = [b[2] for b in bars]
    L = [b[3] for b in bars]
    ev, snaps = small_run(bars)
    res[s] = ev
    snaps_small[s] = snaps
    SW = small_waves(ev)
    bigs, alive = big_run(H, L, SW)
    for w in bigs:
        w['sym'] = s
    bigs_all[s] = bigs
    # 大波段逐 bar 快照
    snaps = [None] * len(bars)
    for w in bigs:
        nb = set(w['newbars'])
        cnt = w['cnt0']
        span = 0
        for i in range(w['b'], w['d'] + 1):
            if i in nb:
                if i != w['b']:
                    cnt += 1
                span = 0
            else:
                span += 1
            snaps[i] = dict(dir=w['dir'], n=cnt, no_new_span=span, wave_age=i - w['b'])
    snaps_big[s] = snaps

# ---- 核对 1：小波段事件 == p20_real_c events.json ----
ref = json.load(open(os.path.join(ROOT, 'data', 'processed', 'p20_real_c', 'events.json'), encoding='utf-8'))
mis = [s for s in res if res[s] != ref.get(s)]
print('核对1 小波段事件 vs p20_real_c：%d 只标的不一致 %s' % (len(mis), mis[:5]))

# ---- 核对 2：大波段 == nested.json 写法 C ----
refb = json.load(open(os.path.join(ROOT, 'data', 'processed', 'nested', 'nested.json'), encoding='utf-8'))['C']['big']
mis2 = sum(
    ([(w['dir'], w['b'], w['d'], w['cnt'], w['nsw'], w['by_kill'], [[m['i'], m['g']] for m in w['moves']]) for w in bigs_all[s]]
     != [(w['dir'], w['b'], w['d'], w['cnt'], w['nsw'], w['by_kill'], w.get('trace', [])) for w in refb.get(s, [])])
    for s in bigs_all)
print('核对2 大波段 vs nested.py C：%d 只标的不一致' % mis2)


def level(name, waves_by_sym, snaps_by_sym, count_key):
    dead = [w for s in waves_by_sym for w in waves_by_sym[s] if w['d'] is not None]
    alive_n = sum(1 for s in waves_by_sym for w in waves_by_sym[s] if w['d'] is None)
    fn = {'UP': sorted(w[count_key] for w in dead if w['dir'] == 'UP'),
          'DN': sorted(w[count_key] for w in dead if w['dir'] == 'DN')}
    fs = {'UP': sorted(w['max_span'] for w in dead if w['dir'] == 'UP'),
          'DN': sorted(w['max_span'] for w in dead if w['dir'] == 'DN')}
    print('== %s：已死 %d 条（活到数据末 %d 条）' % (name, len(dead), alive_n))
    for d in ('UP', 'DN'):
        v = fn[d]
        print('  %s 最终只数 中位 %s P90 %s 最大 %s；池 %d 条' % (d, v[len(v)//2], v[int(.9*len(v))], v[-1], len(v)))
    for d in ('UP', 'DN'):
        v = fs[d]
        print('  %s 最大未推进 中位 %s P90 %s 最大 %s' % (d, v[len(v)//2], v[int(.9*len(v))], v[-1]))
    sample = []
    for s in sorted(rows):
        for i, sn in enumerate(snaps_by_sym[s]):
            if sn is None or i % 60 != 0:
                continue
            sample.append(dict(sym=s, date=rows[s][i][0], dir=sn['dir'], n=sn['n'],
                               no_new_span=sn['no_new_span'],
                               pct_n=pct(fn[sn['dir']], sn['n']),
                               pct_span=pct(fs[sn['dir']], sn['no_new_span'])))
    return dead, sample


SW_all = {s: small_waves(res[s]) for s in res}
for s in SW_all:                       # 每条小波段补 max_span
    for w in SW_all[s]:
        end = w['d'] if w['d'] is not None else len(rows[s]) - 1
        w['max_span'] = max((snaps_small[s][i]['no_new_span'] for i in range(w['b'], end + 1) if snaps_small[s][i]), default=0)

for s in bigs_all:                     # 每条大波段补 max_span
    for w in bigs_all[s]:
        w['max_span'] = max((snaps_big[s][i]['no_new_span'] for i in range(w['b'], w['d'] + 1) if snaps_big[s][i]), default=0)

dead_s, sample_s = level('小波段', SW_all, snaps_small, 'n')
dead_b, sample_b = level('大波段', bigs_all, snaps_big, 'cnt')

json.dump(dict(
    small=[dict(sym=s, dir=w['dir'], b=w['b'], d=w['d'], n=w['n'], max_span=w['max_span']) for s in SW_all for w in SW_all[s]],
    big=[dict(sym=w['sym'], dir=w['dir'], b=w['b'], d=w['d'], cnt=w['cnt'], max_span=w['max_span']) for w in dead_b],
    sample_small=sample_s, sample_big=sample_b),
    open(os.path.join(OUT, 'percentile_first.json'), 'w'), ensure_ascii=False)
print('-> data/processed/first_run/percentile_first.json')
