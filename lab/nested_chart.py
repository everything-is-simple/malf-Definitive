# -*- coding: utf-8 -*-
"""把嵌套实跑（nested.json）里的一条大波段画出来：红号绿号是小波段的新高第几只，顶上蓝号是大波段的新高第几只，蓝虚线是大波段守护点。"""
import csv, json, os, sys, collections, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作台根目录
BASE = os.path.join(ROOT, 'data', 'raw')                   # 只读：bars.csv
OUT = os.path.join(ROOT, 'data', 'processed', 'nested')    # 输入：nested.py 的结果
FIG = os.path.join(ROOT, 'lab', 'figs')                    # 看图用，未编号
SHOT = os.path.join(FIG, '_shot')                          # 截图用的包装件
os.makedirs(SHOT, exist_ok=True)
mode = sys.argv[1]
rows = collections.defaultdict(list)
for x in csv.DictReader(open(os.path.join(BASE, 'bars.csv'), encoding='utf-8')):
    rows[x['symbol']].append(x)
for k in rows:
    rows[k].sort(key=lambda r: r['date'])
d = json.load(open(os.path.join(OUT, 'nested.json'), encoding='utf-8'))[mode]

bigs = [b for s in d['big'] for b in d['big'][s]]
med = statistics.median(b['d'] - b['b'] + 1 for b in bigs if b['nsw'] >= 3)
picked = []
for want in ('UP', 'DN'):
    cand = [b for b in bigs if b['nsw'] >= 3 and b['dir'] == want and 80 <= b['d'] - b['b'] + 1 <= 200
            and b['sym'] not in [p['sym'] for p in picked]]
    cand.sort(key=lambda b: abs((b['d'] - b['b'] + 1) - med))
    picked.append(cand[0])


def draw(w, tag):
    s = w['sym']
    bars = rows[s]
    n = len(bars)
    ev = d['small'][s]['ev']
    bi, di = w['b'], w['d']
    a = max(0, bi - 8)
    b = min(n, di + 10)
    m = b - a
    W, Hh = 680, 330
    PW = min(6.0, 620.0 / m)
    X0 = (W - PW * m) / 2
    lo = min(float(r['low']) for r in bars[a:b])
    hi = max(float(r['high']) for r in bars[a:b])
    pad = (hi - lo) * 0.1
    lo, hi = lo - pad, hi + pad

    def X(i):
        return X0 + PW * (i - a) + PW / 2

    def Y(p):
        return 40 + (Hh - 76) * (hi - p) / (hi - lo)

    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" font-family="var(--font-sans)" width="100%%">' % (W, Hh + 20)]
    o.append('<title>%s 大波段套着小波段</title><desc>红号绿号是小波段的新高第几只，顶上蓝号是大波段的新高第几只，蓝虚线是大波段守护点。</desc>' % s)
    o.append('<path d="M0 27.5H680" stroke="#888780" stroke-opacity="0.4"/>')
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
    # 大波段守护点：台阶
    pts = [(bi, w['guard'])] + [tuple(t) for t in w.get('trace', [])] + [(di + 1, None)]
    path = ''
    for (i0, g), (i1, _) in zip(pts, pts[1:]):
        path += 'M%.1f %.1fH%.1f' % (X(i0), Y(g), X(i1))
    o.append('<path d="%s" stroke="#4A9BEF" stroke-width="2.2" stroke-dasharray="7 4" fill="none"/>' % path)
    # 小波段的号和叉
    lastx = -99
    cur = None
    for e in ev:
        if not (a <= e['i'] < b):
            continue
        r = bars[e['i']]
        up = e['dir'] == 'UP'
        col = '#F06565' if up else '#8FCB5A'
        if e['kind'] == 'born':
            cur = e
            lastx = -99
            o.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="500" fill="%s" text-anchor="middle">1</text>' % (X(e['i']), Y(float(r['high'])) - 5 if up else Y(float(r['low'])) + 14, col))
            lastx = X(e['i'])
        elif e['kind'] == 'new':
            nn = e['n']
            if e['i'] + 1 < n:
                nxt = [x for x in ev if x['kind'] == 'dead' and x['i'] == e['i'] + 1]
            if not (X(e['i']) - lastx >= 28):
                continue
            lastx = X(e['i'])
            o.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" text-anchor="middle">%d</text>' % (X(e['i']), Y(float(r['high'])) - 5 if up else Y(float(r['low'])) + 14, col, nn))
        elif e['kind'] == 'dead':
            o.append('<path d="M%.1f %.1fm-3 -3l6 6m0 -6l-6 6" stroke="%s" stroke-width="1.4"/>' % (X(e['i']), Y(float(r['high'])) - 16 if up else Y(float(r['low'])) + 24, col))
    # 大波段的号
    ext = None
    cnt = 0
    lastx = -99
    for i in range(bi, di + 1):
        p = float(bars[i]['high'] if w['dir'] == 'UP' else bars[i]['low'])
        if ext is None or (p > ext if w['dir'] == 'UP' else p < ext):
            ext = p
            cnt += 1
            if i == bi or i == di or cnt % 5 == 0 or X(i) - lastx >= 44:
                o.append('<text x="%.1f" y="%d" font-size="12" font-weight="%s" fill="#4A9BEF" text-anchor="middle">%d</text>' % (X(i), 22, '500' if cnt == 1 else '400', cnt))
                lastx = X(i)
    o.append('<path d="M%.1f %.1fm-4 -4l8 8m0 -8l-8 8" stroke="#4A9BEF" stroke-width="1.8"/>' % (X(di), Y(w['guard'])))
    lastx = -99
    for i in range(a, b):
        dd = bars[i]['date']
        if i == a or (dd[8:] == '01' and dd[5:7] in ('01', '04', '07', '10')):
            if X(i) - lastx < 60:
                continue
            lastx = X(i)
            o.append('<text x="%.1f" y="%d" font-size="11" fill="var(--color-text-tertiary)" text-anchor="middle">%s</text>' % (X(i), Hh + 14, dd if i == a else dd[:7]))
    o.append('</svg>')
    svg = ''.join(o)
    open(os.path.join(FIG, 'nested_%s.svg' % tag), 'w', encoding='utf-8').write(svg)
    open(os.path.join(SHOT, 'shot_nested_%s.svg' % tag), 'w', encoding='utf-8').write(
        svg.replace('width="100%"', 'width="680" height="350"').replace('<title>', '<rect width="680" height="350" fill="#ffffff"/><title>', 1).replace('var(--color-text-tertiary)', '#888780'))
    return bars[bi]['date'], bars[di]['date']


sys.stdout.reconfigure(encoding='utf-8')
for w, tag in zip(picked, ('up', 'dn')):
    print(w['sym'], w['dir'], draw(w, tag), '只数', w['cnt'], '同向小波段', w['nsw'], '活', w['d'] - w['b'] + 1, '根', '守护点台阶', len(w.get('trace', [])))
