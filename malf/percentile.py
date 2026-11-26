# -*- coding: utf-8 -*-
"""分位：把活的读数放进历史同类里排位置。

口径（首跑假设，待用户确认）：
- 历史库 = 已死的同类波段的冻结读数；级别（小/大）与方向各建一个池；全市场不分层（P7）。
- 时点纪律：某根 bar 上的分位，只用**在那根之前已经死掉**的波段（扩展窗，无未来函数，P10）。
- 两个分位：
    pct_n     当前新高第几只 n，在历史"最终只数"里的位置 = #(final_n <= n) / 池大小
    pct_span  当前未推进时长，在历史"最大未推进时长"里的位置 = #(max_span <= span) / 池大小
"""


def history_pool(waves):
    """waves: 波段列表（含活着的）。返回 dict(dir -> sorted list of (final_n, max_span, lifespan))，只收已死的。"""
    pool = {'UP': [], 'DN': []}
    for w in waves:
        if w['d'] is None:
            continue
        pool[w['dir']].append((w['n'], w['max_span'], w['d'] - w['b']))
    for d in pool:
        pool[d].sort()
    return pool


def pct(sorted_vals, x):
    """sorted_vals: 升序列表；返回 #(v <= x) / len。"""
    if not sorted_vals:
        return None
    from bisect import bisect_right
    return round(bisect_right(sorted_vals, x) / len(sorted_vals), 4)


def finalize(waves, snaps_by_wave):
    """给每条波段补上 max_span（活着期间 no_new_span 的最大值）。snaps_by_wave 与 waves 同序。"""
    for w, snaps in zip(waves, snaps_by_wave):
        seg = [s for s in snaps if s is not None]
        w['max_span'] = max((s['no_new_span'] for s in seg), default=0)
        w['lifespan'] = (w['d'] - w['b']) if w['d'] is not None else None
    return waves
