# -*- coding: utf-8 -*-
"""大小波段嵌套实跑。两种写法对比：
A 现稿：小波段的守护点 = 盘整低点，出生后不动。
B 试跑：小波段的守护点出生时 = 盘整低点，之后每出一只新高，上移到"相邻两只新高之间的最低点"（镜像：新低）。
   大波段的守护点 = 相邻两个同向小波段顶之间的最低点，出现高过前顶的日线那根换过去。两种写法里丙不变。
"""
import csv, json, os, sys, collections, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作台根目录
BASE = os.path.join(ROOT, 'data', 'raw')                   # 只读：bars.csv
OUT = os.path.join(ROOT, 'data', 'processed', 'nested')    # 脚本产物，可重跑
os.makedirs(OUT, exist_ok=True)
rows = collections.defaultdict(list)
for x in csv.DictReader(open(os.path.join(BASE, 'bars.csv'), encoding='utf-8')):
    rows[x['symbol']].append(x)
for k in rows:
    rows[k].sort(key=lambda r: r['date'])


def small_run(bars, mode):
    H = [float(r['high']) for r in bars]
    L = [float(r['low']) for r in bars]
    n = len(bars)
    ev = []
    state = None
    d = 0
    up = {'low': 0, 'consol': None, 'voids': 0, 'zone': None}
    dn = {'high': 0, 'consol': None, 'voids': 0, 'zone': None}
    last_dir = last_ext = None

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
                ev.append(dict(kind='born', i=i, dir='UP', guard=state[2], zone=up['zone'], level=up['consol'], voids=up['voids'], trans=i - d,
                                below_prev=(last_dir == 'UP' and H[i] <= last_ext), same=(last_dir == 'UP')))
            elif db:
                state = ['DN', 1, H[dn['high']], L[i], i, i]
                ev.append(dict(kind='born', i=i, dir='DN', guard=state[2], zone=dn['zone'], level=dn['consol'], voids=dn['voids'], trans=i - d,
                                below_prev=(last_dir == 'DN' and L[i] >= last_ext), same=(last_dir == 'DN')))
        else:
            st = state
            if st[0] == 'UP':
                if H[i] > st[3]:
                    st[1] += 1
                    st[3] = H[i]
                    if mode == 'B' and i - st[4] >= 2:
                        st[2] = max(st[2], min(L[st[4] + 1:i]))
                    st[4] = i
                    ev.append(dict(kind='new', i=i, dir='UP', n=st[1]))
                if mode == 'C' and i - 2 > st[5] and all(L[i - 2] < L[t] for t in (i - 4, i - 3, i - 1, i)):
                    st[2] = max(st[2], L[i - 2])
                    st[5] = i - 2
                if L[i] < st[2]:
                    ev.append(dict(kind='dead', i=i, dir='UP', n=st[1]))
                    last_dir, last_ext = 'UP', st[3]
                    state = None
                    d = i
                    reset(i)
            else:
                if L[i] < st[3]:
                    st[1] += 1
                    st[3] = L[i]
                    if mode == 'B' and i - st[4] >= 2:
                        st[2] = min(st[2], max(H[st[4] + 1:i]))
                    st[4] = i
                    ev.append(dict(kind='new', i=i, dir='DN', n=st[1]))
                if mode == 'C' and i - 2 > st[5] and all(H[i - 2] > H[t] for t in (i - 4, i - 3, i - 1, i)):
                    st[2] = min(st[2], H[i - 2])
                    st[5] = i - 2
                if H[i] > st[2]:
                    ev.append(dict(kind='dead', i=i, dir='DN', n=st[1]))
                    last_dir, last_ext = 'DN', st[3]
                    state = None
                    d = i
                    reset(i)
    return ev


def small_waves(s, ev):
    sw, cur = [], None
    for e in ev:
        if e['kind'] == 'born':
            cur = dict(dir=e['dir'], b=e['i'], d=None, guard=e['guard'], n=1, zone=e['zone'], same=e['same'])
            sw.append(cur)
        elif e['kind'] == 'new' and cur is not None:
            cur['n'] = e['n']
        elif e['kind'] == 'dead' and cur is not None:
            cur['d'] = e['i']
            cur = None
    return sw


def big_run(s, ev, SW):
    bars = rows[s]
    H = [float(r['high']) for r in bars]
    L = [float(r['low']) for r in bars]
    bigs, big, tops, pending, k = [], None, [], None, -1
    for i in range(len(bars)):
        if k + 1 < len(SW) and SW[k + 1]['b'] == i:
            k += 1
            if big is None:
                big = dict(dir=SW[k]['dir'], b=i, since=i, guard=SW[k]['guard'], cnt=1, nsw=1, steps=0, by_kill=False,
                            ext=(H[i] if SW[k]['dir'] == 'UP' else L[i]))
                tops, pending = [], None
            elif SW[k]['dir'] == big['dir']:
                big['nsw'] += 1
                if tops:
                    pending = tops[-1]
        if big is None:
            continue
        if big['dir'] == 'UP':
            if i > big['since'] and H[i] > big['ext']:
                big['cnt'] += 1
                big['ext'] = H[i]
            if pending is not None and H[i] > pending[1]:
                big['guard'] = min(L[pending[0]:i + 1])
                big['steps'] += 1
                big.setdefault('trace', []).append((i, big['guard']))
                pending = None
            dead = L[i] < big['guard']
        else:
            if i > big['since'] and L[i] < big['ext']:
                big['cnt'] += 1
                big['ext'] = L[i]
            if pending is not None and L[i] < pending[1]:
                big['guard'] = max(H[pending[0]:i + 1])
                big['steps'] += 1
                big.setdefault('trace', []).append((i, big['guard']))
                pending = None
            dead = H[i] > big['guard']
        if dead:
            big['d'] = i
            bigs.append(big)
            cur = SW[k] if k >= 0 and SW[k]['b'] <= i and (SW[k]['d'] is None or SW[k]['d'] >= i) else None
            if cur is not None and cur['dir'] != big['dir']:
                big = dict(dir=cur['dir'], b=cur['b'], since=i, guard=cur['guard'], cnt=cur['n'], nsw=1, steps=0, by_kill=True,
                             ext=(max(H[cur['b']:i + 1]) if cur['dir'] == 'UP' else min(L[cur['b']:i + 1])))
                tops, pending = [], None
            else:
                big, tops, pending = None, [], None
        if k >= 0 and SW[k]['d'] == i and big is not None and SW[k]['dir'] == big['dir']:
            if big['dir'] == 'UP':
                j = max(range(SW[k]['b'], i + 1), key=lambda t: H[t])
                tops.append((j, H[j]))
            else:
                j = min(range(SW[k]['b'], i + 1), key=lambda t: L[t])
                tops.append((j, L[j]))
    return bigs, big


def buckets(ns, lens):
    out = []
    for lo_, hi_ in ((1, 1), (2, 3), (4, 6), (7, 14), (15, 10 ** 9)):
        sel = [n for n in ns if lo_ <= n <= hi_]
        out.append('%d-%d 只 %.1f%%' % (lo_, hi_, 100 * len(sel) / len(ns)))
    return '；'.join(out)


sys.stdout.reconfigure(encoding='utf-8')
store = {}
for mode in ('A', 'B', 'C'):
    tag = mode
    allb, alls, ns, lens = {}, {}, [], []
    for s in rows:
        ev = small_run(rows[s], mode)
        SW = small_waves(s, ev)
        bigs, alive = big_run(s, ev, SW)
        for b in bigs:
            b['sym'] = s
        allb[s] = bigs
        alls[s] = dict(ev=ev, sw=SW)
        ns += [b['cnt'] for b in bigs]
        lens += [b['d'] - b['b'] + 1 for b in bigs]
    store[tag] = dict(big=allb, small=alls)
    ns.sort()
    c = collections.Counter(min(b['nsw'], 4) for s in allb for b in allb[s])
    print('== 写法 %s' % tag, {'A': '现稿：守护点不动', 'B': '每出一只新高就上移到两只新高之间的最低点', 'C': 'v1.4：新的低点被确认（k=2 分形）才上移'}[tag])
    print('大波段 %d 条；只数中位 %s，P75 %s，P90 %s，P99 %s，最大 %s；活多少根 中位 %s，P90 %s' % (
        len(ns), statistics.median(ns), ns[int(.75 * len(ns))], ns[int(.9 * len(ns))], ns[int(.99 * len(ns))], ns[-1],
        statistics.median(lens), sorted(lens)[int(.9 * len(lens))]))
    print('  分档', buckets(ns, lens))
    sns = sorted(e['n'] for s in alls for e in alls[s]['ev'] if e['kind'] == 'dead')
    print('  同一份数据上的小波段 %d 条；只数 P10/P25/P50/P75/P90/P99 %s；' % (len(sns), [sns[int(q * len(sns))] for q in (.1, .25, .5, .75, .9, .99)]))
    print('  小波段分档', buckets(sns, sns))
    print('  一条大波段里有几条同向小波段 1/2/3/4+:', [round(c.get(k, 0) / len(ns), 3) for k in (1, 2, 3, 4)])
    print('  守护点抬过的大波段 %.1f%%' % (100 * sum(b['steps'] > 0 for s in allb for b in allb[s]) / len(ns)))
    big3 = [b for s in allb for b in allb[s] if b['nsw'] >= 3]
    if big3:
        print('  3 条以上同向小波段的大波段 %d 条：只数中位 %s，活多少根 中位 %s' % (
            len(big3), statistics.median(b['cnt'] for b in big3), statistics.median(b['d'] - b['b'] + 1 for b in big3)))
json.dump({t: dict(big=store[t]['big'], small=store[t]['small']) for t in store}, open(os.path.join(OUT, 'nested.json'), 'w'))
