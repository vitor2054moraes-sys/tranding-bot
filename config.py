SYMBOL      = "USDBRL=X"
INTERVAL    = "15m"
PERIOD      = "10d"
EMA_FAST    = 8
EMA_SLOW    = 80
ATR_LEN     = 14
ATR_MULT    = 1.5    # stop = 1.5 x ATR
RISK_REWARD = 2.0    # alvo = 2 x stop
MAX_TRADES  = 3      # por dia

TZ          = "America/New_York"
OPEN        = (9, 30)
CLOSE       = (16, 0)
REPORT_END  = (17, 0)   # 1h após o fechamento para gerar o relatório

STATE_FILE  = "data/state.json"
TRADES_FILE = "data/trades.csv"
REPORT_DIR  = "reports"
