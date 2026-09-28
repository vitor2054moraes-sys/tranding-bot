import json, os
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
import pandas as pd
from config import *
from strategy import load, signals

NY = ZoneInfo(TZ)

def phase(now):
    if now.weekday() >= 5:
        return "off"
    t = now.time()
    if dtime(*OPEN) <= t < dtime(*CLOSE):       return "market"
    if dtime(*CLOSE) <= t < dtime(*REPORT_END): return "report"
    return "off"

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {"position": None, "day": "", "count": 0, "report_day": ""}

def save_state(s):
    os.makedirs("data", exist_ok=True)
    json.dump(s, open(STATE_FILE, "w"), indent=2, default=str)

def record(pos):
    os.makedirs("data", exist_ok=True)
    pd.DataFrame([pos]).to_csv(TRADES_FILE, mode="a",
        header=not os.path.exists(TRADES_FILE), index=False)

def close_pos(state, price, ts, result):
    p = state["position"]
    pnl = (price / p["entry"] - 1 - 2 * COST) * 100
    p.update(exit=round(price, 4), exit_ts=str(ts), result=result,
             pnl_pct=round(pnl, 4))
    record(p)
    print(f"{result} COMPRA @ {price:.4f} | {p['pnl_pct']}%")
    state["position"] = None

def check_position(state, df):
    """Percorre candles desde a entrada: stop loss, stop gain e saída por fluxo."""
    p = state["position"]
    last = df.index[-1]                      # candle em formação
    bars = df[df.index > pd.Timestamp(p["entry_ts"])]
    for ts, r in bars.iterrows():
        if r.low  <= p["stop"]:   return close_pos(state, p["stop"], ts, "STOP_LOSS")
        if r.high >= p["target"]: return close_pos(state, p["target"], ts, "STOP_GAIN")
        if ts != last and r.flow_exit:       # só candle FECHADO
            return close_pos(state, float(r.close), ts, "FLUXO")

def observe(state, df):
    if state["position"]:
        check_position(state, df)
    if state["position"] or state["count"] >= MAX_TRADES:
        return
    sig, cur = df.iloc[-2], df.iloc[-1]      # -2 = último candle FECHADO
    if not sig.entry:
        print(f"Sem sinal | {cur.close:.4f} | RSI {sig.rsi:.1f} | Fluxo {sig.flow:.1f}")
        return
    entry, atr = float(cur.open), float(sig.atr)
    state["position"] = dict(
        day=state["day"], side="COMPRA", entry_ts=str(cur.name),
        entry=round(entry, 4),
        stop=round(entry - SL_ATR * atr, 4),
        target=round(entry + TP_ATR * atr, 4))
    state["count"] += 1
    print(f"ENTRADA {state['position']}")

def report(state, df, today):
    if state["position"]:
        check_position(state, df)
    if state["position"]:
        close_pos(state, float(df.close.iloc[-1]), df.index[-1], "FECHAMENTO")

    d = df[(df.index.date == pd.Timestamp(today).date()) &
           (df.index.time >= dtime(*OPEN)) & (df.index.time < dtime(*CLOSE))]
    trades = pd.read_csv(TRADES_FILE) if os.path.exists(TRADES_FILE) else pd.DataFrame()
    if not trades.empty:
        trades = trades[trades.day == today]

    L = [f"# Relatório {SYMBOL} — {today}\n"]
    if not d.empty:
        L += [f"- Abertura: **{d.open.iloc[0]:.4f}** | Fechamento: **{d.close.iloc[-1]:.4f}**",
              f"- Máxima: {d.high.max():.4f} às {d.high.idxmax():%H:%M} | "
              f"Mínima: {d.low.min():.4f} às {d.low.idxmin():%H:%M}\n",
              "## Sinais (fundo / queda de fluxo)\n",
              "| Hora (NY) | Sinal | Preço | RSI | Fluxo |", "|---|---|---|---|---|"]
        for ts, r in d[d.entry | d.flow_exit].iterrows():
            L.append(f"| {ts:%H:%M} | {'🟢 COMPRA' if r.entry else '🔴 SAÍDA FLUXO'} "
                     f"| {r.close:.4f} | {r.rsi:.1f} | {r.flow:.1f} |")

    L += ["\n## Operações simuladas\n"]
    if trades.empty:
        L.append("Nenhuma operação hoje.")
    else:
        L.append(trades[["entry_ts", "entry", "stop", "target",
                         "exit", "result", "pnl_pct"]].to_markdown(index=False))
        L += [f"\n**Acerto:** {(trades.pnl_pct > 0).mean():.0%} | "
              f"**Resultado:** {trades.pnl_pct.sum():.3f}%"]

    txt = "\n".join(L)
    os.makedirs(REPORT_DIR, exist_ok=True)
    open(f"{REPORT_DIR}/{today}.md", "w").write(txt)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        open(os.environ["GITHUB_STEP_SUMMARY"], "a").write(txt)
    state["report_day"] = today
    print(txt)

def main():
    now = datetime.now(NY)
    ph = phase(now)
    print(f"{now:%Y-%m-%d %H:%M} NY | fase: {ph}")
    if ph == "off" and not os.getenv("FORCE"):
        return

    state = load_state()
    today = now.strftime("%Y-%m-%d")
    if state["day"] != today:
        state.update(day=today, count=0)

    df = signals(load())
    if ph == "market":
        observe(state, df)
    elif state["report_day"] != today or os.getenv("FORCE"):
        report(state, df, today)
    save_state(state)

if __name__ == "__main__":
    main()
