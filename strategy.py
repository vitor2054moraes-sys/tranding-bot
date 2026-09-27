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

def signals(df):
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
