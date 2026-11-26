# -*- coding: utf-8 -*-
"""分位契约测试（4.3.3 已签口径，2026-11-26）。

运行（工作台根目录）：python -m unittest discover -s tests -v
覆盖：
- 严格小于：等于池内最大值 → (N-1)/N；高于全部 → 1.0（不超 1）
- MIN_POOL = 30：29 条返回 None，30 条出值
- 时点纪律（P10/P25）：死亡日期 ≤ 查询日期（含当日）；查询日期递增
- count_key：大波段用 cnt 建池
- ExpandingPool 单调性：同日查询共享同一截止池，不回退
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from malf.percentile import pct, ExpandingPool, MIN_POOL


def waves(spec):
    """spec: (dir, dd, n, final_span)"""
    return [dict(dir=d, dd=dd, n=n, final_span=s) for d, dd, n, s in spec]


class TestStrictLessThan(unittest.TestCase):
    def test_below_max(self):
        pool = list(range(1, 31))          # 30 条，1..30
        self.assertEqual(pct(pool, 30), round(29 / 30, 4))

    def test_above_all_is_one(self):
        pool = list(range(1, 31))
        self.assertEqual(pct(pool, 31), 1.0)
        self.assertEqual(pct(pool, 999), 1.0)

    def test_below_all_is_zero(self):
        pool = list(range(10, 40))
        self.assertEqual(pct(pool, 1), 0.0)

    def test_equal_values_not_counted(self):
        pool = [5] * 30
        self.assertEqual(pct(pool, 5), 0.0)   # 严格小于：等于不计
        self.assertEqual(pct(pool, 6), 1.0)


class TestMinPool(unittest.TestCase):
    def test_threshold(self):
        pool29 = list(range(29))
        pool30 = list(range(30))
        self.assertIsNone(pct(pool29, 10))
        self.assertIsNotNone(pct(pool30, 10))
        self.assertEqual(MIN_POOL, 30)


class TestExpandingPool(unittest.TestCase):
    SPEC = [
        ('UP', '2020-02-01', 3, 4),
        ('UP', '2020-03-01', 5, 9),
        ('DN', '2020-02-15', 4, 6),
        ('UP', '2020-01-15', 2, 3),   # 死亡最早但列在后面：构造时须按 dd 排序
    ]

    def test_includes_same_day_death(self):
        p = ExpandingPool(waves(self.SPEC))
        n, sp = p.before('2020-01-31', 'UP')   # 含 01-15 那条
        self.assertEqual(list(n), [2])
        n, sp = p.before('2020-02-01', 'UP')   # 含当日死亡
        self.assertEqual(list(n), [2, 3])

    def test_monotonic_no_shrink(self):
        # 注意：before() 返回内部活列表，快照须立即 list()，否则后续调用会改动它
        p = ExpandingPool(waves(self.SPEC))
        a, _ = p.before('2020-02-01', 'UP')
        a = list(a)
        b, _ = p.before('2020-03-01', 'UP')
        b = list(b)
        c, _ = p.before('2020-03-01', 'UP')    # 同日再查：共享截止池
        self.assertLess(len(a), len(b))
        self.assertEqual(b, list(c))

    def test_dir_separation(self):
        p = ExpandingPool(waves(self.SPEC))
        n_up, _ = p.before('2020-12-31', 'UP')
        n_dn, _ = p.before('2020-12-31', 'DN')
        self.assertNotIn(4, list(n_up))
        self.assertEqual(list(n_dn), [4])

    def test_alive_not_in_pool(self):
        spec = self.SPEC + [('UP', None, 7, 7)]     # 活到数据末：dd=None
        p = ExpandingPool(waves(spec))
        n, _ = p.before('2020-12-31', 'UP')
        self.assertNotIn(7, list(n))

    def test_count_key_cnt(self):
        # 大波段池读 cnt 字段（__main__ 传入的 bigs 同时带 n 与 cnt）
        spec = [dict(dir='UP', dd='2020-01-01', n=3, cnt=10, final_span=4),
                dict(dir='UP', dd='2020-02-01', n=5, cnt=18, final_span=8)]
        p = ExpandingPool(spec, 'cnt')
        n, sp = p.before('2020-12-31', 'UP')
        self.assertEqual(list(n), [10, 18])   # 读的是 cnt 列，不是 n
        self.assertEqual(list(sp), [4, 8])


if __name__ == '__main__':
    unittest.main()
