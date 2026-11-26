# -*- coding: utf-8 -*-
"""P20 盘整认法 + 小波段守护点上移（写法 C）在真实 A 股日线上的实跑。只用 bars.csv 的 high/low。

与 p20_real.py 的差别只有一处：小波段出生之后，守护点换到最新确认的 HL / LH（严格分形 k=2）。
每根日线的顺序（O2）：记新高 -> 确认 k=2 分形并上移守护点 -> 判击穿。
输出与 p20_real.py 同一张表，给文档 4.6.7 用。
"""
import csv, collections, statistics, os, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作台根目录
BASE = os.path.join(ROOT, 'data', 'raw')                        # 只读：bars.csv
OUT = os.path.join(ROOT, 'data', 'processed', 'p20_real_c')     # 脚本产物，可重跑
os.makedirs(OUT, exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')

rows = collections.defaultdict(list)
for x in csv.DictReader(open(os.path.join(BASE, 'bars.csv'), encoding='utf-8')):
    rows[x['symbol']].append((x['date'], float(x['open']), float(x['high']), float(x['low']), float(x['close'])))
for k in rows:
    rows[k].sort(key=lambda t: t[0])


def run(bars):
    """返回事件列表。每条事件：kind = born / new / guard / dead。guard 事件记守护点哪一根换的、换到哪。"""
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
                state = ['UP', 1, L[up['low']], H[i], i, i]
                ev.append(dict(kind='born', i=i, dir='UP', guard=state[2], zone=up['zone'],
                               level=up['consol'], voids=up['voids'], trans=i - d,
                               below_prev=(last_dir == 'UP' and H[i] <= last_ext),
                               same=(last_dir == 'UP')))
            elif dn_break:
                state = ['DN', 1, H[dn['high']], L[i], i, i]
                ev.append(dict(kind='born', i=i, dir='DN', guard=state[2], zone=dn['zone'],
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
                if i - 2 > st[5] and all(L[i - 2] < L[t] for t in (i - 4, i - 3, i - 1, i)):
                    st[2] = max(st[2], L[i - 2])
                    st[5] = i - 2
                    ev.append(dict(kind='guard', i=i, dir='UP', g=st[2], at=i - 2))
                if L[i] < st[2]:
                    ev.append(dict(kind='dead', i=i, dir='UP', n=st[1], guard=st[2]))
                    last_dir, last_ext = 'UP', st[3]
                    state = None
                    d = i
                    reset(i)
            else:
                if L[i] < st[3]:
                    st[1] += 1
                    st[3] = L[i]
                    ev.append(dict(kind='new', i=i, dir='DN', n=st[1]))
                if i - 2 > st[5] and all(H[i - 2] > H[t] for t in (i - 4, i - 3, i - 1, i)):
                    st[2] = min(st[2], H[i - 2])
                    st[5] = i - 2
                    ev.append(dict(kind='guard', i=i, dir='DN', g=st[2], at=i - 2))
                if H[i] > st[2]:
                    ev.append(dict(kind='dead', i=i, dir='DN', n=st[1], guard=st[2]))
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
print('盘整区 2/3/4/5+ 根 占比', [round(sum(1 for x in zone_len if lo <= x <= hi) / len(zone_len), 3) for lo, hi in ((2, 2), (3, 3), (4, 4), (5, 10 ** 9))])
trans = [e['trans'] for e in born]
print('过渡 2/3/4/5/6+ 根 占比', [round(sum(1 for x in trans if lo <= x <= hi) / len(trans), 3) for lo, hi in ((2, 2), (3, 3), (4, 4), (5, 5), (6, 10 ** 9))])
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
# 守护点上移（写法 C 多出来的）
moves = sum(1 for s in res for e in res[s] if e['kind'] == 'guard')
moved = sum(1 for e in dead if any(g['kind'] == 'guard' for s in [None] for g in []))
per_wave = []
for s in res:
    k = 0
    for e in res[s]:
        if e['kind'] == 'born':
            k = 0
        elif e['kind'] == 'guard':
            k += 1
        elif e['kind'] == 'dead':
            per_wave.append(k)
print('小波段守护点上移：共 %d 次；上移过的小波段 %d 条（%.1f%%），上移 1/2/3+ 次的占比 %s' % (
    moves, sum(1 for k in per_wave if k), 100 * sum(1 for k in per_wave if k) / len(per_wave),
    [round(sum(1 for k in per_wave if k == t) / len(per_wave), 3) for t in (1, 2)] + [round(sum(1 for k in per_wave if k >= 3) / len(per_wave), 3)]))
json.dump(res, open(os.path.join(OUT, 'events.json'), 'w'))

if len(sys.argv) > 1 and sys.argv[1] == 'peek':
    s, b0, b1 = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    print('-- 小波段事件', s)
    for e in res[s]:
        if b0 <= e['i'] <= b1:
            print('  ', e)
