"""
analyze_path_ordering.py
Path-ordering анализ: что бьёт первым — SL или TP?

Для каждой сделки из all_trades.csv (gt_category=TP_CLEAR или BOTH_HIT)
прокручивает H1 OHLC bar-by-bar и определяет: SL_first или TP_first.
Сравнивает с реальным MT4 результатом.

Usage:
  python statistics/analyze_path_ordering.py
"""

import csv
from datetime import datetime
from collections import Counter, defaultdict

TRADES_CSV   = "statistics/all_trades.csv"
OHLC_CSV     = "DATA/XAUUSD_H1_OHLC.csv"
SCAN_BARS    = 12   # окно поиска (баров после сигнала)
REPORT_OUT   = "docs/archive/signal_tracer/path_ordering_analysis.md"

# ─── Загрузка OHLC ────────────────────────────────────────────────────────────

def load_ohlc(path):
    ohlc = {}  # datetime -> (open, high, low, close)
    with open(path) as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            t = datetime.strptime(row['time'], "%Y.%m.%d %H:%M")
            ohlc[t] = (
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
            )
    # Отсортированный список времён для быстрого поиска следующего бара
    times = sorted(ohlc.keys())
    time_idx = {t: i for i, t in enumerate(times)}
    return ohlc, times, time_idx

# ─── Bar-by-bar scan ─────────────────────────────────────────────────────────

def path_order(bar_time, direction, sl_price, tp_price, ohlc, times, time_idx, scan=SCAN_BARS):
    """
    Возвращает: 'SL_FIRST', 'TP_FIRST', 'TIMEOUT'
    direction: 'BUY' -> TP=выше, SL=ниже; 'SELL' -> наоборот
    """
    idx0 = time_idx.get(bar_time)
    if idx0 is None:
        return 'NO_BAR'

    for i in range(idx0 + 1, min(idx0 + 1 + scan, len(times))):
        t = times[i]
        o, h, l, c = ohlc[t]

        sl_hit = (direction == 'BUY'  and l <= sl_price) or \
                 (direction == 'SELL' and h >= sl_price)
        tp_hit = (direction == 'BUY'  and h >= tp_price) or \
                 (direction == 'SELL' and l <= tp_price)

        if sl_hit and tp_hit:
            # Оба в одном баре: используем Open для определения порядка
            if direction == 'BUY':
                sl_dist = o - sl_price
                tp_dist = tp_price - o
            else:
                sl_dist = sl_price - o
                tp_dist = o - tp_price
            return 'SL_FIRST' if sl_dist < tp_dist else 'TP_FIRST'

        if sl_hit: return 'SL_FIRST'
        if tp_hit: return 'TP_FIRST'

    return 'TIMEOUT'

# ─── Основной анализ ─────────────────────────────────────────────────────────

def main():
    print("Загрузка OHLC...")
    ohlc, times, time_idx = load_ohlc(OHLC_CSV)
    print(f"  Загружено {len(times)} баров: {times[0]} — {times[-1]}")

    print("Загрузка сделок...")
    with open(TRADES_CSV) as f:
        trades = list(csv.DictReader(f, delimiter=';'))
    print(f"  Всего сделок: {len(trades)}")

    # Анализируем TP_CLEAR + BOTH_HIT
    target_cats = {'TP_CLEAR', 'BOTH_HIT', 'SL_CLEAR'}
    subset = [r for r in trades if r['category'] in target_cats]
    print(f"  Анализируем: {len(subset)} (TP_CLEAR+BOTH_HIT+SL_CLEAR)")

    results = []
    no_bar = 0

    for r in subset:
        try:
            bar_time = datetime.strptime(r['time'], "%Y.%m.%d %H:%M")
            direction = r['direction']
            val   = float(r['val'])
            stp   = float(r['stp'])
            prf   = float(r['prf'])
        except (ValueError, KeyError):
            continue

        po = path_order(bar_time, direction, stp, prf, ohlc, times, time_idx)
        if po == 'NO_BAR':
            no_bar += 1
            continue

        results.append({
            'time':     r['time'],
            'dir':      direction,
            'category': r['category'],
            'mt4':      r['mt4_result'],
            'path_order': po,
            'ratio':    r['ratio'],
        })

    if no_bar:
        print(f"  Не найдено в OHLC: {no_bar} баров")

    # ─── Статистика ───────────────────────────────────────────────────────────

    def stats_for(label, subset_res):
        total = len(subset_res)
        if total == 0:
            return f"{label}: 0 trades\n"
        po_cnt   = Counter(r['path_order'] for r in subset_res)
        mt4_cnt  = Counter(r['mt4'] for r in subset_res)
        sl_first = po_cnt.get('SL_FIRST', 0)
        tp_first = po_cnt.get('TP_FIRST', 0)
        timeout  = po_cnt.get('TIMEOUT', 0)
        decisive = sl_first + tp_first
        pct_sl   = 100 * sl_first / decisive if decisive else 0
        pct_tp   = 100 * tp_first / decisive if decisive else 0
        s  = f"### {label} ({total} сделок)\n"
        s += f"- Path order:  SL_FIRST={sl_first} ({pct_sl:.0f}%)  TP_FIRST={tp_first} ({pct_tp:.0f}%)  TIMEOUT={timeout}\n"
        s += f"- MT4 results: {dict(mt4_cnt)}\n"
        # Cross-table
        ct = defaultdict(Counter)
        for r in subset_res:
            ct[r['path_order']][r['mt4']] += 1
        s += "- Cross-table (path_order × mt4_result):\n"
        for po_key in ['SL_FIRST', 'TP_FIRST', 'TIMEOUT']:
            if ct[po_key]:
                s += f"  - {po_key}: {dict(ct[po_key])}\n"
        return s

    lines = []
    lines.append("# Path-Ordering Analysis\n")
    lines.append(f"**Дата:** 2026-03-27  \n**Данные:** all_trades.csv (v3 log, 367 сделок)  \n**OHLC:** XAUUSD_H1_OHLC.csv ({len(times)} баров)\n\n")
    lines.append("## Метод\n")
    lines.append("Для каждой сделки из TP_CLEAR/BOTH_HIT/SL_CLEAR: bar-by-bar scan H1 OHLC[bar+1..bar+12].\n")
    lines.append("Если High≥TP и Low≤SL в одном баре — порядок по Open: ближе к SL=SL_FIRST, иначе TP_FIRST.\n\n")
    lines.append("## Результаты\n\n")

    for cat in ['BOTH_HIT', 'TP_CLEAR', 'SL_CLEAR']:
        sub = [r for r in results if r['category'] == cat]
        lines.append(stats_for(cat, sub))
        lines.append("\n")

    lines.append("## Общий итог\n\n")
    all_decisive = [r for r in results if r['path_order'] in ('SL_FIRST', 'TP_FIRST')]
    sl_total = sum(1 for r in all_decisive if r['path_order'] == 'SL_FIRST')
    tp_total = sum(1 for r in all_decisive if r['path_order'] == 'TP_FIRST')
    lines.append(f"- SL_FIRST: {sl_total} ({100*sl_total/len(all_decisive):.0f}%)\n")
    lines.append(f"- TP_FIRST: {tp_total} ({100*tp_total/len(all_decisive):.0f}%)\n\n")

    # Диагноз: TP_CLEAR + SL_FIRST — сколько теряем из-за path?
    tp_clear_sl_first = [r for r in results
                         if r['category'] == 'TP_CLEAR' and r['path_order'] == 'SL_FIRST']
    lines.append(f"## Ключевой диагноз\n\n")
    lines.append(f"TP_CLEAR + SL_FIRST = **{len(tp_clear_sl_first)}** сделок — ")
    lines.append(f"модель права (TP достижим), но путь идёт через SL.\n")
    lines.append(f"Это основная цель для first-barrier-hit лейблинга.\n\n")

    # Consistency: path_order vs mt4_result
    consistent = sum(
        1 for r in results
        if (r['path_order'] == 'SL_FIRST' and 'LOSS' in r['mt4']) or
           (r['path_order'] == 'TP_FIRST' and 'WIN' in r['mt4'])
    )
    lines.append(f"## Консистентность path_order vs MT4\n\n")
    lines.append(f"Совпадение: {consistent}/{len(results)} = {100*consistent/len(results):.0f}%\n")
    lines.append("(Несовпадение = сделка закрыта по MARKET-таймауту до достижения SL/TP)\n")

    report = "".join(lines)
    print("\n" + report)

    with open(REPORT_OUT, 'w') as f:
        f.write(report)
    print(f"\nОтчёт сохранён: {REPORT_OUT}")

if __name__ == '__main__':
    main()
