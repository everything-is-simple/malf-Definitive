# -*- coding: utf-8 -*-
"""编号图：314 只 与 全市场（5581 只）的分位池分布对比（CDF）。
数据：data/processed/first_run/percentile_first.json（314 只）对 full_run/（全市场）。
输出：docs/malf-definitive-figs/fig-13-fullmarket-cdf.svg（图 13）
口径：已死波段按方向分池；横轴截尾，纵轴 = 样本中 ≤x 的比例。
"""
import json, os, sys
from bisect import bisect_right

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

A = json.load(open(os.path.join(ROOT, 'data', 'processed', 'first_run', 'percentile_first.json'), encoding='utf-8'))
B = json.load(open(os.path.join(ROOT, 'data', 'processed', 'full_run', 'percentile_first.json'), encoding='utf-8'))

RED, GRN, GRAY = '#D40000', '#009944', '#777777'


def cdf(vals, cap, step=1):
    """返回 [(x, y)]，y = #(v<=x)/N，x 从 0 或 1 到 cap。"""
    vals = sorted(v for v in vals if v is not None)
    n = len(vals)
    x0 = 0 if min(vals, default=0) == 0 else 1
    return [(x, bisect_right(vals, x) / n) for x in range(x0, cap + 1, step)], n


def series(run, level, key):
    """level: 'small'|'big'；返回 {'UP': sorted dead values, 'DN': ...}。小波段列表含活波段，滤掉 d=None。"""
    src = run[level]
    if level == 'small':
        src = [w for w in src if w['d'] is not None]
    k = 'n' if level == 'small' else 'cnt'
    return {d: sorted(w[k] for w in src if w['dir'] == d) for d in ('UP', 'DN')}


PANELS = [
    ('小波段 · 最终只数', 'small', 30, 1),
    ('小波段 · 临终未推进（根）', 'small_span', 40, 1),
    ('大波段 · 最终只数', 'big', 40, 1),
    ('大波段 · 临终未推进（根）', 'big_span', 150, 5),
]

W, Hh = 680, 528
PW, PH = 300, 205
COLX = [40, 370]
ROWY = [62, 300]
MARG_L, MARG_B = 42, 30


def panel(px, py, title, curves, cap):
    """curves: list of (pts, color, dash, label)。画一个 CDF 面板。"""
    o = []
    x0, y0 = COLX[px] + MARG_L, ROWY[py]
    iw, ih = PW - MARG_L - 8, PH - MARG_B - 16
    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#bbb"/>' % (x0, y0, iw, ih))
    for f in (0.25, 0.5, 0.75):
        yy = y0 + ih * (1 - f)
        o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#ddd" stroke-width="0.5"/>' % (x0, yy, x0 + iw, yy))
    o.append('<text x="%d" y="%d" font-size="12" fill="#333">%s</text>' % (x0, y0 - 6, title))
    # 横轴刻度
    for t in range(0, cap + 1, max(1, cap // 5)):
        xx = x0 + iw * t / cap
        o.append('<text x="%.1f" y="%d" font-size="9" fill="#999" text-anchor="middle">%d</text>' % (xx, y0 + ih + 12, t))
    o.append('<text x="%d" y="%d" font-size="9" fill="#999">0</text>' % (x0 - 12, y0 + ih + 3))
    o.append('<text x="%d" y="%d" font-size="9" fill="#999">1</text>' % (x0 - 12, y0 + 3))
    for pts, col, dash, _ in curves:
        d = 'M' + ' L'.join('%.1f,%.1f' % (x0 + iw * x / cap, y0 + ih * (1 - y)) for x, y in pts)
        dd = ' stroke-dasharray="5 3"' if dash else ''
        o.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.6"%s/>' % (d, col, dd))
    return o


o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" font-family="var(--font-sans)" width="100%%">' % (W, Hh)]
o.append('<title>314 只与全市场的分位池分布对比</title>'
         '<desc>四个面板各是已死波段池的累积分布：小波段最终只数、小波段临终未推进、大波段最终只数、大波段临终未推进。'
         '红线上涨池、绿线下跌池；实线全市场 5581 只，虚线 314 只。两组曲线几乎重合。横轴截尾。</desc>')

for idx, (title, level, cap, step) in enumerate(PANELS):
    px, py = idx % 2, idx // 2
    base = level.split('_')[0]
    span = level.endswith('span')

    def vals(run, d):
        src = run[base]
        if base == 'small':
            src = [w for w in src if w['d'] is not None]
        k = 'final_span' if span else ('n' if base == 'small' else 'cnt')
        return sorted(w[k] for w in src if w['dir'] == d)

    curves = []
    for d, col in (('UP', RED), ('DN', GRN)):
        pa, na = cdf(vals(A, d), cap, step)
        pb, nb = cdf(vals(B, d), cap, step)
        curves.append((pb, col, False, '%s 全市场 n=%d' % (d, nb)))
        curves.append((pa, col, True, '%s 314只 n=%d' % (d, na)))
    o += panel(px, py, title, curves, cap)

# 图例（顶部专用条）
lx, ly = 40, 12
o.append('<rect x="%d" y="%d" width="14" height="3" fill="%s"/>' % (lx, ly, RED))
o.append('<text x="%d" y="%d" font-size="10" fill="#333">上涨池 UP</text>' % (lx + 20, ly + 4))
o.append('<rect x="%d" y="%d" width="14" height="3" fill="%s"/>' % (lx + 90, ly, GRN))
o.append('<text x="%d" y="%d" font-size="10" fill="#333">下跌池 DN</text>' % (lx + 110, ly + 4))
o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.6"/>' % (lx + 190, ly + 1, lx + 214, ly + 1, GRAY))
o.append('<text x="%d" y="%d" font-size="10" fill="#333">实线 全市场（5,561,998 根）</text>' % (lx + 220, ly + 4))
o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.6" stroke-dasharray="5 3"/>' % (lx + 430, ly + 1, lx + 454, ly + 1, GRAY))
o.append('<text x="%d" y="%d" font-size="10" fill="#333">虚线 314 只样本（341,593 根）</text>' % (lx + 460, ly + 4))
o.append('<text x="%d" y="%d" font-size="10" fill="#999">2020-01-02 到 2024-12-31，日线，后复权。横轴截尾；纵轴 = 池内 ≤x 的比例。</text>' % (40, Hh - 8))

o.append('</svg>')
out = os.path.join(ROOT, 'docs', 'malf-definitive-figs', 'fig-13-fullmarket-cdf.svg')
open(out, 'w', encoding='utf-8').write('\n'.join(o))
print('->', out)
