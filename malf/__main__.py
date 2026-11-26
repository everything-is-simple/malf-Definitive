# -*- coding: utf-8 -*-
"""全样本运行：malf 引擎 + 分位。读 data/raw/bars.csv（或 argv[1]），写 data/processed/first_run/（或 argv[2]）。

用法：python -m malf [bars_csv] [out_dir]
合同（2026-11-26 签署，P22–P25 对齐）：
- 价格比较域：_px() = 后复权价 ×100 四舍五入 half-up 取整（hfq_x100_halfup_v1）。
- 出生：全历史起点统一盘整出生（D18/O6 已冻结，P22）；同一根 bar 机械按 O2 顺序，
  新守护点当根判死时已生效（P23）。
- 分位：严格小于、终止不晚于当前 bar（含当日）、池不足 30 条返回 None、
  停滞样本 = final_span 临终冻结值（P24/P25，malf/percentile.py）；
  同时保留全历史池（in-sample）分位作分布形态对照。
核对：小波段事件与 lab/p20_real_c.py 的 events.json 比结构；大波段与 nested.json 写法 C 比结构
      （只对参考文件里有的标的核对）。注意：参考文件出自未量化的 float 比较，_px 取整后
      临界相等的边界情形可能产生少量结构分歧，属预期。
数据：bars_all.csv = 全 A 股（5581 只，2020-2024），后复权未舍入（hithink 导出，见 README 数据来历）。
      【取舍｜已签】不含已退市股；与旧 bars.csv 同复权链。
"""
import csv, collections, json, os, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from malf.core import small_run, small_waves, big_run, _px
from malf.percentile import pct, ExpandingPool

BARS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'raw', 'bars.csv')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'data', 'processed', 'first_run')
os.makedirs(OUT, exist_ok=True)

rows = collections.defaultdict(list)
for x in csv.DictReader(open(BARS, encoding='utf-8')):
    rows[x['symbol']].append((x['date'], float(x['open']), float(x['high']), float(x['low']), float(x['close'])))
for k in rows:
    rows[k].sort(key=lambda t: t[0])

res, bigs_all, snaps_small, snaps_big = {}, {}, {}, {}
alive_big = {}
for s in sorted(rows):
    bars = rows[s]
    H = [_px(b[2]) for b in bars]
    L = [_px(b[3]) for b in bars]
    ev, snaps = small_run(bars)
    res[s] = ev
    snaps_small[s] = snaps
    SW = small_waves(ev)
    bigs, alive = big_run(H, L, SW)
    for w in bigs:
        w['sym'] = s
    bigs_all[s] = bigs
    if alive is not None:
        alive['sym'] = s
        alive_big[s] = alive
    # 大波段逐 bar 快照（活到数据末的波段补到最后一根）
    snaps = [None] * len(bars)
    for w in bigs + ([alive] if alive is not None else []):
        nb = set(w['newbars'])
        cnt = w['cnt0']
        span = 0
        end = w['d'] if w.get('d') is not None else len(bars) - 1
        for i in range(w['b'], end + 1):
            if i in nb:
                if i != w['b']:
                    cnt += 1
                span = 0
            else:
                span += 1
            snaps[i] = dict(dir=w['dir'], n=cnt, no_new_span=span, wave_age=i - w['b'])
    snaps_big[s] = snaps

def sig(ev):
    """事件结构签名：kind/i/dir/n（guard/level 等价格值受复权精度影响，不作核对依据）。"""
    return [(e['kind'], e['i'], e['dir'], e.get('n')) for e in ev]


# ---- 核对 1：小波段事件 == p20_real_c events.json（只对参考文件里有的标的） ----
ref = json.load(open(os.path.join(ROOT, 'data', 'processed', 'p20_real_c', 'events.json'), encoding='utf-8'))
chk = [s for s in res if s in ref]
mis = [s for s in chk if sig(res[s]) != sig(ref[s])]
print('核对1 小波段事件(结构) vs p20_real_c：核对 %d 只，不一致 %d 只 %s' % (len(chk), len(mis), mis[:5]))

# ---- 核对 2：大波段 == nested.json 写法 C ----
refb = json.load(open(os.path.join(ROOT, 'data', 'processed', 'nested', 'nested.json'), encoding='utf-8'))['C']['big']
chk2 = [s for s in bigs_all if s in refb]
mis2 = sum(
    ([(w['dir'], w['b'], w['d'], w['cnt'], w['nsw'], w['by_kill'], [m['i'] for m in w['moves']]) for w in bigs_all[s]]
     != [(w['dir'], w['b'], w['d'], w['cnt'], w['nsw'], w['by_kill'], [t[0] for t in w.get('trace', [])]) for w in refb.get(s, [])])
    for s in chk2)
print('核对2 大波段(结构) vs nested.py C：核对 %d 只，不一致 %d 只' % (len(chk2), mis2))


def add_meta(waves_by_sym, snaps_by_sym, alive_by_sym=None):
    """给每条波段补 final_span（P24：临终冻结的未推进时长，不是全程最大）、死亡/出生日期；
    返回全市场拍平列表（含活到数据末的）。waves 就地改。"""
    flat = []
    items = [(s, waves_by_sym[s]) for s in waves_by_sym]
    if alive_by_sym:
        items += [(s, [alive_by_sym[s]]) for s in alive_by_sym]
    for s, ws in items:
        last = len(rows[s]) - 1
        for w in ws:
            if w.get('d') is not None:
                # 死亡那根收盘时的未推进时长 = 前一根快照 + 1（引擎在死亡那根先累加再判死）；
                # 出生即死的边界（仅大波段可能）记 1
                prev = snaps_by_sym[s][w['d'] - 1] if w['d'] - 1 >= w['b'] else None
                w['final_span'] = prev['no_new_span'] + 1 if prev is not None else 1
                w['dd'] = rows[s][w['d']][0]
            else:
                w['final_span'] = snaps_by_sym[s][last]['no_new_span']
                w['dd'] = None
            w['bd'] = rows[s][w['b']][0]
            w['sym'] = s
            flat.append(w)
    return flat


def level(name, flat, snaps_by_sym, count_key):
    """in-sample 全历史池分布（对照）+ 扩展窗逐 bar 分位（P10）。返回 (已死, 活, 采样)。"""
    dead = [w for w in flat if w.get('d') is not None]
    alive = [w for w in flat if w.get('d') is None]
    fn = {d: sorted(w[count_key] for w in dead if w['dir'] == d) for d in ('UP', 'DN')}
    fs = {d: sorted(w['final_span'] for w in dead if w['dir'] == d) for d in ('UP', 'DN')}
    print('== %s：已死 %d 条（活到数据末 %d 条）' % (name, len(dead), len(alive)))
    for d in ('UP', 'DN'):
        v = fn[d]
        print('  %s 最终只数 中位 %s P90 %s 最大 %s；池 %d 条' % (d, v[len(v)//2], v[int(.9*len(v))], v[-1], len(v)))
    for d in ('UP', 'DN'):
        v = fs[d]
        print('  %s 临终未推进 中位 %s P90 %s 最大 %s' % (d, v[len(v)//2], v[int(.9*len(v))], v[-1]))
    pool = ExpandingPool(dead, count_key)
    sample = []
    for s in sorted(rows):
        for i, sn in enumerate(snaps_by_sym[s]):
            if sn is None or i % 60 != 0:
                continue
            pn, ps = pool.before(rows[s][i][0], sn['dir'])
            sample.append(dict(sym=s, date=rows[s][i][0], dir=sn['dir'], n=sn['n'],
                               no_new_span=sn['no_new_span'], wave_age=sn.get('wave_age'),
                               pct_n=pct(fn[sn['dir']], sn['n']),
                               pct_span=pct(fs[sn['dir']], sn['no_new_span']),
                               pct_n_exp=pct(pn, sn['n']),
                               pct_span_exp=pct(ps, sn['no_new_span'])))
    return dead, alive, sample


SW_all = {s: small_waves(res[s]) for s in res}
flat_s = add_meta(SW_all, snaps_small)
flat_b = add_meta(bigs_all, snaps_big, alive_big)

dead_s, alive_s, sample_s = level('小波段', flat_s, snaps_small, 'n')
dead_b, alive_b, sample_b = level('大波段', flat_b, snaps_big, 'cnt')

json.dump(dict(
    small=[dict(sym=w['sym'], dir=w['dir'], b=w['b'], d=w['d'], bd=w['bd'], dd=w['dd'],
                n=w['n'], final_span=w['final_span']) for w in flat_s],
    big=[dict(sym=w['sym'], dir=w['dir'], b=w['b'], d=w['d'], bd=w['bd'], dd=w['dd'],
              cnt=w['cnt'], nsw=w['nsw'], final_span=w['final_span']) for w in dead_b],
    alive_big=[dict(sym=w['sym'], dir=w['dir'], b=w['b'], bd=w['bd'], cnt=w['cnt'],
                    nsw=w['nsw'], final_span=w['final_span']) for w in alive_b],
    alive_small_n=len(alive_s),
    sample_small=sample_s, sample_big=sample_b),
    open(os.path.join(OUT, 'percentile_first.json'), 'w'), ensure_ascii=False)
print('->', os.path.join(OUT, 'percentile_first.json'))
