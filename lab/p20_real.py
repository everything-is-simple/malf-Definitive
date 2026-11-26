# -*- coding: utf-8 -*-
"""P20 盘整认法在真实 A 股日线上的实跑（只用 bars.csv 的 high/low，不用分形，不依赖 P1）。

链是顺序的：活着 -> 守护点被击穿（过渡） -> 下一条出生。过渡里两张表同时跑，各记各的，谁先破谁出生。
bars.csv 来自 B:/arc-pinbar/data/db/arc-pinbar.db 的 bar 表（后复权价，去掉停牌根）。
"""
import csv, collections, statistics, os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作台根目录
BASE = os.path.join(ROOT, 'data', 'raw')                   # 只读：bars.csv
OUT = os.path.join(ROOT, 'data', 'processed', 'p20_real')  # 脚本产物，可重跑
os.makedirs(OUT, exist_ok=True)

rows = collections.defaultdict(list)
for x in csv.DictReader(open(os.path.join(BASE, 'bars.csv'), encoding='utf-8')):
    rows[x['symbol']].append((x['date'], float(x['open']), float(x['high']), float(x['low']), float(x['close'])))
for k in rows:
    rows[k].sort(key=lambda t: t[0])


def run(bars):
    """返回事件列表。每条事件：kind = born / new / dead。"""
    n = len(bars)
    H = [b[2] for b in bars]
    L = [b[3] for b in bars]
    ev = []
    state = None
    d = 0
    up = {'low': 0, 'consol': None, 'voids': 0, 'zone': None}
    dn = {'high': 0, 'consol': None, 'voids': 0, 'zone': None}
    last_dir = None
    last_ext = None
    both = 0

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
            up_break = up['consol'] is not None and H[i] > up['consol']
            dn_break = dn['consol'] is not None and L[i] < dn['consol']
            if up_break and dn_break:
                both += 1
            if up_break:
                state = ['UP', 1, L[up['low']], H[i]]
                ev.append(dict(kind='born', i=i, dir='UP', guard=L[up['low']], zone=up['zone'],
                               level=up['consol'], voids=up['voids'], trans=i - d,
                               below_prev=(last_dir == 'UP' and H[i] <= last_ext),
                               same=(last_dir == 'UP')))
            elif dn_break:
                state = ['DN', 1, H[dn['high']], L[i]]
                ev.append(dict(kind='born', i=i, dir='DN', guard=H[dn['high']], zone=dn['zone'],
                               level=dn['consol'], voids=dn['voids'], trans=i - d,
                               below_prev=(last_dir == 'DN' and L[i] >= last_ext),
                               same=(last_dir == 'DN')))
        else:
            st = state
            if st[0] == 'UP':
                if H[i] > st[3]:
                    st[1] += 1
                    st[3] = H[i]
                    ev.append(dict(kind='new', i=i, dir='UP', n=st[1]))
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
                    ev.append(dict(kind='new', i=i, dir='DN', n=st[1]))
                if H[i] > st[2]:
                    ev.append(dict(kind='dead', i=i, dir='DN', n=st[1]))
                    last_dir, last_ext = 'DN', st[3]
                    state = None
                    d = i
                    reset(i)
    return ev, both


res = {}
both_total = 0
for s, bars in rows.items():
    ev, both = run(bars)
    both_total += both
    res[s] = ev

born = [e for s in res for e in res[s] if e['kind'] == 'born']
dead = [e for s in res for e in res[s] if e['kind'] == 'dead']
print('标的', len(res), '出生', len(born), '死亡', len(dead), '过渡里同一根上下都破', both_total)
print('上涨出生', sum(e['dir'] == 'UP' for e in born), '下跌出生', sum(e['dir'] == 'DN' for e in born))
zone_len = [e['zone'][1] - e['zone'][0] + 1 for e in born]
c = collections.Counter(min(x, 5) for x in zone_len)
print('盘整区根数 1..5+:', [c.get(k, 0) for k in range(1, 6)], '占比', [round(c.get(k, 0) / len(born), 3) for k in range(1, 6)])
trans = [e['trans'] for e in born]
c2 = collections.Counter(min(x, 6) for x in trans)
print('过渡长度 1..6+:', [c2.get(k, 0) for k in range(1, 7)], '占比', [round(c2.get(k, 0) / len(born), 3) for k in range(1, 7)])
print('作废重来 0/1/2/3+:', [sum(1 for e in born if e['voids'] == k) for k in range(3)] + [sum(1 for e in born if e['voids'] >= 3)])
same = [e for e in born if e['same']]
first = sum(1 for s in res if res[s] and res[s][0]['kind'] == 'born')
print('同向新生', len(same), '反向新生', len(born) - len(same) - first, '数据起点的第一条', first)
print('同向新生里出生那根没过前顶的占比', round(sum(1 for e in same if e['below_prev']) / len(same), 3))
ns = [e['n'] for e in dead]
print('波段总只数 中位数', statistics.median(ns), '均值', round(statistics.mean(ns), 2),
      '1 只就死的占比', round(sum(1 for x in ns if x == 1) / len(ns), 3),
      '>=10 只的占比', round(sum(1 for x in ns if x >= 10) / len(ns), 3))
per_sym = [sum(1 for e in res[s] if e['kind'] == 'born') for s in res]
print('每只标的 5 年的波段数 中位数', statistics.median(per_sym), '最多', max(per_sym))
json.dump(res, open(os.path.join(OUT, 'events.json'), 'w'))
