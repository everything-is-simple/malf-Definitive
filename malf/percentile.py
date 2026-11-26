# -*- coding: utf-8 -*-
"""分位：扩展窗历史池（P10 时点纪律 + P24/P25 契约，2026-11-26 签署对齐）。

口径（与当前稿 4.3.3 一致）：
- 历史库 = 已死的同类波段的冻结读数；级别（小/大）与方向各建一个池；全市场不分层（P7）。
- 时点纪律：某根 bar 上的分位，用**死亡日期不晚于该 bar 日期**的波段（含当日，跨股同日
  死亡的波段可用；扩展窗，无未来函数）。
- 比较方向：严格小于 count(x_i < x) / N，分位取值 [0, 1)，永远到不了 1。
- 门槛：池内不足 MIN_POOL 条样本返回 None，不 fallback、不补零、不扩大范围。
- 两个分位的历史样本：
    pct_n     当前新高第几只 n  在池内"最终只数 final_n"里的排位
    pct_span  当前未推进时长     在池内"临终未推进 final_span"（死亡那根收盘时的冻结读数，
              不是全程最大）里的排位
用法：
    pool = ExpandingPool(waves)            # waves: 可迭代 dict(dir, dd=死亡日期str或None,
                                           #       final_span)，读数字段默认 n，大波段用
                                           #       ExpandingPool(waves, 'cnt')
    sorted_n, sorted_span = pool.before(date, 'UP')
    p = pct(sorted_n, x)
"""
from bisect import bisect_left, insort

MIN_POOL = 30          # 4.3.3：不足 30 条样本返回 None


def pct(sorted_vals, x):
    """sorted_vals: 升序列表。严格小于：返回 #(v < x) / N；不足 MIN_POOL 条返回 None。"""
    if len(sorted_vals) < MIN_POOL:
        return None
    return round(bisect_left(sorted_vals, x) / len(sorted_vals), 4)


class ExpandingPool:
    """按死亡日期扩展的历史池：before(date, dir) 返回死亡日期 <= date 的已死波段的
    (升序最终只数列表, 升序临终未推进列表)。查询日期总体递增时均摊 O(1)
    （逐标的遍历时日期局部递增，指针不回退，正确性不受影响）。"""

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
        while c['i'] < len(deaths) and deaths[c['i']]['dd'] <= date:
            w = deaths[c['i']]
            insort(c['n'], w[self._ck])
            insort(c['span'], w['final_span'])
            c['i'] += 1
        return c['n'], c['span']
