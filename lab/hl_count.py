# HH(n) 与 HL(m) 双序列统计（2026-11-26，用户提出：hh、hl 各自记新值第几只）
# 口径：写法 C（k=2 分形确认 HL 才上移守护点）。
# 小波段：HL(1) = 出生守护点（盘整低点）；之后每次确认出更高的分形低点，m+1，守护点跟过去。
#        比当前守护点低的分形低点不算 HL（不抬高，不进序列）。
# 大波段：HL(1) = 出生守护点；之后每次按八步换守护点（过前顶那根），m+1。
import os, csv, json, collections, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed', 'hl')
os.makedirs(OUT, exist_ok=True)
rows = collections.defaultdict(list)
for x in csv.DictReader(open(os.path.join(ROOT, 'data', 'raw', 'bars.csv'), encoding='utf-8')):
    rows[x['symbol']].append(x)
for k in rows:
    rows[k].sort(key=lambda r: r['date'])


def small_waves_hl(bars):
    """写法 C，逐条小波段记录 HL 序列。"""
    H = [float(r['high']) for r in bars]
    L = [float(r['low']) for r in bars]
    n = len(bars)
    waves = []
    state = None
    up = {'low': 0, 'consol': None, 'voids': 0}
    dn = {'high': 0, 'consol': None, 'voids': 0}
    for i in range(n):
        if state is None:
            if L[i] < L[up['low']]:
                up['low'] = i; up['consol'] = None; up['voids'] += 1
            elif up['consol'] is None and i > 0 and H[i] <= H[i - 1]:
                up['consol'] = max(H[up['low']:i + 1])
            if H[i] > H[dn['high']]:
                dn['high'] = i; dn['consol'] = None; dn['voids'] += 1
            elif dn['consol'] is None and i > 0 and L[i] >= L[i - 1]:
                dn['consol'] = min(L[dn['high']:i + 1])
            if up['consol'] is not None and H[i] > up['consol']:
                state = dict(dir='UP', b=i, ext=H[i], guard=L[up['low']],
                             hh=[(i, H[i])], hl=[(up['low'], L[up['low']])], last_hl_bar=i)
            elif dn['consol'] is not None and L[i] < dn['consol']:
                state = dict(dir='DN', b=i, ext=L[i], guard=H[dn['high']],
                             hh=[(i, L[i])], hl=[(dn['high'], H[dn['high']])], last_hl_bar=i)
        else:
            w = state
            if w['dir'] == 'UP':
                if H[i] > w['ext']:
                    w['ext'] = H[i]; w['hh'].append((i, H[i]))
                # k=2 分形低点确认（与 nested.py 写法 C 同一判定）
                if i - 2 > w['last_hl_bar'] and all(L[i - 2] < L[t] for t in (i - 4, i - 3, i - 1, i)):
                    if L[i - 2] > w['guard']:          # 只记抬高的（用户：hl 渐次抬高）
                        w['guard'] = L[i - 2]
                        w['hl'].append((i - 2, L[i - 2]))
                    w['last_hl_bar'] = i - 2
                if L[i] < w['guard']:
                    w['d'] = i; waves.append(w); state = None
                    up.update(low=i, consol=None, voids=0); dn.update(high=i, consol=None, voids=0)
            else:
                if L[i] < w['ext']:
                    w['ext'] = L[i]; w['hh'].append((i, L[i]))
                if i - 2 > w['last_hl_bar'] and all(H[i - 2] > H[t] for t in (i - 4, i - 3, i - 1, i)):
                    if H[i - 2] < w['guard']:
                        w['guard'] = H[i - 2]
                        w['hl'].append((i - 2, H[i - 2]))
                    w['last_hl_bar'] = i - 2
                if H[i] > w['guard']:
                    w['d'] = i; waves.append(w); state = None
                    up.update(low=i, consol=None, voids=0); dn.update(high=i, consol=None, voids=0)
    return waves


allw = []
per_sym = {}
for s, bars in rows.items():
    ws = small_waves_hl(bars)
    per_sym[s] = ws
    allw.extend(ws)

json.dump({s: [dict(dir=w['dir'], b=w['b'], d=w['d'], n=len(w['hh']), m=len(w['hl']),
                    hh=w['hh'], hl=w['hl']) for w in ws] for s, ws in per_sym.items()},
          open(os.path.join(OUT, 'hl.json'), 'w', encoding='utf-8'))

up = [w for w in allw if w['dir'] == 'UP']
dnw = [w for w in allw if w['dir'] == 'DN']
print('小波段 %d 条（涨 %d / 跌 %d）' % (len(allw), len(up), len(dnw)))
ns = [len(w['hh']) for w in allw]
ms = [len(w['hl']) for w in allw]
print('HH(n)：中位 %d，均值 %.2f，最大 %d' % (statistics.median(ns), statistics.mean(ns), max(ns)))
print('HL(m)：中位 %d，均值 %.2f，最大 %d' % (statistics.median(ms), statistics.mean(ms), max(ms)))
print('m 分布：m=1 %.1f%%，m=2 %.1f%%，m=3 %.1f%%，m>=4 %.1f%%' % (
    100 * sum(1 for m in ms if m == 1) / len(ms),
    100 * sum(1 for m in ms if m == 2) / len(ms),
    100 * sum(1 for m in ms if m == 3) / len(ms),
    100 * sum(1 for m in ms if m >= 4) / len(ms)))
diff = collections.Counter(len(w['hh']) - len(w['hl']) for w in allw)
print('n − m 分布（前 9 档）:', sorted(diff.items())[:9])
print('n > m 占 %.1f%%，n = m 占 %.1f%%，n < m 占 %.1f%%' % (
    100 * sum(v for k, v in diff.items() if k > 0) / len(allw),
    100 * diff[0] / len(allw),
    100 * sum(v for k, v in diff.items() if k < 0) / len(allw)))
# 抬升单调性（构造上必单调，验证一下）
bad = sum(1 for w in allw for a, b in zip(w['hl'], w['hl'][1:]) if (b[1] <= a[1]) == (w['dir'] == 'UP'))
print('HL 序列不单调的次数（应为 0）:', bad)
# 死亡那根与最新 HL 的关系：跌穿最新 HL 即死（构造如此）；看「死了但最新 HL 离顶多远」
gaps = []
for w in up:
    top = max(p for _, p in w['hh'])
    gaps.append((top - w['hl'][-1][1]) / top)
print('上涨小波段：顶到最新 HL 的距离 / 顶，中位 %.1f%%，均值 %.1f%%' % (
    100 * statistics.median(gaps), 100 * statistics.mean(gaps)))
# HL(m) 之间的间隔（根数）
gaps2 = [b[0] - a[0] for w in allw for a, b in zip(w['hl'], w['hl'][1:])]
if gaps2:
    print('相邻 HL 间隔：中位 %d 根，均值 %.1f 根' % (statistics.median(gaps2), statistics.mean(gaps2)))
print('产物 ->', os.path.join(OUT, 'hl.json'))
