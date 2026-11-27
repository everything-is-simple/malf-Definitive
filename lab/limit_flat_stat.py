# -*- coding: utf-8 -*-
"""外审第四轮对账：相邻两根最高价相等的到底有多少；一字连板的最高价是否相等。
结论写进当前稿 5.4 与 §10（2026-11-27）：连续一字涨停每根的最高价都更高，没有一对相等。

用法（工作台根目录；文件没按标的排好，要先排序再喂进来）：
    sort -t, -k1,1 -k2,2 data/raw/bars_all.csv | python lab/limit_flat_stat.py
只读，不写任何文件，只用标准库。

一字 = 开、高、低、收四个价相等（后复权价上等式不变）。
一字涨停 = 一字且收盘高于前一根收盘；一字跌停镜像。
"""
import collections
import csv
import sys

sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from malf.core import _px

A = collections.Counter()
maxrun = 0
seen = set()


def proc(rows):
    global maxrun
    n = len(rows)
    A['日线根数'] += n
    O = [r[1] for r in rows]
    H = [r[2] for r in rows]
    L = [r[3] for r in rows]
    C = [r[4] for r in rows]
    flat = [0] * n
    fu = [0] * n
    fd = [0] * n
    for i in range(n):
        if O[i] == H[i] == L[i] == C[i]:
            flat[i] = 1
            A['一字'] += 1
            if i > 0:
                if C[i] > C[i - 1]:
                    fu[i] = 1
                    A['其中一字涨停'] += 1
                elif C[i] < C[i - 1]:
                    fd[i] = 1
                    A['其中一字跌停'] += 1
                else:
                    A['其中一字平'] += 1
    Hp = [_px(x) for x in H]
    Lp = [_px(x) for x in L]
    run = 0
    for i in range(1, n):
        if H[i] == H[i - 1]:
            A['相邻两根最高价相等'] += 1
            run += 1
            maxrun = max(maxrun, run)
            if flat[i] and flat[i - 1]:
                A['  其中两根都是一字'] += 1
            else:
                A['  其中不是两个一字'] += 1
            if fu[i] and fu[i - 1]:
                A['  其中两根都是一字涨停'] += 1
            if fd[i] and fd[i - 1]:
                A['  其中两根都是一字跌停'] += 1
        else:
            run = 0
        if L[i] == L[i - 1]:
            A['相邻两根最低价相等'] += 1
            if fd[i] and fd[i - 1]:
                A['  其中两根都是一字跌停'] += 1
            if fu[i] and fu[i - 1]:
                A['  其中两根都是一字涨停'] += 1
        if Hp[i] == Hp[i - 1]:
            A['取整后最高价相等'] += 1
        if Lp[i] == Lp[i - 1]:
            A['取整后最低价相等'] += 1
        if fu[i] and fu[i - 1]:
            A['相邻两根一字涨停'] += 1
            if H[i] > H[i - 1]:
                A['  其中后一根最高价更高'] += 1
            if H[i] == H[i - 1]:
                A['  其中最高价相等'] += 1
        if fd[i] and fd[i - 1]:
            A['相邻两根一字跌停'] += 1
            if L[i] < L[i - 1]:
                A['  其中后一根最低价更低'] += 1
            if L[i] == L[i - 1]:
                A['  其中最低价相等'] += 1


cur = None
buf = []
rd = csv.reader(sys.stdin)
next(rd)
for r in rd:
    if r[0] == 'symbol':          # 表头被 sort 排到了文件中间
        continue
    s = r[0]
    if s != cur:
        if cur is not None:
            proc(buf)
        assert s not in seen, '排序后同一标的又出现'
        seen.add(s)
        cur = s
        buf = []
    buf.append((r[1], float(r[2]), float(r[3]), float(r[4]), float(r[5])))
proc(buf)
A['标的数'] = len(seen)
for k, v in A.items():
    print('%-22s %d' % (k, v))
print('%-22s %d' % ('最高价相等最长连续根数', maxrun))
