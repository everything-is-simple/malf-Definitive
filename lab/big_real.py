# -*- coding: utf-8 -*-
"""大波段（丙）在真实 A 股日线上的首跑。输入是小波段实跑结果 events.json。

丙（现稿两条细则占位）：
- 大波段同样数日线：每根刷新大波段自己最高价（最低价）的日线记一只。
- 小波段的顶，等它的守护点被击穿才算完。
- 大波段的守护点 = 相邻两个同向小波段顶之间的最低点，出现高过前顶的日线那根换过去。下跌镜像。
- 大波段从一条同向小波段出生那根起算，记第 1 只，守护点 = 这条小波段的守护点。
"""
import csv, json, os, sys, collections, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作台根目录
BASE = os.path.join(ROOT, 'data', 'raw')                   # 只读：bars.csv
OUT = os.path.join(ROOT, 'data', 'processed', 'p20_real')  # 输入：p20_real.py 的结果
BIG = os.path.join(ROOT, 'data', 'processed', 'big')       # 脚本产物，可重跑
os.makedirs(BIG, exist_ok=True)
rows = collections.defaultdict(list)
for x in csv.DictReader(open(os.path.join(BASE, 'bars.csv'), encoding='utf-8')):
    rows[x['symbol']].append(x)
for k in rows:
    rows[k].sort(key=lambda r: r['date'])
res = json.load(open(os.path.join(OUT, 'events.json'), encoding='utf-8'))


def small_waves(s):
    sw, cur = [], None
    for e in res[s]:
        if e['kind'] == 'born':
            cur = dict(dir=e['dir'], b=e['i'], d=None, guard=e['guard'], cnt=1, zone=e['zone'], same=e['same'], hi=rows[s][e['i']])
            sw.append(cur)
        elif e['kind'] == 'new' and cur is not None:
            cur['cnt'] = e['n']
            if cur['dir'] == 'UP':
                cur['hi'] = rows[s][e['i']]
        elif e['kind'] == 'dead' and cur is not None:
            cur['d'] = e['i']
            cur['n'] = e['n']
            cur = None
    return sw


def run(s):
    bars = rows[s]
    n = len(bars)
    H = [float(r['high']) for r in bars]
    L = [float(r['low']) for r in bars]
    SW = small_waves(s)
    bigs = []
    big = None
    tops = []      # 已走完的同向小波段的顶（下标，最高价）
    pending = None  # 等着被上破的前顶
    k = -1         # 当前小波段的序号

    def fresh(sw0, upto):
        d = sw0['dir']
        if d == 'UP':
            hi = max(H[sw0['b']:upto + 1])
            cnt = 1 + sum(1 for j in range(sw0['b'] + 1, upto + 1) if H[j] > max(H[sw0['b']:j + 1][:-1]) and H[j] > max(H[sw0['b']:j]))
            cnt = 1 + sum(1 for j in range(sw0['b'] + 1, upto + 1) if H[j] > max(H[sw0['b']:j]))
        else:
            lo = min(L[sw0['b']:upto + 1])
            cnt = 1 + sum(1 for j in range(sw0['b'] + 1, upto + 1) if L[j] < min(L[sw0['b']:j]))
        return dict(dir=d, b=sw0['b'], guard=sw0['guard'], cnt=cnt, ext=hi if d == 'UP' else lo, nsw=1, by_kill=False, sws=[k])

    for i in range(n):
        if k + 1 < len(SW) and SW[k + 1]['b'] == i:
            k += 1
            sw0 = SW[k]
            if big is None:
                big = fresh(sw0, i)
                tops, pending = [], None
            elif sw0['dir'] == big['dir']:
                big['nsw'] += 1
                big['sws'].append(k)
                if tops:
                    pending = tops[-1]
        if big is None:
            continue
        if big['dir'] == 'UP':
            if i > big['b'] and H[i] > big['ext']:
                big['cnt'] += 1
                big['ext'] = H[i]
                big['last'] = i
            if pending is not None and H[i] > pending[1]:
                j = min(range(pending[0], i + 1), key=lambda t: L[t])
                big['guard'] = L[j]
                big['guard_i'] = j
                big.setdefault('steps', []).append((i, L[j]))
                pending = None
            dead = L[i] < big['guard']
        else:
            if i > big['b'] and L[i] < big['ext']:
                big['cnt'] += 1
                big['ext'] = L[i]
                big['last'] = i
            if pending is not None and L[i] < pending[1]:
                j = max(range(pending[0], i + 1), key=lambda t: H[t])
                big['guard'] = H[j]
                big.setdefault('steps', []).append((i, H[j]))
                pending = None
            dead = H[i] > big['guard']
        if dead:
            big['d'] = i
            bigs.append(big)
            cur = SW[k] if k >= 0 and SW[k]['b'] <= i and (SW[k]['d'] is None or SW[k]['d'] >= i) else None
            if cur is not None and cur['dir'] != big['dir']:
                # 被一条反向小波段杀死的，那条反向小波段算新大波段的第一条
                nb = fresh(cur, i)
                nb['by_kill'] = True
                big = nb
                tops, pending = [], None
            else:
                big = None
                tops, pending = [], None
        # 小波段走完，记顶
        if k >= 0 and SW[k]['d'] == i and big is not None and SW[k]['dir'] == big['dir']:
            if big['dir'] == 'UP':
                j = max(range(SW[k]['b'], i + 1), key=lambda t: H[t])
                tops.append((j, H[j]))
            else:
                j = min(range(SW[k]['b'], i + 1), key=lambda t: L[t])
                tops.append((j, L[j]))
    return SW, bigs, big


allb = {}
for s in rows:
    SW, bigs, alive = run(s)
    allb[s] = dict(sw=SW, bigs=bigs, alive=alive)

done = [b for s in allb for b in allb[s]['bigs']]
ns = sorted(b['cnt'] for b in done)
q = lambda p: ns[min(len(ns) - 1, int(p * len(ns)))]
lens = sorted(b['d'] - b['b'] + 1 for b in done)
print('大波段（有生有死）', len(done), '上涨', sum(b['dir'] == 'UP' for b in done), '下跌', sum(b['dir'] == 'DN' for b in done))
print('总只数分位 P10/P25/P50/P75/P90/P95/P99/最大', [q(p) for p in (.1, .25, .5, .75, .9, .95, .99)], ns[-1])
print('活多少根 中位', statistics.median(lens), 'P90', lens[int(.9 * len(lens))], '最长', lens[-1])
for lo_, hi_, name in ((1, 1, '1 只'), (2, 3, '2-3 只'), (4, 6, '4-6 只'), (7, 14, '7-14 只'), (15, 999, '15 只以上')):
    print('  %s: %.1f%%' % (name, 100 * sum(lo_ <= x <= hi_ for x in ns) / len(ns)))
c = collections.Counter(min(b['nsw'], 4) for b in done)
print('一条大波段里有几条同向小波段 1/2/3/4+:', [round(c.get(k, 0) / len(done), 3) for k in (1, 2, 3, 4)])
print('由杀死前一条的反向小波段起算的', sum(b['by_kill'] for b in done), '占 %.1f%%' % (100 * sum(b['by_kill'] for b in done) / len(done)))
print('守护点一步没抬过的', sum('steps' not in b for b in done), '占 %.1f%%' % (100 * sum('steps' not in b for b in done) / len(done)))
big3 = [b['cnt'] for b in done if b['nsw'] >= 3]
print('大波段和小波段完全重合（只有 1 条同向小波段）的平均只数', round(statistics.mean(b['cnt'] for b in done if b['nsw'] == 1), 2),
      '3 条以上的平均只数', round(statistics.mean(big3), 2) if big3 else '（没有）', '中位', statistics.median(big3) if big3 else '（没有）')
sym_of = {}
for s, d in allb.items():
    for b in d['bigs']:
        sym_of[id(b)] = s
for b in done:
    b['sym'] = sym_of[id(b)]
json.dump({s: dict(bigs=allb[s]['bigs'], sw=allb[s]['sw']) for s in allb}, open(os.path.join(BIG, 'big_events.json'), 'w'))
