# -*- coding: utf-8 -*-
"""Core 引擎：单根标的的事件流。规则 = 已签裁决（见包 docstring）。

事件（与 lab/p20_real_c.py 同结构，便于核对）：
  born  新波段出生：i, dir, guard(=盘整低点/高点=HL(1)/LH(1)), zone, level(门禁价),
        voids(作废次数), trans(过渡bar数), same(同向重生), below_prev(同向且没过前顶)
  new   推进一只：i, dir, n
  guard 守护点上移：i, dir, g(新守护点), at(被确认的HL那根)
  dead  死亡：i, dir, n(冻结读数), guard
snaps：逐 bar 快照 dict(dir, n, no_new_span, wave_age, hl_count)；无活波段或死亡那根为 None。
每根顺序（O2）：记新值 -> 确认 k=2 分形并上移守护点 -> 判击穿。
"""


def _px(x):
    """P2/P25 价格比较域（price_compare_policy = hfq_x100_halfup_v1）：
    后复权价 × 100，四舍五入（half-up，非银行家舍入）取整。
    用 str(x) 中转，避免二进制浮点把恰好的 .5 落成 .4999…。"""
    from decimal import Decimal, ROUND_HALF_UP
    return int((Decimal(str(x)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def small_run(bars):
    """bars: (date, open, high, low, close)。high/low 先经 _px 量化（P25）再比较。"""
    n = len(bars)
    H = [_px(b[2]) for b in bars]
    L = [_px(b[3]) for b in bars]
    ev = []
    snaps = [None] * n
    state = None                    # dict(dir, n, guard, ext, birth, last_frac, hl)
    d = 0                           # 上次死亡那根（过渡起点）
    up = {'low': 0, 'consol': None, 'voids': 0, 'zone': None}
    dn = {'high': 0, 'consol': None, 'voids': 0, 'zone': None}
    last_dir = last_ext = None

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
            if up_break:            # 同一根两边都破：上破优先（实跑 0 次）
                state = dict(dir='UP', n=1, guard=L[up['low']], ext=H[i], birth=i, last_frac=i, hl=1)
                ev.append(dict(kind='born', i=i, dir='UP', guard=state['guard'], zone=list(up['zone']),
                               level=up['consol'], voids=up['voids'], trans=i - d,
                               below_prev=(last_dir == 'UP' and H[i] <= last_ext),
                               same=(last_dir == 'UP')))
            elif dn_break:
                state = dict(dir='DN', n=1, guard=H[dn['high']], ext=L[i], birth=i, last_frac=i, hl=1)
                ev.append(dict(kind='born', i=i, dir='DN', guard=state['guard'], zone=list(dn['zone']),
                               level=dn['consol'], voids=dn['voids'], trans=i - d,
                               below_prev=(last_dir == 'DN' and L[i] >= last_ext),
                               same=(last_dir == 'DN')))
            if state is not None:
                snaps[i] = dict(dir=state['dir'], n=1, no_new_span=0, wave_age=0, hl_count=1)
        else:
            u = state['dir'] == 'UP'
            previous_span = snaps[i - 1]['no_new_span']
            advanced = (H[i] > state['ext']) if u else (L[i] < state['ext'])
            if advanced:            # O2 第 3 步：记新值
                state['n'] += 1
                state['ext'] = H[i] if u else L[i]
                ev.append(dict(kind='new', i=i, dir=state['dir'], n=state['n']))
            if (i - 2 > state['last_frac'] and all(L[i - 2] < L[t] for t in (i - 4, i - 3, i - 1, i))) if u else \
               (i - 2 > state['last_frac'] and all(H[i - 2] > H[t] for t in (i - 4, i - 3, i - 1, i))):
                state['guard'] = max(state['guard'], L[i - 2]) if u else min(state['guard'], H[i - 2])
                state['last_frac'] = i - 2
                state['hl'] += 1
                ev.append(dict(kind='guard', i=i, dir=state['dir'], g=state['guard'], at=i - 2))
            dead = (L[i] < state['guard']) if u else (H[i] > state['guard'])
            span = 0 if advanced else previous_span if dead else previous_span + 1
            snaps[i] = dict(dir=state['dir'], n=state['n'], no_new_span=span,
                            wave_age=i - state['birth'] - int(dead), hl_count=state['hl'])
            if dead:
                ev.append(dict(kind='dead', i=i, dir=state['dir'], n=state['n'], guard=state['guard'],
                               final_span=span, wave_age=snaps[i]['wave_age'],
                               ambig=bool(advanced)))   # P26：同根推进+击穿 = ambiguous_intraday_event
                snaps[i] = None         # 死亡那根起归过渡区
                last_dir, last_ext = state['dir'], state['ext']
                state = None
                d = i
                reset(i)
    return ev, snaps


def small_waves(ev):
    """事件流 -> 小波段列表（b/d 为 bar 下标，d=None 表示数据结束时仍活着）。"""
    sw, cur = [], None
    for e in ev:
        if e['kind'] == 'born':
            cur = dict(dir=e['dir'], b=e['i'], d=None, guard=e['guard'], n=1,
                       zone=e['zone'], level=e['level'], same=e['same'])
            sw.append(cur)
        elif e['kind'] == 'new' and cur is not None:
            cur['n'] = e['n']
        elif e['kind'] == 'dead' and cur is not None:
            cur['d'] = e['i']
            cur['final_span'] = e['final_span']
            cur = None
    return sw


def _refresh_count(P, b, e, up):
    """P[b..e] 里刷新"到目前为止极值"的根数，出生那根记第 1 只（新值记录法）。up：上涨比最高价，下跌比最低价。"""
    ext = P[b]
    c = 1
    for t in range(b + 1, e + 1):
        if (P[t] > ext) if up else (P[t] < ext):
            ext = P[t]
            c += 1
    return c


def big_run(H, L, SW):
    """大波段从小波段推（八步 + 已签细则；前顶 = 上一条同向小波段）。

    返回 (bigs, alive)。每条 big：dir, b, since, d, guard, cnt, nsw, by_kill, ext,
    sw(小波段下标), moves(换位记录), newbars, tops, cnt0。
    b = 出生那根（倒算继承时早于 since，只作追溯起点）；since = 可知日（P28）：
      非倒算的波段 since = b；倒算继承的波段 since = 旧大波段死的那根，这天之前它不存在。
    """
    n = len(H)
    bigs, big, tops, pend, maxtop, k = [], None, [], None, None, -1
    for i in range(n):
        if k + 1 < len(SW) and SW[k + 1]['b'] == i:
            k += 1
            w = SW[k]
            if big is None:
                big = dict(dir=w['dir'], b=i, since=i, guard=w['guard'], cnt=1, nsw=1, by_kill=False,
                           ext=H[i] if w['dir'] == 'UP' else L[i], sw=[k], moves=[], newbars=[], tops=[], cnt0=1)
                tops, pend, maxtop = [], None, None
            elif w['dir'] == big['dir']:
                big['nsw'] += 1
                big['sw'].append(k)
                pend = (tops[-1], w['guard']) if tops else None
        if big is None:
            continue
        u = big['dir'] == 'UP'
        if i > big['since'] and (H[i] > big['ext'] if u else L[i] < big['ext']):
            big['cnt'] += 1
            big['ext'] = H[i] if u else L[i]
            big['newbars'].append(i)
        if pend is not None and (H[i] > pend[0][1] if u else L[i] < pend[0][1]):
            g = min(L[pend[0][0]:i + 1]) if u else max(H[pend[0][0]:i + 1])
            big['moves'].append(dict(i=i, g=g, top=list(pend[0]), cnt=big['cnt'],
                                     is_max=pend[0] is maxtop, same_low=(g == pend[1])))
            big['guard'] = g
            pend = None
        dead = L[i] < big['guard'] if u else H[i] > big['guard']
        if dead:
            big['d'] = i
            bigs.append(big)
            cur = SW[k] if k >= 0 and SW[k]['b'] <= i and (SW[k]['d'] is None or SW[k]['d'] >= i) else None
            if cur is not None and cur['dir'] != big['dir']:
                cu = cur['dir'] == 'UP'
                # P28：继承的读数 = 旧大波段死这一根，小波段已经记到第几只。
                # 从它的出生那根数到这一根，不取它的最终只数（最终只数含这一根之后的新值）。
                cnt0 = _refresh_count(H if cu else L, cur['b'], i, cu)
                big = dict(dir=cur['dir'], b=cur['b'], since=i, guard=cur['guard'], cnt=cnt0, nsw=1, by_kill=True,
                           ext=max(H[cur['b']:i + 1]) if cu else min(L[cur['b']:i + 1]),
                           sw=[k], moves=[], newbars=[], tops=[], cnt0=cnt0)
                tops, pend, maxtop = [], None, None
            else:
                big = None
        if big is not None and k >= 0 and SW[k]['d'] == i and SW[k]['dir'] == big['dir']:
            bu = big['dir'] == 'UP'
            j = (max if bu else min)(range(SW[k]['b'], i + 1), key=lambda t: H[t] if bu else L[t])
            top = (j, H[j] if bu else L[j], SW[k]['n'])
            is_max = (H[j] >= big['ext'] if bu else L[j] <= big['ext'])
            tops.append(top)
            big['tops'].append(dict(j=j, price=top[1], n=top[2], is_max=is_max))
            if is_max:
                maxtop = top
    return bigs, big


def big_snaps(H, L, bigs, alive=None):
    """大波段逐 bar 快照，按时点（P28）。每根 dict(dir, n, no_new_span, wave_age)；没有大波段状态的 bar 为 None。

    读数：从出生那根起，每根刷新大波段极值的日线记一只，出生那根记第 1 只（与 big_run 的 cnt 同口径）。
    时点：倒算继承的波段（by_kill）在旧大波段死之前不可知，从可知日 since 起才写；
    [b, since) 那几根仍是旧大波段的快照。出生那根未推进时长为 0，与小波段一致。
    活到数据末的波段（alive）写到最后一根。
    """
    n = len(H)
    snaps = [None] * n
    for w in bigs + ([alive] if alive is not None else []):
        P = H if w['dir'] == 'UP' else L
        up = w['dir'] == 'UP'
        end = w['d'] if w.get('d') is not None else n - 1
        ext = P[w['b']]
        cnt = span = 0
        for i in range(w['b'], end + 1):
            refresh = i == w['b'] or (P[i] > ext if up else P[i] < ext)
            if refresh:
                ext = P[i]
                cnt += 1
                span = 0
            else:
                span += 1
            if i >= w['since']:
                snaps[i] = dict(dir=w['dir'], n=cnt, no_new_span=span, wave_age=i - w['b'])
    return snaps
