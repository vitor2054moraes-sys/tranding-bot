import numpy as np
import pandas as pd
import yfinance as yf
from config import *

def load():
    df = yf.download(SYMBOL, interval=INTERVAL, period=PERIOD,
                     progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df.tz_convert(TZ).dropna()

# ---------- Estratégia antiga (cruzamento de EMAs) ----------
def signals_ema(df):
    f = df["close"].ewm(span=EMA_FAST, adjust=False).mean()
    s = df["close"].ewm(span=EMA_SLOW, adjust=False).mean()
    tr = pd.concat([df.high - df.low,
                    (df.high - df.close.shift()).abs(),
                    (df.low  - df.close.shift()).abs()], axis=1).max(axis=1)
    df["ema_fast"], df["ema_slow"] = f, s
    df["atr"] = tr.rolling(ATR_LEN).mean()

    up = (f > s) & (f.diff() > 0) & (s.diff() > 0)
    dn = (f < s) & (f.diff() < 0) & (s.diff() < 0)
    df["trend"] = np.where(up, 1, np.where(dn, -1, 0))
    df["buy"]  = (df.trend == 1)  & (df.trend.shift() != 1)
    df["sell"] = (df.trend == -1) & (df.trend.shift() != -1)
    return df.dropna()

# ---------- Indicadores ----------
def rsi(close, n):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)

def mfi(df, n):
    tp = (df.high + df.low + df.close) / 3
    mf = tp * df.volume
    pos = mf.where(tp > tp.shift(), 0).rolling(n).sum()
    neg = mf.where(tp < tp.shift(), 0).rolling(n).sum()
    return 100 - 100 / (1 + pos / neg)

# ---------- Nova estratégia (compra no fundo) ----------
def signals(df):
    c = df.close
    df["ema_slow"] = c.ewm(span=EMA_SLOW, adjust=False).mean()
    tr = pd.concat([df.high - df.low,
                    (df.high - c.shift()).abs(),
                    (df.low - c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = tr.rolling(ATR_LEN).mean()
    df["rsi"] = rsi(c, RSI_LEN)

    has_vol = "volume" in df and df.volume.sum() > 0
    df["flow"] = mfi(df, MFI_LEN) if has_vol else df.rsi

    oversold_recent = df.rsi.rolling(3).min() < RSI_OVERSOLD
    df["entry"] = (c < df.ema_slow) & oversold_recent & \
                  (df.rsi > df.rsi.shift()) & (c > df.high.shift())
    df["flow_exit"] = (df.flow.shift() > MFI_HIGH) & (df.flow < df.flow.shift())
    return df.dropna()

# ---------- Backtest ----------
def backtest(df):
    trades, pos = [], None
    for t, r in df.iterrows():
        if pos is None:
            if r.entry:
                pos = dict(time=t, price=r.close,
                           sl=r.close - SL_ATR * r.atr,
                           tp=r.close + TP_ATR * r.atr)
            continue
        if r.low <= pos["sl"]:
            exit_p, why = pos["sl"], "stop_loss"
        elif r.high >= pos["tp"]:
            exit_p, why = pos["tp"], "stop_gain"
        elif r.flow_exit:
            exit_p, why = r.close, "fluxo"
        else:
            continue
        ret = exit_p / pos["price"] - 1 - 2 * COST
        trades.append(dict(entrada=pos["time"], saida=t, preco_ent=pos["price"],
                           preco_sai=exit_p, motivo=why, ret=ret))
        pos = None

    tr = pd.DataFrame(trades)
    if tr.empty:
        print("Nenhuma operação."); return tr

    eq = (1 + tr.ret).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    gains, losses = tr.ret[tr.ret > 0].sum(), -tr.ret[tr.ret < 0].sum()
    bh = df.close.iloc[-1] / df.close.iloc[0] - 1

    print(f"Operações:       {len(tr)}")
    print(f"Taxa de acerto:  {(tr.ret > 0).mean():.1%}")
    print(f"Retorno total:   {eq.iloc[-1] - 1:.2%}")
    print(f"Fator de lucro:  {gains / losses if losses else float('inf'):.2f}")
    print(f"Drawdown máx.:   {dd:.2%}")
    print(f"Buy & hold:      {bh:.2%}")
    print(tr.motivo.value_counts().to_string())
    return tr

if __name__ == "__main__":
    df = signals(load())
    trades = backtest(df)
    print(trades.tail(10))
