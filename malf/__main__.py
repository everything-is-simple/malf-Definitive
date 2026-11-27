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
- 大波段倒算继承（P28，2026-11-27）：继承的读数 = 旧大波段死那根小波段已记的只数，不取它的最终只数；
  快照按时点，从可知日 since 起才写新大波段（malf/core.py big_snaps）；输出带 since / sd / by_kill。
核对：小波段事件与 lab/p20_real_c.py 的 events.json 比结构；大波段与 nested.json 写法 C 比结构
      （只对参考文件里有的标的核对；比 dir/b/d/nsw/by_kill/换位，不比 cnt——
      参考文件出自 2026-11-27 同步成 P28 口径的 lab/nested.py，同一份价格下与引擎逐条一致，
      但它用未取整的 float 比较，_px 取整后只数会有少量临界差异）。
      注意：参考文件出自未量化的 float 比较，_px 取整后
      临界相等的边界情形可能产生少量结构分歧，属预期。
数据：bars_all.csv = 全 A 股（库内 5581 只，2020-2024 窗口内有 K 线的 5328 只），后复权未舍入
      （hithink 导出，见 README 数据来历）。
      【取舍｜已签】不含已退市股；与旧 bars.csv 同复权链。
"""
import csv, collections, json, os, sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from malf.core import small_run, small_waves, big_run, big_snaps, _px
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
CHECK_BAD = [0]       # 快照读数与大波段本子对不上的条数（自检，应为 0）
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
    # 大波段逐 bar 快照（按时点，P28；活到数据末的波段补到最后一根）
    snaps = big_snaps(H, L, bigs, alive)
    # 自检：快照里的读数与大波段自己的本子对得上。
    # 已死的波段看它死前一天那根（死那根的快照可能已被倒算继承的新波段接管）；
    # 死那根如果自己刷新了极值（P26 同根推进+击穿），本子多 1，快照里没有。
    for w in bigs + ([alive] if alive is not None else []):
        if w.get('d') is not None:
            last = w['d'] - 1
            want = w['cnt'] - (1 if w['d'] in w['newbars'] else 0)
        else:
            last, want = len(bars) - 1, w['cnt']
        if snaps[last] is None or snaps[last]['n'] != want:
            CHECK_BAD[0] += 1
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
    ([(w['dir'], w['b'], w['d'], w['nsw'], w['by_kill'], [m['i'] for m in w['moves']]) for w in bigs_all[s]]
     != [(w['dir'], w['b'], w['d'], w['nsw'], w['by_kill'], [t[0] for t in w.get('trace', [])]) for w in refb.get(s, [])])
    for s in chk2)
print('核对2 大波段(结构，不含 cnt) vs nested.py C：核对 %d 只，不一致 %d 只' % (len(chk2), mis2))
print('自检 大波段快照读数 == 本子 cnt（已死的看死前一天）：对不上 %d 条' % CHECK_BAD[0])
_bk = [w for s in bigs_all for w in bigs_all[s] if w['by_kill']]
_all = [w for s in bigs_all for w in bigs_all[s]]
print('P28 倒算继承：已死大波段 %d 条里 %d 条（%.1f%%）；继承来的读数中位 %d' % (
    len(_all), len(_bk), 100 * len(_bk) / max(1, len(_all)), sorted(w['cnt0'] for w in _bk)[len(_bk) // 2] if _bk else 0))


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
                if 'final_span' not in w:
                    # 大波段：big_run 不带 final_span，从快照推同口径值
                    # （L6/L-T4：击穿那根不再加一 → 冻结值 = 前一根快照的未推进时长）
                    prev = snaps_by_sym[s][w['d'] - 1] if w['d'] - 1 >= w['since'] else None
                    w['final_span'] = prev['no_new_span'] if prev is not None else 0
                w['dd'] = rows[s][w['d']][0]
            else:
                w['final_span'] = snaps_by_sym[s][last]['no_new_span']
                w['dd'] = None
            w['bd'] = rows[s][w['b']][0]
            w['sd'] = rows[s][w['since']][0] if 'since' in w else w['bd']   # 大波段可知日（P28）；小波段 = 出生日
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
    # Sort all symbols together so the expanding pool never advances past a later query.
    queries = [(rows[s][i][0], s, i, sn) for s in sorted(rows)
               for i, sn in enumerate(snaps_by_sym[s]) if sn is not None and i % 60 == 0]
    queries.sort(key=lambda q: (q[0], q[1], q[2]))
    for date, s, i, sn in queries:
        pn, ps = pool.before(date, sn['dir'])
        sample.append(dict(sym=s, date=date, dir=sn['dir'], n=sn['n'],
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

# P26：ambiguous_intraday_event 统计（同根推进+击穿的死亡事件，日线还原不了盘中先后）
amb_s = [e for s in res for e in res[s] if e['kind'] == 'dead' and e.get('ambig')]
amb_b = sum(1 for s in bigs_all for w in bigs_all[s] if w['d'] in w['newbars'])  # 活波段无死亡，天然不计
print('== P26 ambiguous_intraday_event：小波段 %d 条 / 大波段 %d 条' % (len(amb_s), amb_b))

json.dump(dict(
    small=[dict(sym=w['sym'], dir=w['dir'], b=w['b'], d=w['d'], bd=w['bd'], dd=w['dd'],
                n=w['n'], final_span=w['final_span']) for w in flat_s],
    big=[dict(sym=w['sym'], dir=w['dir'], b=w['b'], d=w['d'], bd=w['bd'], dd=w['dd'],
              since=w['since'], sd=w['sd'], by_kill=w['by_kill'],
              cnt=w['cnt'], cnt0=w['cnt0'], nsw=w['nsw'], final_span=w['final_span']) for w in dead_b],
    alive_big=[dict(sym=w['sym'], dir=w['dir'], b=w['b'], bd=w['bd'], since=w['since'], sd=w['sd'],
                    by_kill=w['by_kill'], cnt=w['cnt'], cnt0=w['cnt0'], nsw=w['nsw'],
                    final_span=w['final_span']) for w in alive_b],
    alive_small_n=len(alive_s),
    ambig_small=[dict(sym=s2, **{k: e[k] for k in ('i', 'dir', 'n', 'final_span')})
                 for s2 in res for e in res[s2] if e['kind'] == 'dead' and e.get('ambig')],
    ambig_big_n=amb_b,
    sample_small=sample_s, sample_big=sample_b),
    open(os.path.join(OUT, 'percentile_first.json'), 'w'), ensure_ascii=False)
print('->', os.path.join(OUT, 'percentile_first.json'))
