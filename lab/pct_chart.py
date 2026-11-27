# -*- coding: utf-8 -*-
"""单标的 5 年全景图（不编号）：K线 + 大波段时间带 + 小波段新高第几只 n + 守护点台阶 + 死亡叉，
下方面板 = 逐 bar 扩展窗分位 pct_n_exp（P10，无未来函数）与 pct_span_exp（历史池使用临终冻结未推进值）。
用法：python lab/pct_chart.py 000001 [tag]
输出：lab/figs/pct_<sym>_<tag>.svg
"""
import csv, json, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding='utf-8')
from malf.core import small_run, small_waves, big_run, _px
from malf.percentile import pct, ExpandingPool

sym = sys.argv[1]
tag = sys.argv[2] if len(sys.argv) > 2 else 'a'
BASE = os.path.join(ROOT, 'data', 'raw')
OUT = os.path.join(ROOT, 'lab', 'figs')
os.makedirs(OUT, exist_ok=True)

bars = [x for x in csv.DictReader(open(os.path.join(BASE, 'bars.csv'), encoding='utf-8')) if x['symbol'] == sym]
bars.sort(key=lambda r: r['date'])
n = len(bars)
H = [_px(float(r['high'])) for r in bars]   # P25：与引擎同一比较域
L = [_px(float(r['low'])) for r in bars]
ev, snaps = small_run([(r['date'], float(r['open']), float(r['high']), float(r['low']), float(r['close'])) for r in bars])
SW = small_waves(ev)
bigs, alive = big_run(H, L, SW)
if alive is not None:
    bigs = bigs + [alive]

# Full-market dead small-wave pool (expanding window). 2026-11-27 起读 P28 修正后的重跑结果。
fr = json.load(open(os.path.join(ROOT, 'data', 'processed', 'full_run_1127', 'percentile_first.json'), encoding='utf-8'))
pool = ExpandingPool(fr['small'])
pct_n = [None] * n
for i, r in enumerate(bars):
    sn = snaps[i]
    if sn is None:
        continue
    pn, ps = pool.before(r['date'], sn['dir'])
    pct_n[i] = (pct(pn, sn['n']), pct(ps, sn['no_new_span']))

# ---- 图 ----
W = 1240
P1H, P2H, GAP = 430, 150, 34          # 上图高、下方面板高、间距
Hh = P1H + GAP + P2H
PW = min(1.0, (W - 60.0) / n)
X0 = (W - PW * n) / 2
lo = min(L)
hi = max(H)
pad = (hi - lo) * 0.10
lo, hi = lo - pad, hi + pad


def X(i):
    return X0 + PW * (i - a) + PW / 2


a = 0


def Y(p):
    return 16 + (P1H - 60) * (hi - p) / (hi - lo)


Y2T, Y2B = P1H + GAP + 8, Hh - 26    # 分位面板纵轴（0~1 倒置）

o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" font-family="var(--font-sans)" width="100%%">' % (W, Hh)]
o.append('<title>%s 五年 HH(n) 与扩展窗分位</title><desc>上：K线，红绿底带是大波段（红涨绿跌），红号是新高第几只，灰虚线是守护点台阶，叉是击穿那根。下：逐bar扩展窗分位 pct_n（实线）与 pct_span（虚线，历史样本为临终冻结未推进值），无未来函数。</desc>' % sym)

# 大波段时间带
for k, w in enumerate(bigs):
    end = w['d'] if w.get('d') is not None else n - 1
    col = '#D40000' if w['dir'] == 'UP' else '#009944'
    o.append('<rect x="%.1f" y="16" width="%.1f" height="%d" fill="%s" fill-opacity="0.07"/>' % (
        X(w['b']) - PW / 2, X(end) - X(w['b']) + PW, P1H - 44, col))
    o.append('<text x="%.1f" y="%d" font-size="10" fill="%s">大%s #%d cnt=%d%s</text>' % (
        X(w['b']), 30 if k % 2 == 0 else 46, col, '涨' if w['dir'] == 'UP' else '跌', k + 1, w['cnt'],
        '（活到数据末）' if w.get('d') is None else ''))

# K 线
for i in range(n):
    c = float(bars[i]['close'])
    up = c >= float(bars[i]['open'])
    col = '#D40000' if up else '#009944'
    x = X(i)
    o.append('<line x1="%.2f" y1="%.1f" x2="%.2f" y2="%.1f" stroke="%s" stroke-width="0.5"/>' % (
        x, Y(H[i]), x, Y(L[i]), col))
    y0, y1 = Y(max(float(bars[i]['open']), c)), Y(min(float(bars[i]['open']), c))
    o.append('<rect x="%.2f" y="%.1f" width="%.2f" height="%.1f" fill="%s"/>' % (
        x - PW / 2.4, y0, PW / 1.2, max(0.6, y1 - y0), col))

# 守护点台阶（灰虚线）+ 死亡叉
for w in SW:
    end = w['d'] if w['d'] is not None else n - 1
    g = w['guard']
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#888" stroke-width="0.8" stroke-dasharray="4 3"/>' % (
        X(w['b']) - PW / 2, Y(g), X(end), Y(g)))
    if w['d'] is not None:
        o.append('<text x="%.1f" y="%.1f" font-size="9" fill="#555">×</text>' % (X(w['d']) - 3, Y(L[w['d']]) + 10))
    o.append('<circle cx="%.1f" cy="%.1f" r="1.6" fill="none" stroke="#888" stroke-width="0.8"/>' % (X(w['b']), Y(H[w['b']] if w['dir'] == 'UP' else L[w['b']])))

# 新高第几只（红/绿号，标在刷新那根的最高/最低处）
for e in ev:
    if e['kind'] != 'new':
        continue
    i = e['i']
    if e['dir'] == 'UP':
        o.append('<text x="%.1f" y="%.1f" font-size="8" fill="#D40000" text-anchor="middle">%d</text>' % (X(i), Y(H[i]) - 3, e['n']))
    else:
        o.append('<text x="%.1f" y="%.1f" font-size="8" fill="#009944" text-anchor="middle">%d</text>' % (X(i), Y(L[i]) + 9, e['n']))

# 分位面板
o.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="none" stroke="#ccc"/>' % (X0, Y2T, PW * n, Y2B - Y2T))
for v in (0.25, 0.5, 0.75, 0.9):
    y = Y2T + (Y2B - Y2T) * (1 - v)
    o.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#ddd" stroke-width="0.5"/>' % (X0, y, X0 + PW * n, y))
    o.append('<text x="%.1f" y="%.1f" font-size="9" fill="#999">%g</text>' % (X0 + PW * n + 4, y + 3, v))


def path(get, dash=None):
    pts = [(X(i), Y2T + (Y2B - Y2T) * (1 - v)) for i in range(n) if pct_n[i] and (v := get(pct_n[i])) is not None]
    if not pts:
        return ''
    d = 'M' + ' L'.join('%.1f,%.1f' % p for p in pts)
    s = '<path d="%s" fill="none" stroke-width="1.1" %s/>' % (d, 'stroke="#D40000"' if not dash else 'stroke="#777" stroke-dasharray="5 3"')
    return s


o.append(path(lambda t: t[0]))
o.append(path(lambda t: t[1], dash=True))
o.append('<text x="%.1f" y="%d" font-size="11" fill="#D40000">pct_n（当前只数在历史最终只数里的分位，扩展窗）</text>' % (X0, Y2T - 4))
o.append('<text x="%.1f" y="%d" font-size="11" fill="#777">pct_span（虚线，当前未推进时长在历史临终未推进值里的分位）</text>' % (X0 + 400, Y2T - 4))

# 年份刻度
for i in range(0, n, 244):
    o.append('<text x="%.1f" y="%d" font-size="9" fill="#999">%s</text>' % (X(i), Hh - 8, bars[i]['date'][:4]))

o.append('</svg>')
out = os.path.join(OUT, 'pct_%s_%s.svg' % (sym, tag))
open(out, 'w', encoding='utf-8').write('\n'.join(o))
print('->', out, n, '根', len(SW), '条小波段', len(bigs), '条大波段')
