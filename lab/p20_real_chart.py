# -*- coding: utf-8 -*-
"""实跑看图（不编号）：一段真实日线上，程序认出的盘整区、新高第几只、守护点（含上移台阶）、击穿那根。
输入是 p20_real_c.py 的结果（写法 C：小波段守护点随最新确认的 HL / LH 上移）。
用法：python lab/p20_real_chart.py 002899 2020-03-16 2020-08-24 a
"""
import csv, json, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作台根目录
BASE = os.path.join(ROOT, 'data', 'raw')                        # 只读：bars.csv
SRC = os.path.join(ROOT, 'data', 'processed', 'p20_real_c')     # 输入：p20_real_c.py 的结果
FIG = os.path.join(ROOT, 'lab', 'figs')                         # 看图用，未编号
sys.stdout.reconfigure(encoding='utf-8')

sym, d0, d1, tag = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
bars = [x for x in csv.DictReader(open(os.path.join(BASE, 'bars.csv'), encoding='utf-8')) if x['symbol'] == sym]
bars.sort(key=lambda r: r['date'])
res = json.load(open(os.path.join(SRC, 'events.json'), encoding='utf-8'))[sym]
a = next(i for i, r in enumerate(bars) if r['date'] >= d0)
b = next((i for i, r in enumerate(bars) if r['date'] > d1), len(bars))
m = b - a
print(sym, bars[a]['date'], '~', bars[b - 1]['date'], m, '根')

# 这一段里的事，给写图注用
born = [e for e in res if e['kind'] == 'born' and a <= e['i'] < b]
dead = [e for e in res if e['kind'] == 'dead' and a <= e['i'] < b]
guards = [e for e in res if e['kind'] == 'guard' and a <= e['i'] < b]
print('出生', len(born), '死亡', len(dead), '守护点上移', len(guards))
print('  同向', sum(e['same'] for e in born), '反向', sum(not e['same'] for e in born),
      '同向里没过前顶', sum(e['same'] and e['below_prev'] for e in born))

W, Hh = 680, 300
PW = min(6.0, 600.0 / m)
X0 = (W - PW * m) / 2
lo = min(float(r['low']) for r in bars[a:b])
hi = max(float(r['high']) for r in bars[a:b])
pad = (hi - lo) * 0.16
lo, hi = lo - pad, hi + pad


def X(i):
    return X0 + PW * (i - a) + PW / 2


def Y(p):
    return 14 + (Hh - 50) * (hi - p) / (hi - lo)


o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" font-family="var(--font-sans)" width="100%%">' % (W, Hh)]
o.append('<title>%s 真实日线上的盘整区、新高第几只与守护点</title><desc>蓝底是程序认出的盘整区，蓝虚线是盘整高值或盘整低值，红号绿号是新高、新低第几只，灰虚线是守护点（会跟着抬高的台阶走），叉是击穿那根。</desc>' % sym)

# 盘整区（蓝底）只画这一段里出生的那些
for e in born:
    z0, z1 = e['zone']
    if z1 < a:
        continue
    r0 = bars[z0]
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#378ADD" fill-opacity="0.14"/>' % (
        X(max(z0, a)) - PW / 2, Y(float(r0['high'])), X(z1) - X(max(z0, a)) + PW, Y(float(r0['low'])) - Y(float(r0['high']))))
# K 线
wu, wd, body = [], [], []
for i in range(a, b):
    r = bars[i]
    op, h, l, c = (float(r[k]) for k in ('open', 'high', 'low', 'close'))
    up = c >= op
    (wu if up else wd).append('M%.1f %.1fV%.1f' % (X(i), Y(h), Y(l)))
    y1, y2 = Y(max(op, c)), Y(min(op, c))
    body.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (
        X(i) - max(PW * .36, 1), y1, max(PW * .72, 2), max(y2 - y1, 1), '#E24B4A' if up else '#4A8A2A'))
o.append('<path d="%s" stroke="#E24B4A" stroke-width="1"/>' % ''.join(wu))
o.append('<path d="%s" stroke="#4A8A2A" stroke-width="1"/>' % ''.join(wd))
o.extend(body)

# 每条小波段：盘整高值/低值线、守护点台阶、号、叉
lastx = {}
for e in born:
    bi = e['i']
    de = next((x for x in res if x['kind'] == 'dead' and x['i'] > bi), None)
    di = de['i'] if de else b - 1
    di = min(di, b - 1)
    up = e['dir'] == 'UP'
    col = '#F06565' if up else '#8FCB5A'
    z0 = e['zone'][0]
    # 盘整高值 / 低值：从低点（高点）那根画到出生那根
    o.append('<path d="M%.1f %.1fH%.1f" stroke="#185FA5" stroke-width="1.2" stroke-dasharray="3 3"/>' % (X(z0), Y(e['level']), X(bi)))
    # 守护点：出生守护点 -> 每次 guard 事件换一级 -> 死
    pts = [(bi, e['guard'])] + [(g['i'], g['g']) for g in guards if bi < g['i'] <= di] + [(di + 1, None)]
    path = 'M%.1f %.1f' % (X(pts[0][0]), Y(pts[0][1]))
    for (i0, g0), (i1, g1) in zip(pts, pts[1:]):
        path += 'H%.1f' % X(i1)
        if g1 is not None:
            path += 'V%.1f' % Y(g1)
    o.append('<path d="%s" stroke="#8C8A82" stroke-width="1.3" stroke-dasharray="5 3" fill="none"/>' % path)
    # 号：出生那根记 1，之后每只新高
    N = de['n'] if de else None
    last = -99
    for x in res:
        if x['kind'] not in ('born', 'new') or not (bi <= x['i'] <= di) or x.get('dir') != e['dir']:
            continue
        nn = 1 if x['kind'] == 'born' else x['n']
        if not (nn == 1 or nn == N or nn % 5 == 0):
            continue
        if X(x['i']) - last < (11 if nn == N else 16):
            continue
        last = X(x['i'])
        r = bars[x['i']]
        if up:
            o.append('<text x="%.1f" y="%.1f" font-size="11" font-weight="%s" fill="%s" text-anchor="middle">%d</text>' % (
                X(x['i']), Y(float(r['high'])) - 4, '600' if nn == 1 else '400', col, nn))
        else:
            o.append('<text x="%.1f" y="%.1f" font-size="11" font-weight="%s" fill="%s" text-anchor="middle">%d</text>' % (
                X(x['i']), Y(float(r['low'])) + 13, '600' if nn == 1 else '400', col, nn))
    if de is not None and de['i'] < b:
        o.append('<path d="M%.1f %.1fm-4 -4l8 8m0 -8l-8 8" stroke="#55534D" stroke-width="1.7"/>' % (X(de['i']), Y(de['guard'])))
# 日期轴
lastx = -99
labels = [(a, bars[a]['date'])]
for i in range(a, b):
    d = bars[i]['date']
    if d[5:7] in ('01', '04', '07', '10') and d[8:] == '01':
        labels.append((i, d[:7]))
for i, t in labels:
    if X(i) - lastx < 60:
        continue
    lastx = X(i)
    o.append('<text x="%.1f" y="%d" font-size="11" fill="var(--color-text-tertiary)" text-anchor="middle">%s</text>' % (X(i), Hh - 8, t))
o.append('<text x="%.1f" y="%d" font-size="11" fill="var(--color-text-tertiary)" text-anchor="end">%s</text>' % (X(b - 1), Hh - 8, bars[b - 1]['date']))
o.append('</svg>')
svg = ''.join(o)
p = os.path.join(FIG, 'p20c_%s.svg' % tag)
open(p, 'w', encoding='utf-8').write(svg)
shot = os.path.join(FIG, '_shot')
os.makedirs(shot, exist_ok=True)
open(os.path.join(shot, 'shot_p20c_%s.svg' % tag), 'w', encoding='utf-8').write(
    svg.replace('width="100%"', 'width="680" height="300"').replace('<title>', '<rect width="680" height="300" fill="#ffffff"/><title>', 1)
        .replace('var(--color-text-tertiary)', '#888780').replace('var(--font-sans)', 'Microsoft YaHei, sans-serif'))
print('  ->', p)
