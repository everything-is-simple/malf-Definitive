# -*- coding: utf-8 -*-
"""分位：扩展窗历史池（P10 时点纪律）。

口径：
- 历史库 = 已死的同类波段的冻结读数；级别（小/大）与方向各建一个池；全市场不分层（P7）。
- 时点纪律：某根 bar 上的分位，只用**死亡日期早于该 bar 日期**的波段（扩展窗，无未来函数）。
- 两个分位：
    pct_n     当前新高第几只 n，在池内"最终只数"里的位置 = #(final_n <= n) / 池大小
    pct_span  当前未推进时长，在池内"最大未推进时长"里的位置 = #(max_span <= span) / 池大小
用法：
    pool = ExpandingPool(waves)            # waves: 可迭代 dict(dir, dd=死亡日期str或None, max_span)，
                                           #       读数字段默认 n，大波段用 ExpandingPool(waves, 'cnt')
    sorted_n, sorted_span = pool.before(date, 'UP')
    p = pct(sorted_n, x)
"""
from bisect import bisect_right, insort


def pct(sorted_vals, x):
    """sorted_vals: 升序列表；返回 #(v <= x) / len；空池返回 None。"""
    if not sorted_vals:
        return None
    return round(bisect_right(sorted_vals, x) / len(sorted_vals), 4)


class ExpandingPool:
    """按死亡日期扩展的历史池：before(date, dir) 返回 date 之前已死波段的
    (升序最终只数列表, 升序最大未推进列表)。查询按日期递增调用时均摊 O(1)。"""

    def __init__(self, waves, count_key='n'):
        self._ck = count_key
        self._deaths = {}
        for d in ('UP', 'DN'):
            self._deaths[d] = sorted((w for w in waves if w['dir'] == d and w.get('dd') is not None),
                                     key=lambda w: w['dd'])
        self._cur = {d: dict(n=[], span=[], i=0) for d in ('UP', 'DN')}

    def before(self, date, d):
        c = self._cur[d]
        deaths = self._deaths[d]
        while c['i'] < len(deaths) and deaths[c['i']]['dd'] < date:
            w = deaths[c['i']]
            insort(c['n'], w[self._ck])
            insort(c['span'], w['max_span'])
            c['i'] += 1
        return c['n'], c['span']
