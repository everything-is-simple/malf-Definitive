# -*- coding: utf-8 -*-
"""按波段总只数的分位分档，每档挑一只真实例子，画这条小波段的一生（前面的过渡 + 出生 + 新高第几只 + 击穿）。
只画这一条波段自己的东西：它的盘整区、它的守护点、它的号、它的叉。"""
import csv, json, os, sys, collections, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作台根目录
BASE = os.path.join(ROOT, 'data', 'raw')                   # 只读：bars.csv
OUT = os.path.join(ROOT, 'data', 'processed', 'p20_real')  # 输入：p20_real.py 的结果
FIG = os.path.join(ROOT, 'lab', 'figs')                    # 看图用，未编号
SHOT = os.path.join(FIG, '_shot')                          # 截图用的包装件
os.makedirs(SHOT, exist_ok=True)
rows = collections.defaultdict(list)
for x in csv.DictReader(open(os.path.join(BASE, 'bars.csv'), encoding='utf-8')):
    rows[x['symbol']].append(x)
for k in rows:
    rows[k].sort(key=lambda r: r['date'])
res = json.load(open(os.path.join(OUT, 'events.json'), encoding='utf-8'))

waves = []
for s, ev in res.items():
    born = None
    prev_dead = None
    for e in ev:
        if e['kind'] == 'dead':
            if born is not None:
                waves.append(dict(sym=s, born=born, dead=e, prev_dead=prev_dead))
                born = None
            prev_dead = e
        elif e['kind'] == 'born':
            born = e
print('波段（有生有死）', len(waves))
ns = sorted(w['dead']['n'] for w in waves)
q = lambda p: ns[min(len(ns) - 1, int(p * len(ns)))]
print('总只数分位 P10/P25/P50/P75/P90/P95/P99/最大', [q(p) for p in (.1, .25, .5, .75, .9, .95, .99)], ns[-1])

BUCKETS = [(1, 1, 'q1'), (2, 3, 'q2'), (4, 6, 'q3'), (7, 14, 'q4'), (15, 999, 'q5')]
W, Hh = 680, 300
picked = []
for lo_, hi_, tag in BUCKETS:
    b = [w for w in waves if lo_ <= w['dead']['n'] <= hi_]
    share = len(b) / len(waves)
    lens = [w['dead']['i'] - w['born']['i'] + 1 for w in b]
    med = statistics.median(lens)
    same = sum(1 for w in b if w['born']['same']) / len(b)
    below = sum(1 for w in b if w['born']['same'] and w['born']['below_prev']) / max(1, sum(1 for w in b if w['born']['same']))
    zl = collections.Counter(min(w['born']['zone'][1] - w['born']['zone'][0] + 1, 5) for w in b)
    print('%s %d-%d 只: %d 条 占 %.1f%%; 活多少根 中位 %s; 同向出生 %.0f%%; 同向里没过前顶 %.0f%%; 盘整区 2/3/4/5+ 根 %s' % (
        tag, lo_, hi_, len(b), share * 100, med, same * 100, below * 100, [round(zl.get(k, 0) / len(b), 2) for k in (2, 3, 4, 5)]))
    used = {p['sym'] for p in picked}
    cand = [w for w in b if w['sym'] not in used and w['prev_dead'] is not None]
    cand.sort(key=lambda w: abs((w['dead']['i'] - w['born']['i'] + 1) - med))
    # 上下跌交替挑，标的不重复，长度最接近本档中位数
    want_dir = 'UP' if len(picked) % 2 == 0 else 'DN'
    pick = None
    for d in (want_dir, 'DN' if want_dir == 'UP' else 'UP'):
        c2 = [w for w in cand if w['dead']['n'] == lo_ and w['born']['dir'] == d] or \
             [w for w in cand if w['born']['dir'] == d]
        if c2:
            pick = c2[0]
            break
    picked.append(pick)
    print('   例子', pick['sym'], rows[pick['sym']][pick['born']['i']]['date'], '->', rows[pick['sym']][pick['dead']['i']]['date'],
          '只数', pick['dead']['n'], '活', pick['dead']['i'] - pick['born']['i'] + 1, '根', '方向', pick['born']['dir'],
          '同向', pick['born']['same'], '过渡', pick['born']['trans'], '根')


def draw(w, tag):
    s = w['sym']
    bars = rows[s]
    n = len(bars)
    bi, di = w['born']['i'], w['dead']['i']
    a = max(0, w['prev_dead']['i'] - 12)
    b = min(n, di + 8)
    if b - a < 50:
        a = max(0, a - (50 - (b - a)) // 2)
        b = min(n, b + (50 - (b - a)))
    m = b - a
    PW = min(6.0, 600.0 / m)
    X0 = (W - PW * m) / 2
    Hh2 = 280
    lo = min(float(r['low']) for r in bars[a:b])
    hi = max(float(r['high']) for r in bars[a:b])
    pad = (hi - lo) * 0.14
    lo, hi = lo - pad, hi + pad

    def X(i):
        return X0 + PW * (i - a) + PW / 2

    def Y(p):
        return 16 + (Hh2 - 46) * (hi - p) / (hi - lo)

    bw = w['born']
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" font-family="var(--font-sans)" width="100%%">' % (W, Hh2 + 20)]
    o.append('<title>%s 小波段的一生</title><desc>蓝底是盘整区，红号绿号是新高新低第几只，灰线是守护点，叉是击穿那根。</desc>' % s)
    z0, z1 = bw['zone']
    r0 = bars[z0]
    o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#378ADD" fill-opacity="0.22"/>' % (
        X(z0) - PW / 2, Y(float(r0['high'])), X(z1) - X(z0) + PW, Y(float(r0['low'])) - Y(float(r0['high']))))
    wu, wd, body = [], [], []
    for i in range(a, b):
        r = bars[i]
        op, h, l, c = (float(r[k]) for k in ('open', 'high', 'low', 'close'))
        up = c >= op
        (wu if up else wd).append('M%.1f %.1fV%.1f' % (X(i), Y(h), Y(l)))
        y1, y2 = Y(max(op, c)), Y(min(op, c))
        body.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (X(i) - max(PW * .36, 1), y1, max(PW * .72, 2), max(y2 - y1, 1), '#E24B4A' if up else '#4A8A2A'))
    o.append('<path d="%s" stroke="#E24B4A" stroke-width="1"/>' % ''.join(wu))
    o.append('<path d="%s" stroke="#4A8A2A" stroke-width="1"/>' % ''.join(wd))
    o.extend(body)
    o.append('<path d="M%.1f %.1fH%.1f" stroke="#185FA5" stroke-width="1.2" stroke-dasharray="3 3"/>' % (X(z0) - PW / 2, Y(bw['level']), X(bi)))
    o.append('<path d="M%.1f %.1fH%.1f" stroke="#B4B2A9" stroke-width="1.3" stroke-dasharray="5 3"/>' % (X(bi), Y(bw['guard']), X(di)))
    up = bw['dir'] == 'UP'
    col = '#F06565' if up else '#8FCB5A'
    N = w['dead']['n']
    lastx = -99
    for i in range(bi, di + 1):
        e = next((x for x in res[s] if x['kind'] in ('born', 'new') and x['i'] == i and x['dir'] == bw['dir'] and x.get('n', 1) == (1 if x['kind'] == 'born' else x.get('n'))), None)
        if e is None:
            continue
        nn = 1 if e['kind'] == 'born' else e['n']
        if not (nn == 1 or nn == N or (X(i) - lastx >= 18 and (N <= 12 or nn % 5 == 0))):
            continue
        lastx = X(i)
        r = bars[i]
        if up:
            o.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="%s" fill="%s" text-anchor="middle">%d</text>' % (X(i), Y(float(r['high'])) - 4, '500' if nn == 1 else '400', col, nn))
        else:
            o.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="%s" fill="%s" text-anchor="middle">%d</text>' % (X(i), Y(float(r['low'])) + 14, '500' if nn == 1 else '400', col, nn))
    o.append('<path d="M%.1f %.1fm-4 -4l8 8m0 -8l-8 8" stroke="#B4B2A9" stroke-width="1.7"/>' % (X(di), Y(bw['guard'])))
    o.append('<path d="M%.1f %.1fm-4 -4l8 8m0 -8l-8 8" stroke="#B4B2A9" stroke-width="1.7"/>' % (X(w['prev_dead']['i']), Y(float(bars[w['prev_dead']['i']]['close']))))
    labels = [(a, bars[a]['date'])]
    for i in range(a, b):
        d = bars[i]['date']
        if d[5:7] in ('01', '04', '07', '10') and d[8:] == '01':
            labels.append((i, d[:7]))
    lastx = -99
    for i, t in labels:
        if X(i) - lastx < 56:
            continue
        lastx = X(i)
        o.append('<text x="%.1f" y="%d" font-size="11" fill="var(--color-text-tertiary)" text-anchor="middle">%s</text>' % (X(i), Hh2 + 14, t))
    o.append('<text x="%.1f" y="%d" font-size="11" fill="var(--color-text-tertiary)" text-anchor="end">%s</text>' % (X(b - 1), Hh2 + 14, bars[b - 1]['date']))
    o.append('</svg>')
    svg = ''.join(o)
    p = os.path.join(FIG, 'wave_' + tag + '.svg')
    open(p, 'w', encoding='utf-8').write(svg)
    open(os.path.join(SHOT, 'shot_' + tag + '.svg'), 'w', encoding='utf-8').write(
        svg.replace('width="100%"', 'width="680" height="300"').replace('<title>', '<rect width="680" height="300" fill="#ffffff"/><title>', 1).replace('var(--color-text-tertiary)', '#888780'))
    return p


sys.stdout.reconfigure(encoding='utf-8')
for w, (_, _, tag) in zip(picked, BUCKETS):
    print('  ->', draw(w, tag))
