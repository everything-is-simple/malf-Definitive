# -*- coding: utf-8 -*-
"""引擎 golden 测试 + 关键契约测试（v3.1 已签口径，2026-11-26）。

运行（工作台根目录）：python -m unittest discover -s tests -v
覆盖：
- P25 价格比较域：后复权价 ×100 四舍五入 half-up（非银行家）
- P23 同一根 bar：先确认 HL 上移守护，再按新守护判死
- L6/L-T4 临终冻结：击穿那根不再加一（final_span = 前一根 no_new_span）
- P20 盘整出生：停一根即盘整、门禁 = 盘整高值、出生守护 = 盘整低点、born 记第 1 只
- 大波段八步：过前顶守护换到整段回调最低点、+1 加在大波段自己读数上
- golden 快照：合成序列的事件流签名冻结（tests/golden_engine.json，重建用 GEN=1）
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from malf.core import _px, small_run, small_waves, big_run

GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'golden_engine.json')


def sig(ev):
    """事件结构签名（与全市场核对同口径：kind/i/dir/n）。"""
    return [(e['kind'], e['i'], e['dir'], e.get('n')) for e in ev]


class TestPx(unittest.TestCase):
    def test_half_up(self):
        self.assertEqual(_px(12.345), 1235)
        self.assertEqual(_px(12.3449), 1234)
        self.assertEqual(_px(12.3451), 1235)

    def test_float_repr_not_bankers(self):
        # 2.675 的二进制浮点是 2.67499…，str 中转后必须仍按 half-up 进位；
        # 若误用 round()（银行家舍入）会得到 267
        self.assertEqual(_px(2.675), 268)
        self.assertEqual(_px(0.125), 13)   # 银行家舍入会给 12

    def test_int_domain(self):
        self.assertIsInstance(_px(9.99), int)


class TestSameBarP23(unittest.TestCase):
    """P23（同一根 bar 机械按 O2，新守护当根生效）的边界行为。

    定理（E4，2026-11-27 精确化）：设 g_t 为第 t 根处理后守护值。若 g_t > g_{t-1}
    （严格上移），则同根判死不成立。证明：严格上移 ⟹ 分形确认且 g_t = L[t-2]；
    分形比较集含当前根 ⟹ L[t-2] < L[t]；判死要求 L[t] < g_t = L[t-2]，矛盾。
    依赖两个结构要件：更新取极值使新守护恰等于分形值；比较集含当前根给出反向不等式。
    守护未严格变化时新旧同值，判定无差异。故 P23 对当前引擎恒真。
    本组测试钉住边界：确认守护那根必不死、下一根起按新守护判死。
    """

    H = [10, 12, 11, 13, 14, 15, 15, 14]
    L = [ 9, 10, 10.6, 11, 10.5, 12, 11.2, 10.4]

    def test_guard_bar_never_dies(self):
        bars = [('d%d' % i, 0, self.H[i], self.L[i], 0) for i in range(7)]
        ev, _ = small_run(bars)
        g = [e for e in ev if e['kind'] == 'guard']
        self.assertEqual(len(g), 1)
        self.assertEqual((g[0]['i'], g[0]['g']), (6, 1050))
        self.assertNotIn(('dead', 6), [(e['kind'], e['i']) for e in ev])

    def test_death_uses_new_guard_next_bar(self):
        bars = [('d%d' % i, 0, self.H[i], self.L[i], 0) for i in range(8)]
        ev, _ = small_run(bars)
        dead = [e for e in ev if e['kind'] == 'dead']
        self.assertEqual(len(dead), 1)
        self.assertEqual(dead[0]['i'], 7)
        self.assertEqual(dead[0]['guard'], 1050)   # 新守护，不是出生守护 900


class TestAmbigP26(unittest.TestCase):
    """P26：同根推进+击穿 → dead 事件 ambig=True（ambiguous_intraday_event，纯审计不改判定）。"""

    def test_new_and_dead_same_bar(self):
        # born i=2 guard=900；i=3 最高 13 刷新极值（推进）且最低 8.5 跌破 900（击穿）→ 同根双事件
        H = [12, 11, 12.5, 13]
        L = [ 9, 9.2, 9.0, 8.5]
        ev, _ = small_run([('d%d' % i, 0, H[i], L[i], 0) for i in range(4)])
        dead = [e for e in ev if e['kind'] == 'dead']
        self.assertEqual(len(dead), 1)
        self.assertTrue(dead[0]['ambig'])
        self.assertEqual(dead[0]['n'], 2)          # 推进已记，再判死
        self.assertEqual(dead[0]['final_span'], 0)  # 推进那根归零，冻结

    def test_plain_death_not_ambig(self):
        bars = [('d%d' % i, 0, h, l, 0) for i, (h, l) in
                enumerate([(12, 9), (11, 9.2), (12.5, 9.0), (12.4, 8.5)])]
        ev, _ = small_run(bars)
        dead = [e for e in ev if e['kind'] == 'dead']
        self.assertEqual(len(dead), 1)
        self.assertFalse(dead[0]['ambig'])


class TestFreezeL6(unittest.TestCase):
    """L6/L-T4：死亡那根不再加一，final_span = 前一根的 no_new_span。"""

    def test_freeze(self):
        # born i=3（guard=11），i=4 新高 n=2，i=5..8 停 4 根，i=9 跌破 11 死。
        H = [10, 12, 11, 13, 14, 13, 13, 13, 13, 12]
        L = [ 9, 10, 10, 11, 12, 12, 12, 12, 12,  8]
        bars = [('d%d' % i, 0, H[i], L[i], 0) for i in range(len(H))]
        ev, snaps = small_run(bars)
        dead = [e for e in ev if e['kind'] == 'dead']
        self.assertEqual(len(dead), 1)
        self.assertEqual(dead[0]['final_span'], 4)   # 不是 5
        self.assertEqual(dead[0]['wave_age'], 5)     # i - birth - 1
        self.assertEqual(snaps[8]['no_new_span'], 4)
        self.assertIsNone(snaps[9])                  # 死亡那根起归过渡区


class TestP20Birth(unittest.TestCase):
    def test_consolidation_birth(self):
        # i=0 低点 9；i=1 H 不高于前一根 → 盘整成立，盘整高值=12、低点=9。
        # i=2 上破 12 → born UP，n=1，guard=900（盘整低点），可以低于任何前顶。
        H = [12, 12, 13]
        L = [ 9, 10, 10]
        bars = [('d%d' % i, 0, H[i], L[i], 0) for i in range(3)]
        ev, snaps = small_run(bars)
        self.assertEqual(sig(ev), [('born', 2, 'UP', None)])   # born 事件不带 n
        self.assertEqual(ev[0]['guard'], 900)
        self.assertEqual(ev[0]['level'], 1200)
        self.assertEqual(snaps[2]['n'], 1)                     # 快照记第 1 只

    def test_stall_one_bar(self):
        # 停一根即盘整（P20），不等确认
        H = [12, 11, 12.5]
        L = [ 9,  9,  9.5]
        ev, _ = small_run([('d%d' % i, 0, H[i], L[i], 0) for i in range(3)])
        self.assertEqual(sig(ev), [('born', 2, 'UP', None)])


class TestBigEightSteps(unittest.TestCase):
    """八步核心：过前顶那根，守护换到整段回调最低点、+1 加在大波段读数上。

    直接喂手工小波段列表测 big_run（避开小波段引擎的联动约束）：
      小波段① UP b=0 d=4 n=2 guard=900（前顶在 i=3，价 1300）
      小波段② UP b=6 活着   n=3 guard=945（同向 → 大波段延续，pend=①的前顶）
      i=9 最高 1320 过前顶 1300 → 守护换到整段回调最低点 min(L[3..9])，cnt 已 +1
    注：小波段②的出生守护必不低于大波段守护（更低的低点会先击穿大波段），
       所以 UP 大波段的守护「换到整段回调最低点」实际是把守护抬到顶后区间的最低低点。
    """

    H = [12, 11.5, 11.8, 13, 12.4, 12.2, 12.5, 12.7, 12.9, 13.2]
    L = [9.0, 9.3, 9.2, 9.6, 9.5, 9.4, 9.45, 9.5, 9.55, 9.6]
    SW = [dict(dir='UP', b=0, d=4, guard=900, n=2),
          dict(dir='UP', b=6, d=None, guard=945, n=3)]

    def test_guard_move_and_own_count(self):
        H = [_px(x) for x in self.H]
        L = [_px(x) for x in self.L]
        bigs, alive = big_run(H, L, self.SW)
        self.assertEqual(bigs, [])           # 大波段活到数据末
        self.assertIsNotNone(alive)
        mv = alive['moves']
        self.assertEqual(len(mv), 1)
        # 换到整段回调最低点：前顶那根到破位那根之间的最低 low
        top_i = mv[0]['top'][0]
        lo = min(L[top_i:mv[0]['i'] + 1])
        self.assertEqual(mv[0]['g'], lo)
        self.assertEqual(mv[0]['g'], 940)
        # +1 加在大波段自己的读数上：过顶那根 cnt 已有推进
        self.assertEqual(mv[0]['cnt'], 3)


class TestGoldenSnapshot(unittest.TestCase):
    """合成多波段序列的事件流签名快照（防第三处改岔）。重建：GEN=1 python -m unittest tests.test_engine"""

    def test_golden(self):
        bars = self._fixture()
        ev, snaps = small_run(bars)
        got = dict(sig=sig(ev),
                   dead=[(e['i'], e['final_span']) for e in ev if e['kind'] == 'dead'],
                   born=[(e['i'], e['dir'], e['guard'], e['level']) for e in ev if e['kind'] == 'born'])
        if os.environ.get('GEN'):
            json.dump(got, open(GOLDEN, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            self.skipTest('golden regenerated')
        want = json.load(open(GOLDEN, encoding='utf-8'))
        self.assertEqual(json.loads(json.dumps(got)), want)   # JSON 往返规范化元组/列表

    @staticmethod
    def _fixture():
        # 合成 24 根：一条上涨小波段走完全程（出生→推进→守护上移→死亡），
        # 过渡后第二条上涨小波段活到数据末
        seq = [
            (12, 9), (12, 10), (13, 11),      # i0-2  盘整
            (14, 11.5), (13, 12), (15, 12.5), # i3-5  born i3 UP
            (16, 13), (15, 12), (14, 11.4),   # i6-8  i8 跌破 11 死
            (13, 10), (12.5, 10.5), (12, 10.8),  # i9-11 盘整（DN 侧）
            (11, 10.2), (10.5, 9),            # i12-13 born i12 DN
            (11, 9.5), (12, 9.2),             # i14-15
            (12, 10), (11.5, 10.5), (12, 10.4),  # i16-18 停 → i19 破？不破（10.4<11?）
            (13, 10.6), (14, 11),             # i19-20 新高
            (13.5, 11.2), (13, 11.5),         # i21-22 停
            (13.2, 11.1),                     # i23 仍活
        ]
        return [('d%02d' % i, 0, h, l, 0) for i, (h, l) in enumerate(seq)]


if __name__ == '__main__':
    unittest.main()
