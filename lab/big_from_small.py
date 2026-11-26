# -*- coding: utf-8 -*-
"""大波段从小波段推（八步）。真实 A 股日线实跑，只用 bars.csv 的 high/low。

小波段（用户 2026-11-26 认可写法 C）：
  出生 = 止跌后上破盘整高值那根（P20）；守护点出生时 = 盘整低点，之后换到最新确认的 HL（k=2 分形）；跌破守护点 = 死。
大波段，上涨为例（下跌镜像）：
  ① 小波段走完上升，留下顶（最高的那根、它是第几只）
  ② 小波段守护点被击穿
  ③ ④ 回调；回调低点从击穿那根起记
  ⑤ ⑥ 回升后停一根，盘整高值 = 门禁；上破门禁 = 新生小波段，它的出生守护点 = 回调低点 = 两个小波段之间的低点
  ⑦ ⑧ 新生小波段高过前一个小波段的顶那根：大波段守护点换到那个低点；大波段计数 = 前顶第几只 + 1，之后每根新高 +1
  大波段和第一条同向小波段同时出生，出生守护点 = 那条小波段的出生守护点；第一段两边记的是同一批日线。
守护点哪一根换过去，两种读法都跑：
  prev  前顶 = 上一条同向小波段的顶（八步字面）；
  max   前顶 = 造出大波段最高价的那条小波段的顶（要过了大波段自己的顶才换）。
"""
import csv, json, os, sys, collections, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作台根目录
BASE = os.path.join(ROOT, 'data', 'raw')                    # 只读：bars.csv
OUT = os.path.join(ROOT, 'data', 'processed', 'big8')       # 脚本产物，可重跑
FIG = os.path.join(ROOT, 'lab', 'figs')                     # 看图用，未编号
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')

rows = collections.defaultdict(list)
for x in csv.DictReader(open(os.path.join(BASE, 'bars.csv'), encoding='utf-8')):
    rows[x['symbol']].append(x)
for k in rows:
    rows[k].sort(key=lambda r: r['date'])


def small_run(bars):
    """小波段。与 nested.py 的写法 C 相同，多记 guard 事件（守护点哪一根换的、换到哪）。"""
    H = [float(r['high']) for r in bars]
    L = [float(r['low']) for r in bars]
    n = len(bars)
    ev, state, d = [], None, 0
    up = {'low': 0, 'consol': None, 'voids': 0, 'zone': None}
    dn = {'high': 0, 'consol': None, 'voids': 0, 'zone': None}
    last_dir = None

    def reset(i):
        up.update(low=i, consol=None, voids=0, zone=None)
        dn.update(high=i, consol=None, voids=0, zone=None)

    for i in range(n):
        if state is None:
            if L[i] < L[up['low']]:
                up['low'] = i
                if up['consol'] is not None:
                    up['consol'] = None
                    up['voids'] += 1
            elif up['consol'] is None and i > 0 and H[i] <= H[i - 1]:
                up['consol'] = max(H[up['low']:i + 1])
                up['zone'] = (up['low'], i)
            if H[i] > H[dn['high']]:
                dn['high'] = i
                if dn['consol'] is not None:
                    dn['consol'] = None
                    dn['voids'] += 1
            elif dn['consol'] is None and i > 0 and L[i] >= L[i - 1]:
                dn['consol'] = min(L[dn['high']:i + 1])
                dn['zone'] = (dn['high'], i)
            ub = up['consol'] is not None and H[i] > up['consol']
            db = dn['consol'] is not None and L[i] < dn['consol']
            if ub:
                state = ['UP', 1, L[up['low']], H[i], i, i]
                ev.append(dict(kind='born', i=i, dir='UP', guard=state[2], zone=up['zone'], level=up['consol'], same=(last_dir == 'UP')))
            elif db:
                state = ['DN', 1, H[dn['high']], L[i], i, i]
                ev.append(dict(kind='born', i=i, dir='DN', guard=state[2], zone=dn['zone'], level=dn['consol'], same=(last_dir == 'DN')))
        else:
            st = state
            if st[0] == 'UP':
                if H[i] > st[3]:
                    st[1] += 1
                    st[3] = H[i]
                    st[4] = i
                    ev.append(dict(kind='new', i=i, dir='UP', n=st[1]))
                if i - 2 > st[5] and all(L[i - 2] < L[t] for t in (i - 4, i - 3, i - 1, i)):
                    st[2] = max(st[2], L[i - 2])
                    st[5] = i - 2
                    ev.append(dict(kind='guard', i=i, dir='UP', g=st[2]))
                if L[i] < st[2]:
                    ev.append(dict(kind='dead', i=i, dir='UP', n=st[1]))
                    last_dir = 'UP'
                    state = None
                    d = i
                    reset(i)
            else:
                if L[i] < st[3]:
                    st[1] += 1
                    st[3] = L[i]
                    st[4] = i
                    ev.append(dict(kind='new', i=i, dir='DN', n=st[1]))
                if i - 2 > st[5] and all(H[i - 2] > H[t] for t in (i - 4, i - 3, i - 1, i)):
                    st[2] = min(st[2], H[i - 2])
                    st[5] = i - 2
                    ev.append(dict(kind='guard', i=i, dir='DN', g=st[2]))
                if H[i] > st[2]:
                    ev.append(dict(kind='dead', i=i, dir='DN', n=st[1]))
                    last_dir = 'DN'
                    state = None
                    d = i
                    reset(i)
    return ev


def small_waves(ev):
    sw, cur = [], None
    for e in ev:
        if e['kind'] == 'born':
            cur = dict(dir=e['dir'], b=e['i'], d=None, guard=e['guard'], n=1, zone=e['zone'], level=e['level'], same=e['same'])
            sw.append(cur)
        elif e['kind'] == 'new' and cur is not None:
            cur['n'] = e['n']
        elif e['kind'] == 'dead' and cur is not None:
            cur['d'] = e['i']
            cur = None
    return sw


def big_run(H, L, SW, policy):
    """大波段从小波段推。每一步的顺序：小波段出生 -> 大波段记新高 -> 过前顶换守护点 -> 大波段死没死 -> 小波段死了记顶。"""
    n = len(H)
    bigs, big, tops, pend, maxtop, k = [], None, [], None, None, -1
    for i in range(n):
        if k + 1 < len(SW) and SW[k + 1]['b'] == i:
            k += 1
            w = SW[k]
            if big is None:
                big = dict(dir=w['dir'], b=i, since=i, guard=w['guard'], cnt=1, nsw=1, by_kill=False,
                           ext=H[i] if w['dir'] == 'UP' else L[i], sw=[k], moves=[], newbars=[], tops=[], cnt0=1)
                tops, pend, maxtop = [], None, None
            elif w['dir'] == big['dir']:
                big['nsw'] += 1
                big['sw'].append(k)
                src = tops[-1] if policy == 'prev' else maxtop
                pend = (src, w['guard']) if src else None
        if big is None:
            continue
        u = big['dir'] == 'UP'
        if i > big['since'] and (H[i] > big['ext'] if u else L[i] < big['ext']):
            big['cnt'] += 1
            big['ext'] = H[i] if u else L[i]
            big['newbars'].append(i)
        if pend is not None and (H[i] > pend[0][1] if u else L[i] < pend[0][1]):
            g = min(L[pend[0][0]:i + 1]) if u else max(H[pend[0][0]:i + 1])
            big['moves'].append(dict(i=i, g=g, top=list(pend[0]), cnt=big['cnt'], is_max=pend[0] is maxtop, same_low=(g == pend[1])))
            big['guard'] = g
            pend = None
        dead = L[i] < big['guard'] if u else H[i] > big['guard']
        if dead:
            big['d'] = i
            bigs.append(big)
            cur = SW[k] if k >= 0 and SW[k]['b'] <= i and (SW[k]['d'] is None or SW[k]['d'] >= i) else None
            if cur is not None and cur['dir'] != big['dir']:
                cu = cur['dir'] == 'UP'
                big = dict(dir=cur['dir'], b=cur['b'], since=i, guard=cur['guard'], cnt=cur['n'], nsw=1, by_kill=True,
                           ext=max(H[cur['b']:i + 1]) if cu else min(L[cur['b']:i + 1]), sw=[k], moves=[], newbars=[], tops=[], cnt0=cur['n'])
                tops, pend, maxtop = [], None, None
            else:
                big = None
        if big is not None and k >= 0 and SW[k]['d'] == i and SW[k]['dir'] == big['dir']:
            bu = big['dir'] == 'UP'
            j = (max if bu else min)(range(SW[k]['b'], i + 1), key=lambda t: H[t] if bu else L[t])
            top = (j, H[j] if bu else L[j], SW[k]['n'])
            is_max = (H[j] >= big['ext'] if bu else L[j] <= big['ext'])
            tops.append(top)
            big['tops'].append(dict(j=j, price=top[1], n=top[2], is_max=is_max))
            if is_max:
                maxtop = top
    return bigs, big


def q(xs, f):
    return xs[min(int(f * len(xs)), len(xs) - 1)]


def report(allb, alls):
    bigs = [w for s in allb for w in allb[s]]
    ns = sorted(w['cnt'] for w in bigs)
    lens = sorted(w['d'] - w['b'] + 1 for w in bigs)
    c = collections.Counter(min(w['nsw'], 4) for w in bigs)
    moves = [m for w in bigs for m in w['moves']]
    tops = [t for w in bigs for t in w['tops']]
    nm = sum(m['is_max'] for m in moves)
    low_diff = sum(not m['same_low'] for m in moves)
    print('大波段 %d 条（涨 %d 跌 %d）；只数 中位 %s，P75 %s，P90 %s，最大 %s；活多少根 中位 %s，P90 %s' % (
        len(bigs), sum(w['dir'] == 'UP' for w in bigs), sum(w['dir'] == 'DN' for w in bigs),
        statistics.median(ns), q(ns, .75), q(ns, .9), ns[-1], statistics.median(lens), q(lens, .9)))
    print('  分档 1 / 2-3 / 4-6 / 7-14 / 15+ 只:', [round(sum(1 for n in ns if lo <= n <= hi) / len(ns), 3) for lo, hi in ((1, 1), (2, 3), (4, 6), (7, 14), (15, 10 ** 9))])
    print('  一条大波段里同向小波段 1/2/3/4+:', [round(c.get(k, 0) / len(bigs), 3) for k in (1, 2, 3, 4)])
    print('  守护点换过的大波段 %.1f%%；共换 %d 次：前顶就是大波段最高价的 %d 次，前顶更低（没过顶就死的小波段）%d 次' % (
        100 * sum(bool(w['moves']) for w in bigs) / len(bigs), len(moves), nm, len(moves) - nm))
    own_ok = extra = first_ok = later_ok = 0
    first_n = later_n = 0
    for w in bigs:
        for m in w['moves']:
            if not m['is_max']:
                continue
            j = m['top'][0]
            read = w['cnt0'] + sum(1 for b in w['newbars'] if b <= j)   # 大波段自己在前顶那根的读数
            own_ok += (read + 1 == m['cnt'])
            extra += (read + 1 != m['cnt'])
            t = next(t for t, x in enumerate(w['tops']) if x['j'] == j)
            if t == 0:
                first_n += 1
                first_ok += (m['top'][2] + 1 == m['cnt'])
            else:
                later_n += 1
                later_ok += (m['top'][2] + 1 == m['cnt'])
    print('  计数一「过顶那根的大波段读数 = 大波段自己在前顶那根的读数 + 1」：%d 次里对上 %d 次；另 %d 次前顶到过顶之间大波段自己已经另记过' % (nm, own_ok, extra))
    print('  计数二「前顶那条小波段的读数 + 1」：前顶是第一条小波段的 %d 次里对上 %d 次；是后面几条的 %d 次里只对上 %d 次' % (
        first_n, first_ok, later_n, later_ok))
    lowtop = sum(not t['is_max'] for t in tops)
    print('  小波段的顶 %d 个，其中没过当时大波段最高价的 %d 个（%.1f%%）；有这样小波段的大波段 %d 条' % (
        len(tops), lowtop, 100 * lowtop / len(tops), sum(any(not t['is_max'] for t in w['tops']) for w in bigs)))
    print('  位置「换到的低点 = 新生小波段的出生守护点」：%d 次里重合 %d 次（回调只走一段）；不重合 %d 次（回调走了好几段，中间有别的小波段生死）' % (
        len(moves), len(moves) - low_diff, low_diff))
    total = vshape = 0
    for s in allb:
        SW = alls[s]['sw']
        for w in allb[s]:
            for i in w['newbars']:
                total += 1
                if not any(x['dir'] == w['dir'] and x['b'] <= i and (x['d'] is None or i <= x['d']) for x in SW):
                    vshape += 1
    print('  直线走势「大波段记的每一只都落在一条同向小波段里」：%d 只里 %d 只不在（%.1f%%：每根都创新极值、不停一下，盘整立不起来，小波段没出生）' % (
        total, vshape, 100 * vshape / total))


res = {}
for policy in ('prev', 'max'):
    allb, alls = {}, {}
    for s in rows:
        H = [float(r['high']) for r in rows[s]]
        L = [float(r['low']) for r in rows[s]]
        ev = small_run(rows[s])
        SW = small_waves(ev)
        bigs, alive = big_run(H, L, SW, policy)
        for w in bigs:
            w['sym'] = s
        allb[s] = bigs
        alls[s] = dict(ev=ev, sw=SW)
    res[policy] = (allb, alls)
    print('== 读法 %s' % {'prev': 'prev  前顶 = 上一条同向小波段的顶（八步字面）', 'max': 'max   前顶 = 大波段最高价那个顶'}[policy])
    report(allb, alls)

# 与 nested.py 写法 C 交叉核对
ref = json.load(open(os.path.join(ROOT, 'data', 'processed', 'nested', 'nested.json'), encoding='utf-8'))['C']['big']
mis = 0
for s in res['prev'][0]:
    a = [(w['dir'], w['b'], w['d'], w['cnt'], w['nsw'], w['by_kill'], [[m['i'], m['g']] for m in w['moves']]) for w in res['prev'][0][s]]
    b = [(w['dir'], w['b'], w['d'], w['cnt'], w['nsw'], w['by_kill'], w.get('trace', [])) for w in ref[s]]
    mis += a != b
print('== 与 nested.py 写法 C 逐条核对（方向、出生、死亡、只数、小波段数、守护点台阶）：%d 只标的不一致' % mis)

# 两种读法差在哪
A, B = res['prev'][0], res['max'][0]
same = later = guard_only = only_prev = only_max = 0
for s in A:
    ka = {(w['dir'], w['b']): w for w in A[s]}
    kb = {(w['dir'], w['b']): w for w in B[s]}
    for key, wa in ka.items():
        wb = kb.get(key)
        if wb is None:
            only_prev += 1
        elif wb['d'] != wa['d']:
            later += 1
        elif wb['guard'] != wa['guard']:
            guard_only += 1
        else:
            same += 1
    only_max += len(set(kb) - set(ka))
print('== 两种读法：同生同死 %d 条；读法 prev 更早死 %d 条；同一天死但最后守护点不同 %d 条；只在 prev 里有 %d 条，只在 max 里有 %d 条' % (
    same, later, guard_only, only_prev, only_max))


def small_cnt_at(ev, i):
    n = None
    for e in ev:
        if e['i'] > i:
            break
        if e['kind'] == 'born':
            n = 1
        elif e['kind'] == 'new':
            n = e['n']
    return n


def pick(dirn, gap):
    cand = []
    allb, alls = res['prev']
    for s in allb:
        for w in allb[s]:
            if w['dir'] != dirn or w['by_kill'] or w['nsw'] < 3 or not (80 <= w['d'] - w['b'] + 1 <= 240):
                continue
            if len(w['moves']) != w['nsw'] - 1 or any(not m['is_max'] for m in w['moves']):
                continue
            if any(x['dir'] != dirn for x in [alls[s]['sw'][k] for k in w['sw']]):
                continue
            s2 = alls[s]['sw'][w['sw'][1]]
            if w['moves'][0]['i'] - s2['b'] < 3 or s2['b'] - alls[s]['sw'][w['sw'][0]]['d'] < gap:
                continue
            if not (w['moves'][0]['same_low'] and w['moves'][0]['cnt'] == w['moves'][0]['top'][2] + 1):
                continue
            cand.append(w)
    med = statistics.median(w['d'] - w['b'] + 1 for w in cand) if cand else None
    cand.sort(key=lambda w: (w['nsw'] != 3, abs((w['d'] - w['b'] + 1) - (med or 0))))
    return cand, med


def draw(w, tag):
    s = w['sym']
    bars = rows[s]
    n = len(bars)
    ev, SW = res['prev'][1][s]['ev'], res['prev'][1][s]['sw']
    bi, di = w['b'], w['d']
    a = max(0, bi - 10)
    b = min(n, di + 12)
    m = b - a
    W, Hh = 680, 330
    PW = min(6.0, 620.0 / m)
    X0 = (W - PW * m) / 2
    lo = min(float(r['low']) for r in bars[a:b])
    hi = max(float(r['high']) for r in bars[a:b])
    pad = (hi - lo) * 0.16
    lo, hi = lo - pad, hi + pad
    u = w['dir'] == 'UP'
    PRI, TER = 'var(--color-text-primary)', 'var(--color-text-tertiary)'

    def X(i):
        return X0 + PW * (i - a) + PW / 2

    def Y(p):
        return 40 + (Hh - 76) * (hi - p) / (hi - lo)

    CH = Hh
    CAP = 104                                                  # 底部说明四行
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" font-family="var(--font-sans)" width="100%%">' % (W, Hh + CAP)]
    o.append('<title>%s 大波段从小波段推</title><desc>红号绿号是小波段的新高第几只，顶上蓝号是大波段的新高第几只，细点线是小波段守护点，蓝虚线是大波段守护点，带圈数字是八步。</desc>' % s)
    wu, wd, body = [], [], []
    for i in range(a, b):
        r = bars[i]
        op, h, l, c = (float(r[k]) for k in ('open', 'high', 'low', 'close'))
        (wu if c >= op else wd).append('M%.1f %.1fV%.1f' % (X(i), Y(h), Y(l)))
        y1, y2 = Y(max(op, c)), Y(min(op, c))
        body.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (
            X(i) - max(PW * .36, 1), y1, max(PW * .72, 2), max(y2 - y1, 1), '#E24B4A' if c >= op else '#4A8A2A'))
    o.append('<path d="%s" stroke="#E24B4A" stroke-width="1"/>' % ''.join(wu))
    o.append('<path d="%s" stroke="#4A8A2A" stroke-width="1"/>' % ''.join(wd))
    o.extend(body)
    # 小波段守护点：台阶
    cur = None
    steps = []
    for e in ev:
        if e['kind'] == 'born':
            cur = dict(dir=e['dir'], pts=[(e['i'], e['guard'])])
            steps.append(cur)
        elif cur is not None and e['kind'] == 'guard':
            cur['pts'].append((e['i'], e['g']))
        elif cur is not None and e['kind'] == 'dead':
            cur['pts'].append((e['i'] + 1, None))
            cur = None
    for st in steps:
        pts = [(i, g) for i, g in st['pts'] if i >= a and i <= b]
        if len(pts) < 2:
            continue
        path = ''.join('M%.1f %.1fH%.1f' % (X(i0), Y(g), X(i1)) for (i0, g), (i1, _) in zip(pts, pts[1:]))
        o.append('<path d="%s" stroke="%s" stroke-width="1.2" stroke-dasharray="2 3" fill="none"/>' % (path, '#F06565' if st['dir'] == 'UP' else '#8FCB5A'))
    # 大波段守护点：台阶
    pts = [(bi, SW[w['sw'][0]]['guard'])] + [(x['i'], x['g']) for x in w['moves']] + [(di + 1, None)]
    path = ''.join('M%.1f %.1fH%.1f' % (X(i0), Y(g), X(i1)) for (i0, g), (i1, _) in zip(pts, pts[1:]))
    o.append('<path d="%s" stroke="#4A9BEF" stroke-width="2.2" stroke-dasharray="7 4" fill="none"/>' % path)
    # 小波段的号和叉
    lastx = -99
    for e in ev:
        if not (a <= e['i'] < b) or e['kind'] == 'guard':
            continue
        r = bars[e['i']]
        sup = e['dir'] == 'UP'
        col = '#F06565' if sup else '#8FCB5A'
        ty = (lambda: Y(float(r['high'])) - 5) if sup else (lambda: Y(float(r['low'])) + 14)
        if e['kind'] == 'born':
            lastx = -99
            o.append('<text x="%.1f" y="%.1f" font-size="12" font-weight="500" fill="%s" text-anchor="middle">1</text>' % (X(e['i']), ty(), col))
            lastx = X(e['i'])
        elif e['kind'] == 'new':
            if X(e['i']) - lastx < 28:
                continue
            lastx = X(e['i'])
            o.append('<text x="%.1f" y="%.1f" font-size="11" fill="%s" text-anchor="middle">%d</text>' % (X(e['i']), ty(), col, e['n']))
        elif e['kind'] == 'dead':
            o.append('<path d="M%.1f %.1fm-3 -3l6 6m0 -6l-6 6" stroke="%s" stroke-width="1.4"/>' % (
                X(e['i']), Y(float(r['high'])) - 16 if sup else Y(float(r['low'])) + 24, col))
    # 大波段的号
    ext, cnt, lastx = None, 0, -99
    for i in range(bi, di + 1):
        p = float(bars[i]['high'] if u else bars[i]['low'])
        if ext is None or (p > ext if u else p < ext):
            ext = p
            cnt += 1
            if X(i) - lastx < 16 and i not in (bi, di):
                continue
            if i == bi or i == di or cnt % 5 == 0 or X(i) - lastx >= 44:
                o.append('<text x="%.1f" y="22" font-size="12" font-weight="%s" fill="#4A9BEF" text-anchor="middle">%d</text>' % (
                    X(i), '500' if cnt == 1 else '400', cnt))
                lastx = X(i)
    o.append('<path d="M%.1f %.1fm-4 -4l8 8m0 -8l-8 8" stroke="#4A9BEF" stroke-width="1.8"/>' % (X(di), Y(w['guard'])))

    # 八步的标记（只标第一轮）
    def lab(i, p, txt, dy, anchor='middle', dx=0):
        o.append('<text x="%.1f" y="%.1f" font-size="13" font-weight="500" fill="%s" text-anchor="%s">%s</text>' % (X(i) + dx, Y(p) + dy, PRI, anchor, txt))

    s1, s2, m0 = SW[w['sw'][0]], SW[w['sw'][1]], w['moves'][0]
    j1 = m0['top'][0]
    away = -30 if u else 30      # 远离守护点那一侧
    near = 26 if u else -20      # 靠近守护点那一侧
    ext_p = lambda i: float(bars[i]['high'] if u else bars[i]['low'])
    gte_p = lambda i: float(bars[i]['low'] if u else bars[i]['high'])
    lab(j1, ext_p(j1), '①', away)
    lab(s1['d'], gte_p(s1['d']), '②', 14 if u else -8)
    lab(s2['zone'][0], gte_p(s2['zone'][0]), '④', near)
    o.append('<path d="M%.1f %.1fH%.1f" stroke="%s" stroke-width="1"/>' % (X(s2['zone'][0]), Y(s2['level']), X(s2['b']), PRI))
    lab(s2['b'], s2['level'], '⑤', -5 if u else 13, anchor='end', dx=-4)
    lab(s2['b'], gte_p(s2['b']), '⑥', 14 if u else -8)
    lab(m0['i'], ext_p(m0['i']), '⑧', away)

    lastx = -99
    for i in range(a, b):
        dd = bars[i]['date']
        if i == a or (dd[8:] == '01' and dd[5:7] in ('01', '04', '07', '10')):
            if X(i) - lastx < 60:
                continue
            lastx = X(i)
            o.append('<text x="%.1f" y="%d" font-size="11" fill="%s" text-anchor="middle">%s</text>' % (X(i), Hh + 14, TER, dd if i == a else dd[:7]))
    brk = '上破' if u else '下破'
    hi_lo = '高' if u else '低'
    caps = [
        PRI, '① 小波段走到顶：第 %d 只　② 它的守护点被击穿　④ 回调%s点 %.2f　⑤ 门禁 %.2f' % (s1['n'], hi_lo, gte_p(s2['zone'][0]), s2['level']),
        PRI, '⑥ %s门禁：新生小波段记第 1 只　⑧ 第 %d 只过前%s：守护点换到④，大波段记 %d+1=%d' % (
            brk, small_cnt_at(ev, m0['i']), hi_lo, m0['top'][2], m0['cnt']),
        TER, '%s　%s大波段 %s ～ %s，%d 根日线；同向小波段 %d 条' % (s, '上涨' if u else '下跌', bars[bi]['date'], bars[di]['date'], di - bi + 1, w['nsw']),
        TER, '红号绿号是小波段的本子，归 1 过 %d 次；蓝号是大波段的本子，一路数到 %d。点线虚线是两边的守护点' % (w['nsw'], w['cnt']),
    ]
    for x in range(4):
        o.append('<text x="340" y="%d" font-size="12" fill="%s" text-anchor="middle">%s</text>' % (Hh + 40 + 20 * x, caps[2 * x], caps[2 * x + 1]))
    o.append('</svg>')
    svg = ''.join(o)
    open(os.path.join(FIG, 'big8_%s.svg' % tag), 'w', encoding='utf-8').write(svg)
    return s1, s2, m0


for dirn, tag in (('UP', 'up'), ('DN', 'dn')):
    for gap in (10, 8, 6, 5, 4, 3):
        cand, med = pick(dirn, gap)
        if cand:
            break
    w = cand[0]
    s1, s2, m0 = draw(w, tag)
    bars = rows[w['sym']]
    print('-- 举例 %s %s：回调至少 %d 根这一档有候选 %d 条，长度中位 %s，挑了 %s ～ %s' % (tag, dirn, gap, len(cand), med, bars[w['b']]['date'], bars[w['d']]['date']))
    for x, k in enumerate(w['sw'], 1):
        xw = res['prev'][1][w['sym']]['sw'][k]
        print('   小波段 %d %s %s ～ %s，%d 只' % (x, xw['dir'], bars[xw['b']]['date'], bars[xw['d']]['date'], xw['n']))
    for z in w['moves']:
        print('   ⑧ %s 守护点换到 %.2f；前顶是第 %d 只，大波段当时记 %d' % (bars[z['i']]['date'], z['g'], z['top'][2], z['cnt']))

json.dump({p: dict(big=res[p][0], small={s: dict(sw=res[p][1][s]['sw']) for s in res[p][1]}) for p in res},
          open(os.path.join(OUT, 'big8.json'), 'w'))
