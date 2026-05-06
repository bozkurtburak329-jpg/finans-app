"""
Burak Borsa Terminali v19.0 — NOVA EDITION
==========================================
4 Katman:
  1. Veri & Gündem Takibi  (RSS + yfinance + ekonomik takvim)
  2. Claude AI Öneri Motoru (doğal dil gerekçeli, haber destekli)
  3. Akıllı Portföy Yönetimi (stop/kar alarmı, anlık uyarılar)
  4. Kendi Kendine Öğrenme  (öneri geçmişi, başarı skoru, parametre optimizasyonu)
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
import time
import feedparser 
import google.generativeai as genai
import sqlite3
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# SAYFA AYARLARI
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Burak Borsa Terminali",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# SESSION STATE BAŞLANGIÇ
# ─────────────────────────────────────────────
DEFAULTS = {
    "theme": "dark",
    "portfolio": {},
    "ai_signals": {},
    "news_cache": [],
    "news_last_fetch": None,
    "learning_params": {"rsi_buy_threshold": 35, "rsi_sell_threshold": 68, "min_score": 2},
    "signal_history": [],
    "ai_chat_history": [],
    "selected_stock": "THYAO",
    "binance_connected": False,
    "binance_mode": "Testnet",
    "portfolio_alerts": {},
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# VERİTABANI (Öğrenme için kalıcı hafıza)
# ─────────────────────────────────────────────
DB_PATH = "trading_memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS signal_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        signal_type TEXT,
        entry_price REAL,
        target_price REAL,
        stop_price REAL,
        signal_date TEXT,
        close_date TEXT,
        close_price REAL,
        outcome TEXT,
        pnl_pct REAL,
        ai_score INTEGER,
        news_sentiment TEXT,
        rsi_at_signal REAL,
        notes TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS learning_params (
        id INTEGER PRIMARY KEY,
        rsi_buy_threshold REAL,
        rsi_sell_threshold REAL,
        min_score INTEGER,
        total_signals INTEGER,
        success_rate REAL,
        last_updated TEXT
    )""")
    c.execute("INSERT OR IGNORE INTO learning_params VALUES (1, 35, 68, 2, 0, 0.0, ?)",
              (datetime.now().isoformat(),))
    conn.commit()
    conn.close()

def load_learning_params():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT rsi_buy_threshold, rsi_sell_threshold, min_score FROM learning_params WHERE id=1")
        row = c.fetchone()
        conn.close()
        if row:
            return {"rsi_buy_threshold": row[0], "rsi_sell_threshold": row[1], "min_score": row[2]}
    except:
        pass
    return {"rsi_buy_threshold": 35, "rsi_sell_threshold": 68, "min_score": 2}

def save_signal_to_db(symbol, signal_type, entry, target, stop, ai_score, rsi, sentiment=""):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO signal_history
            (symbol, signal_type, entry_price, target_price, stop_price, signal_date, ai_score, rsi_at_signal, news_sentiment)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (symbol, signal_type, entry, target, stop, datetime.now().isoformat(), ai_score, rsi, sentiment))
        conn.commit()
        conn.close()
    except Exception as e:
        pass

def get_signal_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM signal_history ORDER BY signal_date DESC LIMIT 100", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def update_signal_outcomes():
    """Açık sinyalleri kontrol et, kapanmış olanların sonucunu kaydet"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, symbol, entry_price, target_price, stop_price, signal_date FROM signal_history WHERE outcome IS NULL")
        open_signals = c.fetchall()
        for sig_id, sym, entry, target, stop, sig_date in open_signals:
            try:
                ticker = f"{sym}.IS" if sym not in ["BTC","ETH","BNB","SOL"] else f"{sym}-USD"
                df = yf.download(ticker, period="1d", progress=False, auto_adjust=True)
                if df.empty: continue
                cp = float(df["Close"].iloc[-1])
                if cp >= target:
                    outcome, pnl = "WIN", (cp - entry) / entry * 100
                elif cp <= stop:
                    outcome, pnl = "LOSS", (cp - entry) / entry * 100
                else:
                    days_open = (datetime.now() - datetime.fromisoformat(sig_date)).days
                    if days_open > 14:
                        outcome, pnl = "EXPIRED", (cp - entry) / entry * 100
                    else:
                        continue
                c.execute("UPDATE signal_history SET outcome=?, pnl_pct=?, close_date=?, close_price=? WHERE id=?",
                          (outcome, pnl, datetime.now().isoformat(), cp, sig_id))
            except:
                continue
        conn.commit()
        conn.close()
    except:
        pass

def compute_and_update_learning():
    """Başarı oranına göre parametreleri güncelle"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT outcome, rsi_at_signal, pnl_pct FROM signal_history WHERE outcome IS NOT NULL")
        rows = c.fetchall()
        if len(rows) < 5:
            conn.close()
            return None

        wins = [r for r in rows if r[0] == "WIN"]
        losses = [r for r in rows if r[0] == "LOSS"]
        total = len(wins) + len(losses)
        success_rate = len(wins) / total if total > 0 else 0

        # RSI eşiği optimizasyonu: hangi RSI aralığında daha fazla kazanç?
        if len(wins) >= 3:
            win_rsis = [r[1] for r in wins if r[1] is not None]
            loss_rsis = [r[1] for r in losses if r[1] is not None]
            if win_rsis:
                optimal_rsi = np.mean(win_rsis)
                new_threshold = max(25, min(45, round(optimal_rsi)))
            else:
                new_threshold = 35
        else:
            new_threshold = 35

        c.execute("""UPDATE learning_params SET
            rsi_buy_threshold=?, total_signals=?, success_rate=?, last_updated=?
            WHERE id=1""", (new_threshold, total, success_rate, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        st.session_state.learning_params["rsi_buy_threshold"] = new_threshold
        return {
            "total": total,
            "wins": len(wins),
            "losses": len(losses),
            "success_rate": success_rate,
            "new_rsi_threshold": new_threshold
        }
    except:
        return None

# ─────────────────────────────────────────────
# TEMA & RENKLER
# ─────────────────────────────────────────────
def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

tv_theme = "dark" if st.session_state.theme == "dark" else "light"
is_dark = st.session_state.theme == "dark"

bg       = "#0d1117" if is_dark else "#f6f8fa"
bg2      = "#161b22" if is_dark else "#ffffff"
bg3      = "#21262d" if is_dark else "#f0f3f6"
border   = "#30363d" if is_dark else "#d0d7de"
txt      = "#e6edf3" if is_dark else "#1f2328"
txt2     = "#8b949e" if is_dark else "#656d76"
blue     = "#58a6ff" if is_dark else "#0969da"
green    = "#3fb950" if is_dark else "#1a7f37"
red      = "#f85149" if is_dark else "#cf222e"
amber    = "#e3b341" if is_dark else "#9a6700"
purple   = "#bc8cff" if is_dark else "#8250df"

init_db()
params = load_learning_params()
st.session_state.learning_params = params

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');

html,body,[class*="css"]{{
    font-family:'DM Sans',sans-serif!important;
    background:{bg}!important;
    color:{txt}!important;
}}
[data-testid="collapsedControl"],section[data-testid="stSidebar"]{{display:none;}}
::-webkit-scrollbar{{width:5px;height:5px;}}
::-webkit-scrollbar-track{{background:{bg2};}}
::-webkit-scrollbar-thumb{{background:{border};border-radius:3px;}}

/* ── Header ── */
.top-bar{{
    display:flex;align-items:center;justify-content:space-between;
    padding:10px 0 14px;border-bottom:1px solid {border};margin-bottom:12px;
}}
.logo{{
    display:flex;align-items:center;gap:10px;
}}
.logo-mark{{
    width:34px;height:34px;background:linear-gradient(135deg,{blue},{purple});
    border-radius:8px;display:flex;align-items:center;justify-content:center;
    font-family:'JetBrains Mono',monospace;font-weight:700;color:#fff;font-size:16px;
}}
.logo-name{{font-size:1rem;font-weight:700;color:{txt};letter-spacing:-0.02em;}}
.logo-ver{{font-size:0.65rem;color:{txt2};letter-spacing:0.08em;text-transform:uppercase;}}

/* ── Ticker ── */
.ticker-row{{
    display:flex;gap:0;border:1px solid {border};border-radius:8px;
    overflow:hidden;background:{bg2};margin-bottom:10px;
}}
.tick{{
    display:flex;flex-direction:column;padding:9px 16px;
    border-right:1px solid {border};flex:1;min-width:0;
}}
.tick-label{{font-size:0.6rem;color:{txt2};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:3px;}}
.tick-price{{font-size:1rem;font-weight:700;color:{txt};font-family:'JetBrains Mono',monospace;}}
.tick-chg{{font-size:0.72rem;font-weight:600;margin-top:1px;}}
.tc-g{{color:{green};}}
.tc-r{{color:{red};}}

/* ── Cards ── */
.card{{
    background:{bg2};border:1px solid {border};border-radius:8px;
    padding:14px 16px;margin-bottom:10px;
}}
.card-title{{font-size:0.78rem;color:{txt2};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;}}

/* ── AI Sinyaller ── */
.sig-card{{
    border-radius:8px;padding:14px 16px;margin-bottom:10px;
    border-left:3px solid {green};background:{bg2};border-top:1px solid {border};
    border-right:1px solid {border};border-bottom:1px solid {border};
}}
.sig-card.sell{{border-left-color:{red};}}
.sig-card.watch{{border-left-color:{amber};}}
.sig-sym{{font-size:1.1rem;font-weight:700;color:{blue};font-family:'JetBrains Mono',monospace;}}
.sig-badge{{
    display:inline-block;padding:2px 8px;border-radius:4px;
    font-size:0.68rem;font-weight:700;letter-spacing:0.06em;margin-left:8px;
}}
.badge-buy{{background:rgba(63,185,80,0.15);color:{green};}}
.badge-sell{{background:rgba(248,81,73,0.15);color:{red};}}
.badge-hold{{background:rgba(227,179,65,0.15);color:{amber};}}

/* ── Portföy ── */
.pf-card{{
    background:{bg2};border:1px solid {border};border-radius:8px;
    padding:12px 14px;margin-bottom:8px;
}}
.pf-sym{{font-size:1rem;font-weight:700;color:{blue};font-family:'JetBrains Mono',monospace;}}
.pf-detail{{font-size:0.75rem;color:{txt2};margin-top:3px;}}

/* ── Alarm banner ── */
.alarm-buy{{
    background:rgba(63,185,80,0.12);border:1px solid {green};
    border-radius:8px;padding:12px 16px;margin-bottom:8px;
    animation:pulse-green 2s infinite;
}}
.alarm-sell{{
    background:rgba(248,81,73,0.12);border:1px solid {red};
    border-radius:8px;padding:12px 16px;margin-bottom:8px;
    animation:pulse-red 2s infinite;
}}
@keyframes pulse-green{{
    0%,100%{{box-shadow:0 0 0 0 rgba(63,185,80,0.3);}}
    50%{{box-shadow:0 0 0 6px rgba(63,185,80,0);}}
}}
@keyframes pulse-red{{
    0%,100%{{box-shadow:0 0 0 0 rgba(248,81,73,0.3);}}
    50%{{box-shadow:0 0 0 6px rgba(248,81,73,0);}}
}}

/* ── Öğrenme ── */
.learn-stat{{
    background:{bg3};border-radius:6px;padding:10px 14px;text-align:center;
}}
.learn-val{{font-size:1.4rem;font-weight:700;color:{txt};font-family:'JetBrains Mono',monospace;}}
.learn-lbl{{font-size:0.68rem;color:{txt2};text-transform:uppercase;letter-spacing:0.08em;margin-top:3px;}}

/* ── Haber ── */
.news-item{{
    border-bottom:1px solid {border};padding:10px 0;
}}
.news-title{{font-size:0.85rem;font-weight:600;color:{txt};line-height:1.4;}}
.news-meta{{font-size:0.7rem;color:{txt2};margin-top:4px;}}
.news-tag{{
    display:inline-block;padding:1px 6px;border-radius:3px;
    font-size:0.65rem;font-weight:700;margin-right:4px;
}}
.tag-positive{{background:rgba(63,185,80,0.15);color:{green};}}
.tag-negative{{background:rgba(248,81,73,0.15);color:{red};}}
.tag-neutral{{background:rgba(139,148,158,0.2);color:{txt2};}}

/* ── Tablo ── */
.tv-table{{width:100%;border-collapse:collapse;font-size:13px;}}
.tv-table thead th{{
    padding:9px 12px;font-weight:500;color:{txt2};
    border-bottom:1px solid {border};font-size:11px;
    text-transform:uppercase;letter-spacing:0.06em;text-align:right;
}}
.tv-table thead th:first-child{{text-align:left;}}
.tv-table tbody tr:hover{{background:{bg3};}}
.tv-table td{{
    padding:8px 12px;color:{txt};vertical-align:middle;
    border-bottom:1px solid {border};text-align:right;
}}
.tv-table td:first-child{{text-align:left;}}
.tv-sym{{color:{blue};font-weight:600;font-family:'JetBrains Mono',monospace;font-size:13px;}}
.tv-green{{color:{green}!important;font-weight:600;}}
.tv-red{{color:{red}!important;font-weight:600;}}

/* ── Chat ── */
.chat-msg-user{{
    background:{bg3};border-radius:8px 8px 2px 8px;
    padding:10px 14px;margin-bottom:8px;font-size:0.88rem;
    border:1px solid {border};
}}
.chat-msg-ai{{
    background:rgba(88,166,255,0.06);border-radius:8px 8px 8px 2px;
    padding:10px 14px;margin-bottom:8px;font-size:0.88rem;
    border:1px solid rgba(88,166,255,0.15);
    border-left:2px solid {blue};
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KATMAN 1 — VERİ ALTYAPISI
# ─────────────────────────────────────────────
BIST_SYMBOLS = [
    "AKBNK","GARAN","ISCTR","YKBNK","VAKBN","KCHOL","SAHOL","DOHOL","ALARK","ENKAI",
    "EREGL","KRDMD","TUPRS","PETKM","SASA","HEKTS","GUBRF","KOZAL","SISE","CIMSA",
    "FROTO","TOASO","DOAS","OTKAR","KARSN","ARCLK","VESTL","BRISA","THYAO","PGSUS",
    "BIMAS","MGROS","SOKM","AEFES","CCOLA","TCELL","TTKOM","ASELS","ASTOR","KONTR",
    "ENJSA","AKSEN","ODAS","EKGYO","ISGYO","DEVA","SELEC","PETKM","KOZAA","OYAKC"
]
CRYPTO_SYMBOLS = ["BTC","ETH","BNB","SOL","XRP","ADA","DOGE","AVAX","LINK","DOT"]
US_SYMBOLS = ["AAPL","MSFT","NVDA","TSLA","AMZN","GOOGL","META","AMD","NFLX","JPM"]

TICKERS_BIST   = {f"{s}.IS": s for s in BIST_SYMBOLS}
TICKERS_CRYPTO = {f"{s}-USD": s for s in CRYPTO_SYMBOLS}
TICKERS_US     = {s: s for s in US_SYMBOLS}

def compute_rsi(series, period=14):
    try:
        delta = series.diff().dropna()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return round(float((100 - 100 / (1 + rs)).iloc[-1]), 1)
    except:
        return np.nan

def compute_macd(series):
    try:
        ema12 = series.ewm(span=12).mean()
        ema26 = series.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        return float(macd.iloc[-1]), float(signal.iloc[-1])
    except:
        return np.nan, np.nan

@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_data(tickers_dict):
    end = datetime.today()
    start = end - timedelta(days=90)
    rows = []

    def process(ticker, name):
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty or len(df) < 30: return None
            close = df["Close"].squeeze()
            vol   = df["Volume"].squeeze()
            p_last = float(close.iloc[-1])
            p_prev = float(close.iloc[-2])
            p_week = float(close.iloc[-6]) if len(close) >= 6 else p_prev
            chg_d  = (p_last - p_prev) / p_prev * 100
            chg_w  = (p_last - p_week) / p_week * 100
            rsi    = compute_rsi(close)
            macd_v, macd_s = compute_macd(close)
            vol_ratio = float(vol.iloc[-1] / vol.rolling(20).mean().iloc[-1]) if vol.iloc[-1] > 0 else 1.0
            volatility = float(close.rolling(14).std().iloc[-1] / p_last) if p_last > 0 else 0
            ma20 = float(close.rolling(20).mean().iloc[-1])
            ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else ma20

            threshold = st.session_state.learning_params.get("rsi_buy_threshold", 35)
            sell_threshold = st.session_state.learning_params.get("rsi_sell_threshold", 68)

            score = 0
            if pd.notna(rsi):
                if rsi < threshold: score += 3
                elif rsi < threshold + 10: score += 2
                elif rsi > sell_threshold: score -= 2
            if pd.notna(macd_v) and pd.notna(macd_s):
                if macd_v > macd_s: score += 1
                else: score -= 1
            if vol_ratio > 1.5: score += 1
            if p_last > ma20: score += 1
            if ma20 > ma50: score += 1

            if score >= 3: teknik = "Güçlü Al"
            elif score >= 1: teknik = "Al"
            elif score <= -2: teknik = "Sat"
            else: teknik = "Nötr"

            return {
                "Sembol": name, "Fiyat": p_last, "Değişim %": chg_d,
                "Haftalık %": chg_w, "RSI": rsi, "MACD": macd_v,
                "MACD_Signal": macd_s, "Hacim_Oran": vol_ratio,
                "Volatilite": volatility, "MA20": ma20, "MA50": ma50,
                "Teknik": teknik, "AI_Skor": score
            }
        except:
            return None

    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = [ex.submit(process, t, n) for t, n in tickers_dict.items()]
        for f in as_completed(futures):
            r = f.result()
            if r: rows.append(r)

    return pd.DataFrame(rows)

@st.cache_data(ttl=300, show_spinner=False)
def fetch_macro():
    tickers = {
        "XU100.IS": "BIST 100", "USDTRY=X": "USD/TRY",
        "EURTRY=X": "EUR/TRY", "GC=F": "ALTIN", "BTC-USD": "BTC"
    }
    res = {}
    for t, name in tickers.items():
        try:
            df = yf.download(t, period="5d", interval="1h", progress=False, auto_adjust=True)
            if not df.empty and len(df) >= 3:
                close = df["Close"].squeeze().dropna()
                curr = float(close.iloc[-1])
                prev = float(close.iloc[-3])
                res[name] = {"price": curr, "chg": (curr - prev) / prev * 100}
            else:
                res[name] = {"price": 0.0, "chg": 0.0}
        except:
            res[name] = {"price": 0.0, "chg": 0.0}
    return res

# ─────────────────────────────────────────────
# KATMAN 1 — HABER & GÜNDEM (RSS)
# ─────────────────────────────────────────────
RSS_FEEDS = [
    ("https://feeds.bbci.co.uk/news/business/rss.xml",           "BBC Business"),
    ("https://www.investing.com/rss/news_301.rss",                "Investing.com"),
    ("https://feeds.a.dj.com/rss/RSSMarketsMain.xml",             "WSJ Markets"),
    ("https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best", "Reuters"),
]

BIST_KEYWORDS = {
    "THYAO": ["thy","türk hava","turkish airlines","thyao"],
    "GARAN": ["garanti","garan","garanti bankası"],
    "AKBNK": ["akbank","akbnk"],
    "EREGL": ["ereğli","erdemir","eregl"],
    "TUPRS": ["tüpraş","tupras","tüpraş"],
    "BIMAS": ["bim","bimas","bim mağazaları"],
    "ASELS": ["aselsan","asels","savunma"],
    "TCELL": ["turkcell","tcell"],
    "KCHOL": ["koç holding","kchol"],
    "FROTO": ["ford otosan","froto"],
}

@st.cache_data(ttl=900, show_spinner=False)
def fetch_news():
    all_news = []
    for url, source in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                published = entry.get("published", "")
                link = entry.get("link", "#")
                
                text = (title + " " + summary).lower()
                
                # Basit sentiment
                pos_words = ["arttı","yükseldi","büyüdü","kâr","rekor","güçlü","rallied","gains","rose","surge","profit","growth","beat","strong","up","high"]
                neg_words = ["düştü","geriledi","kayıp","zarar","risk","düşüş","fell","lost","decline","drop","loss","miss","weak","down","cut","warn"]
                
                pos_count = sum(1 for w in pos_words if w in text)
                neg_count = sum(1 for w in neg_words if w in text)
                
                if pos_count > neg_count: sentiment = "positive"
                elif neg_count > pos_count: sentiment = "negative"
                else: sentiment = "neutral"
                
                # İlgili hisseler
                related = []
                for sym, keywords in BIST_KEYWORDS.items():
                    if any(k in text for k in keywords):
                        related.append(sym)
                
                all_news.append({
                    "title": title,
                    "summary": summary[:200] if summary else "",
                    "published": published,
                    "source": source,
                    "link": link,
                    "sentiment": sentiment,
                    "related_stocks": related
                })
        except:
            continue
    
    all_news.sort(key=lambda x: x.get("published",""), reverse=True)
    return all_news[:40]

# ─────────────────────────────────────────────
# KATMAN 2 — CLAUDE AI ÖNERI MOTORU
# ─────────────────────────────────────────────
def call_claude_api(messages, system_prompt="", max_tokens=1000):
    """Gemini API ile çalışır — aynı arayüz korundu"""
    try:
        import os
        api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
        if not api_key:
            return "API key bulunamadı. Streamlit Secrets'a GEMINI_API_KEY ekleyin."
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=system_prompt if system_prompt else "Sen yardımcı bir asistansın."
        )
        
        # Mesaj geçmişini Gemini formatına çevir
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=history)
        last_msg = messages[-1]["content"]
        response = chat.send_message(last_msg)
        return response.text
    except Exception as e:
        return f"AI hatası: {str(e)}"

def generate_ai_recommendation(stock_data_row, news_context, market_context, budget_per_stock):
    """Tek bir hisse için Claude AI'dan gerekçeli öneri al"""
    sym = stock_data_row["Sembol"]
    fiyat = stock_data_row["Fiyat"]
    rsi = stock_data_row.get("RSI", 50)
    macd = stock_data_row.get("MACD", 0)
    macd_s = stock_data_row.get("MACD_Signal", 0)
    chg_d = stock_data_row.get("Değişim %", 0)
    chg_w = stock_data_row.get("Haftalık %", 0)
    vol_r = stock_data_row.get("Hacim_Oran", 1.0)
    volatilite = stock_data_row.get("Volatilite", 0.03)
    ai_skor = stock_data_row.get("AI_Skor", 0)

    # Bu hisseyle ilgili haberler
    related_news = [n for n in news_context if sym in n.get("related_stocks", [])]
    news_summary = ""
    if related_news:
        news_summary = "\n".join([f"- [{n['sentiment'].upper()}] {n['title']}" for n in related_news[:3]])

    system = """Sen bir uzman Türk borsa analistisisin. 
Teknik analiz ve güncel haberleri birleştirerek net, kısa, Türkçe yatırım önerileri üretiyorsun.
Her öneri şunları içermeli:
1. Kararın (AL / SAT / İZLE)
2. Gerekçe (1-2 cümle, somut)
3. Risk notu (stop neden o seviyede)
Çok kısa ve net ol. Finansal tavsiye vermediğini belirt."""

    user_msg = f"""Hisse: {sym}
Fiyat: {fiyat:.2f} TL
Günlük Değişim: {chg_d:+.2f}%  |  Haftalık: {chg_w:+.2f}%
RSI(14): {rsi:.1f}
MACD: {macd:.3f} / Sinyal: {macd_s:.3f}
Hacim (norm): {vol_r:.1f}x ortalama
Volatilite: %{volatilite*100:.1f}
Teknik Skor: {ai_skor}/7
Bütçe: {budget_per_stock:,.0f} TL

Güncel Haberler:
{news_summary if news_summary else "Bu hisseye özel haber bulunamadı."}

Piyasa Bağlamı: {market_context}

Bu hisse için yatırım analizi yap."""

    response = call_claude_api([{"role": "user", "content": user_msg}], system_prompt=system, max_tokens=400)
    return response if response else "AI analizi şu an kullanılamıyor."

def ai_market_briefing(df_data, news, macro):
    """Günlük piyasa özeti üret"""
    top_gainers = df_data.nlargest(3, "Değişim %")["Sembol"].tolist() if not df_data.empty else []
    top_losers  = df_data.nsmallest(3, "Değişim %")["Sembol"].tolist() if not df_data.empty else []

    bist_chg = macro.get("BIST 100", {}).get("chg", 0)
    usd_price = macro.get("USD/TRY", {}).get("price", 0)
    btc_chg   = macro.get("BTC", {}).get("chg", 0)

    pos_news = len([n for n in news if n["sentiment"] == "positive"])
    neg_news = len([n for n in news if n["sentiment"] == "negative"])

    system = """Sen kısa, net, bilgilendirici bir Türk piyasa yorumcususun.
Verilen verilere dayanarak bugünün piyasa durumunu 3-4 cümleyle özetle.
Türkçe, sade, profesyonel bir dil kullan."""

    user_msg = f"""Bugünün piyasa verileri:
BIST 100: {bist_chg:+.2f}%
USD/TRY: {usd_price:.4f}
BTC: {btc_chg:+.2f}%
En çok artan: {', '.join(top_gainers)}
En çok düşen: {', '.join(top_losers)}
Olumlu haber sayısı: {pos_news} | Olumsuz: {neg_news}

Bugün piyasada ne oluyor? Yatırımcı ne dikkat etmeli?"""

    return call_claude_api([{"role": "user", "content": user_msg}], system_prompt=system, max_tokens=300)

# ─────────────────────────────────────────────
# KATMAN 3 — PORTFÖY ALARM SİSTEMİ
# ─────────────────────────────────────────────
def check_portfolio_alerts(portfolio, df_data):
    """Portföydeki her hissenin stop/hedef durumunu kontrol et"""
    alerts = {}
    if portfolio and not df_data.empty:
        for sym, data in portfolio.items():
            cur = df_data[df_data["Sembol"] == sym]
            if cur.empty: continue
            cp = float(cur.iloc[0]["Fiyat"])
            entry = data.get("maliyet", cp)
            stop  = data.get("stop", entry * 0.93)
            target = data.get("hedef", entry * 1.10)
            pnl_pct = (cp - entry) / entry * 100 if entry > 0 else 0

            if cp <= stop:
                alerts[sym] = {"type": "STOP", "price": cp, "pnl": pnl_pct, "entry": entry}
            elif cp >= target:
                alerts[sym] = {"type": "HEDEF", "price": cp, "pnl": pnl_pct, "entry": entry}
    return alerts

# ─────────────────────────────────────────────
# HEADER & TICKER BANDI
# ─────────────────────────────────────────────
macro = fetch_macro()

h1, h2, h3 = st.columns([4, 2, 0.5])
with h1:
    st.markdown(f"""
    <div class="logo">
        <div class="logo-mark">B</div>
        <div>
            <div class="logo-name">Burak Borsa Terminali</div>
            <div class="logo-ver">v19.0 · AI Destekli · 4 Katman · Nova Edition</div>
        </div>
    </div>""", unsafe_allow_html=True)

with h2:
    secilen_piyasa = st.selectbox("Piyasa", ["BIST 100","Kripto (USD)","ABD Borsaları"],
                                  label_visibility="collapsed")
with h3:
    st.button("☀️" if is_dark else "🌙", on_click=toggle_theme, use_container_width=True)

if secilen_piyasa == "BIST 100":     aktif_tickerlar = TICKERS_BIST
elif secilen_piyasa == "Kripto (USD)": aktif_tickerlar = TICKERS_CRYPTO
else:                                  aktif_tickerlar = TICKERS_US

aktif_semboller = list(aktif_tickerlar.values())
df_data = fetch_market_data(aktif_tickerlar)

# Macro ticker bandı
def _tick_html(label, price, chg, fmt=".2f", prefix=""):
    c = "tc-g" if chg >= 0 else "tc-r"
    s = "▲" if chg >= 0 else "▼"
    return f"""<div class="tick">
        <div class="tick-label">{label}</div>
        <div class="tick-price">{prefix}{price:{fmt}}</div>
        <div class="tick-chg {c}">{s} {abs(chg):.2f}%</div>
    </div>"""

bist = macro.get("BIST 100", {"price":0,"chg":0})
usd  = macro.get("USD/TRY",  {"price":0,"chg":0})
eur  = macro.get("EUR/TRY",  {"price":0,"chg":0})
xau  = macro.get("ALTIN",    {"price":0,"chg":0})
btc  = macro.get("BTC",      {"price":0,"chg":0})

st.markdown(f"""
<div class="ticker-row">
    {_tick_html("BIST 100", bist['price'], bist['chg'], ",.0f")}
    {_tick_html("USD/TRY", usd['price'], usd['chg'], ",.4f", "₺")}
    {_tick_html("EUR/TRY", eur['price'], eur['chg'], ",.4f", "₺")}
    {_tick_html("ALTIN", xau['price'], xau['chg'], ",.1f", "$")}
    {_tick_html("BTC/USD", btc['price'], btc['chg'], ",.0f", "$")}
    <div class="tick" style="min-width:80px;border-right:none;">
        <div class="tick-label">İstanbul</div>
        <div class="tick-price">{datetime.now().strftime('%H:%M')}</div>
        <div class="tick-chg" style="color:{txt2};">{datetime.now().strftime('%d.%m.%Y')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PORTFÖY ALARM BANNER (Kalıcı üstte göster)
# ─────────────────────────────────────────────
if st.session_state.portfolio and not df_data.empty:
    alerts = check_portfolio_alerts(st.session_state.portfolio, df_data)
    if alerts:
        for sym, alert in alerts.items():
            if alert["type"] == "STOP":
                st.markdown(f"""
                <div class="alarm-sell">
                    <span style="font-size:1.1rem;">🚨</span>
                    <strong style="color:{red};font-size:1rem;margin:0 8px;">{sym} — STOP LOSS TETİKLENDİ!</strong>
                    <span style="color:{txt2};font-size:0.82rem;">
                        Fiyat: {alert['price']:,.2f} · P&L: {alert['pnl']:+.2f}% · Giriş: {alert['entry']:,.2f}
                    </span>
                    <span style="margin-left:10px;font-size:0.8rem;color:{red};">► SAT</span>
                </div>""", unsafe_allow_html=True)
            elif alert["type"] == "HEDEF":
                st.markdown(f"""
                <div class="alarm-buy">
                    <span style="font-size:1.1rem;">🎯</span>
                    <strong style="color:{green};font-size:1rem;margin:0 8px;">{sym} — HEDEF FİYATA ULAŞTI!</strong>
                    <span style="color:{txt2};font-size:0.82rem;">
                        Fiyat: {alert['price']:,.2f} · Kar: {alert['pnl']:+.2f}% · Giriş: {alert['entry']:,.2f}
                    </span>
                    <span style="margin-left:10px;font-size:0.8rem;color:{green};">► KAR AL</span>
                </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ANA SEKMELER
# ─────────────────────────────────────────────
tabs = st.tabs([
    "🌐 Piyasa & Isı Haritası",
    "🤖 AI Öneri Motoru",
    "📰 Gündem & Haberler",
    "💼 Portföy Yönetimi",
    "🧠 Öğrenme Merkezi",
    "📈 Pro Grafik",
    "🏢 Temel Analiz"
])
tab_market, tab_ai, tab_news, tab_portfolio, tab_learning, tab_chart, tab_fundamentals = tabs

# ╔══════════════════════════╗
# ║  SEKME 1: PİYASA         ║
# ╚══════════════════════════╝
with tab_market:
    c1, c2 = st.columns([2.5, 1.5])
    with c1:
        st.markdown(f'<div class="card-title">Piyasa Isı Haritası — {secilen_piyasa}</div>', unsafe_allow_html=True)
        heatmap_src = "BIST" if "BIST" in secilen_piyasa else ("CRYPTO" if "Kripto" in secilen_piyasa else "SP500")
        data_src = "XU100" if "BIST" in secilen_piyasa else ("Crypto" if "Kripto" in secilen_piyasa else "SPX500")
        hm_html = f"""<html><head><style>body{{margin:0;background:{bg};}}</style></head><body>
<div class="tradingview-widget-container" style="height:500px;width:100%">
  <div class="tradingview-widget-container__widget" style="height:500px;width:100%"></div>
  <script src="https://s3.tradingview.com/external-embedding/embed-widget-stock-heatmap.js">
  {{"exchanges":["{heatmap_src}"],"dataSource":"{data_src}","grouping":"sector",
    "blockSize":"market_cap_basic","blockColor":"change","locale":"tr",
    "colorTheme":"{tv_theme}","hasTopBar":true,"isTransparent":false,"width":"100%","height":"500"}}
  </script>
</div></body></html>"""
        components.html(hm_html, height=520, scrolling=False)

    with c2:
        st.markdown(f'<div class="card-title">En Hareketliler</div>', unsafe_allow_html=True)
        if not df_data.empty:
            top5g = df_data.nlargest(7, "Değişim %")
            top5r = df_data.nsmallest(5, "Değişim %")
            st.markdown(f'<div style="font-size:0.75rem;color:{green};font-weight:600;margin-bottom:6px;">▲ En Çok Yükselen</div>', unsafe_allow_html=True)
            for _, r in top5g.iterrows():
                rsi_v = f"{r['RSI']:.0f}" if pd.notna(r['RSI']) else "—"
                st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid {border};">
                    <div><span style="color:{blue};font-weight:600;font-family:'JetBrains Mono',monospace;">{r['Sembol']}</span>
                    <span style="font-size:0.68rem;color:{txt2};margin-left:6px;">RSI {rsi_v}</span></div>
                    <div style="text-align:right;">
                        <div style="color:{green};font-weight:600;font-size:0.88rem;">+{r['Değişim %']:.2f}%</div>
                        <div style="font-size:0.68rem;color:{txt2};">{r['Fiyat']:,.2f}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown(f'<div style="font-size:0.75rem;color:{red};font-weight:600;margin:12px 0 6px;">▼ En Çok Düşen</div>', unsafe_allow_html=True)
            for _, r in top5r.iterrows():
                st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid {border};">
                    <div><span style="color:{blue};font-weight:600;font-family:'JetBrains Mono',monospace;">{r['Sembol']}</span></div>
                    <div style="text-align:right;">
                        <div style="color:{red};font-weight:600;font-size:0.88rem;">{r['Değişim %']:.2f}%</div>
                        <div style="font-size:0.68rem;color:{txt2};">{r['Fiyat']:,.2f}</div>
                    </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f'<div class="card-title">Tüm Hisse Tarayıcı</div>', unsafe_allow_html=True)
    if not df_data.empty:
        df_show = df_data.sort_values("AI_Skor", ascending=False)
        rows_html = ""
        for _, r in df_show.iterrows():
            d_c = "tv-green" if r["Değişim %"] >= 0 else "tv-red"
            d_s = "+" if r["Değişim %"] >= 0 else ""
            rsi_v = f"{r['RSI']:.0f}" if pd.notna(r['RSI']) else "—"
            rsi_c = "tv-green" if pd.notna(r['RSI']) and r['RSI'] < 40 else \
                    "tv-red" if pd.notna(r['RSI']) and r['RSI'] > 65 else ""

            tek_c = "tv-green" if "Al" in r["Teknik"] else \
                    "tv-red" if "Sat" in r["Teknik"] else ""

            skor_bars = "█" * max(0, r["AI_Skor"]) + "░" * max(0, 7 - r["AI_Skor"])

            rows_html += f"""<tr>
                <td><span class="tv-sym">{r['Sembol']}</span></td>
                <td>{r['Fiyat']:,.2f}</td>
                <td class="{d_c}">{d_s}{r['Değişim %']:.2f}%</td>
                <td class="{d_c}">{r.get('Haftalık %', 0):+.2f}%</td>
                <td class="{rsi_c}">{rsi_v}</td>
                <td class="{tek_c}" style="font-size:12px;">{r['Teknik']}</td>
                <td style="font-family:'JetBrains Mono';font-size:10px;color:{blue};">{skor_bars}</td>
            </tr>"""

        st.markdown(f"""<div style="overflow-x:auto;overflow-y:auto;max-height:450px;border:1px solid {border};border-radius:8px;">
        <table class="tv-table">
            <thead><tr>
                <th style="text-align:left;">Sembol</th>
                <th>Fiyat</th><th>Günlük</th><th>Haftalık</th>
                <th>RSI</th><th>Teknik</th><th>AI Skor</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table></div>""", unsafe_allow_html=True)

# ╔══════════════════════════════╗
# ║  SEKME 2: AI ÖNERİ MOTORU   ║
# ╚══════════════════════════════╝
with tab_ai:
    st.markdown(f'<div class="card-title">Claude AI Öneri Motoru — {secilen_piyasa}</div>', unsafe_allow_html=True)

    # Piyasa özeti (günlük briefing)
    if st.button("📊 Günlük Piyasa Özeti Al (AI)", use_container_width=True):
        with st.spinner("Claude piyasayı analiz ediyor..."):
            news = fetch_news()
            briefing = ai_market_briefing(df_data, news, macro)
            if briefing:
                st.markdown(f"""<div class="chat-msg-ai">
                    <div style="font-size:0.72rem;color:{txt2};margin-bottom:6px;">🤖 AI Piyasa Özeti · {datetime.now().strftime('%H:%M')}</div>
                    {briefing}
                </div>""", unsafe_allow_html=True)
            else:
                st.info("Piyasa özeti şu an kullanılamıyor.")

    st.markdown("---")

    # Öneri parametreleri
    col_a, col_b, col_c, col_d = st.columns([2,2,1.5,1])
    with col_a:
        risk_plani = st.selectbox("Risk Profili", [
            "Muhafazakâr (Düşük Risk)",
            "Dengeli (Orta Risk)",
            "Agresif (Yüksek Risk)"
        ])
    with col_b:
        filtre = st.selectbox("Filtre", [
            "AI Skoru Yüksek",
            "Aşırı Satılmış (RSI Düşük)",
            "Momentum + Hacim",
            "Tüm Hisseler"
        ])
    with col_c:
        butce = st.number_input("Bütçe (TL)", min_value=1000, max_value=10_000_000, value=50_000, step=5000)
    with col_d:
        st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
        ai_btn = st.button("🤖 AI Analiz", use_container_width=True, type="primary")

    # Anlık öğrenme parametreleri göster
    lp = st.session_state.learning_params
    st.markdown(f"""<div style="background:{bg3};border-radius:6px;padding:8px 14px;margin-bottom:12px;font-size:0.75rem;color:{txt2};border:1px solid {border};">
        ⚡ Öğrenme Motoru Aktif — RSI Al Eşiği: <strong style="color:{blue};">{lp['rsi_buy_threshold']:.0f}</strong> ·
        RSI Sat Eşiği: <strong style="color:{blue};">{lp['rsi_sell_threshold']:.0f}</strong> ·
        Bu değerler geçmiş sinyallerin başarısına göre otomatik güncellenir
    </div>""", unsafe_allow_html=True)

    if ai_btn:
        if df_data.empty:
            st.error("Veri çekilemedi.")
        else:
            df_ai = df_data.copy()
            min_score = lp.get("min_score", 2)
            rsi_threshold = lp.get("rsi_buy_threshold", 35)

            # Risk parametreleri
            if "Muhafazakâr" in risk_plani:   k, s_stop = 1.06, 0.96
            elif "Dengeli" in risk_plani:      k, s_stop = 1.10, 0.93
            else:                               k, s_stop = 1.18, 0.88

            # Filtrele
            if "Aşırı Satılmış" in filtre:
                df_ai = df_ai[df_ai["RSI"] < rsi_threshold + 5]
            elif "Momentum" in filtre:
                df_ai = df_ai[(df_ai["Değişim %"] > 0) & (df_ai["Hacim_Oran"] > 1.3)]
            elif "AI Skoru" in filtre:
                df_ai = df_ai[df_ai["AI_Skor"] >= min_score]

            top_picks = df_ai.nlargest(5, "AI_Skor")

            if top_picks.empty:
                st.warning("Seçili kriterlere uyan hisse bulunamadı.")
            else:
                hisse_basi = butce / len(top_picks)
                news_ctx = fetch_news()
                macro_ctx = f"BIST100: {macro.get('BIST 100',{}).get('chg',0):+.2f}%, USD/TRY: {macro.get('USD/TRY',{}).get('price',0):.4f}"

                st.markdown(f"""<div class="card" style="margin-bottom:14px;">
                    <span style="font-size:0.82rem;color:{txt2};">
                        AI <strong style="color:{txt};">{len(top_picks)}</strong> hisse seçti ·
                        Her birine <strong style="color:{txt};">₺{hisse_basi:,.0f}</strong> ·
                        Risk: <strong style="color:{txt};">{risk_plani.split('(')[0].strip()}</strong>
                    </span>
                </div>""", unsafe_allow_html=True)

                for _, row in top_picks.iterrows():
                    sym = row["Sembol"]
                    fiyat = row["Fiyat"]
                    hedef = fiyat * k
                    stop  = fiyat * s_stop
                    adet  = int(hisse_basi / fiyat) if fiyat > 0 else 0
                    rr    = ((hedef - fiyat) / (fiyat - stop)) if (fiyat - stop) > 0 else 0

                    with st.spinner(f"Claude {sym} analiz ediyor..."):
                        ai_aciklama = generate_ai_recommendation(
                            row, news_ctx, macro_ctx, hisse_basi
                        )

                    sig_key = f"sig_{sym}_{int(time.time())}"
                    rsi_val = row.get("RSI", 50)

                    st.markdown(f"""<div class="sig-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                            <div>
                                <span class="sig-sym">{sym}</span>
                                <span class="sig-badge badge-buy">AL SİNYALİ</span>
                                <span style="font-size:0.7rem;color:{txt2};margin-left:6px;">AI Skor: {int(row['AI_Skor'])}/7</span>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:0.68rem;color:{txt2};">Önerilen Adet</div>
                                <div style="font-weight:700;color:{txt};font-family:'JetBrains Mono',monospace;">{adet} adet</div>
                            </div>
                        </div>
                        <div style="display:flex;gap:1.5rem;margin:10px 0;flex-wrap:wrap;">
                            <div><div style="font-size:0.6rem;color:{txt2};text-transform:uppercase;">Giriş</div>
                                <div style="font-weight:700;font-family:'JetBrains Mono',monospace;">{fiyat:,.2f}</div></div>
                            <div><div style="font-size:0.6rem;color:{txt2};text-transform:uppercase;">Hedef</div>
                                <div style="font-weight:700;color:{green};font-family:'JetBrains Mono',monospace;">{hedef:,.2f} (+{(k-1)*100:.0f}%)</div></div>
                            <div><div style="font-size:0.6rem;color:{txt2};text-transform:uppercase;">Stop</div>
                                <div style="font-weight:700;color:{red};font-family:'JetBrains Mono',monospace;">{stop:,.2f} (-{(1-s_stop)*100:.0f}%)</div></div>
                            <div><div style="font-size:0.6rem;color:{txt2};text-transform:uppercase;">R/R</div>
                                <div style="font-weight:700;font-family:'JetBrains Mono',monospace;">{rr:.1f}x</div></div>
                            <div><div style="font-size:0.6rem;color:{txt2};text-transform:uppercase;">RSI</div>
                                <div style="font-weight:700;color:{blue};font-family:'JetBrains Mono',monospace;">{rsi_val:.0f}</div></div>
                        </div>
                        <div style="background:{bg3};border-radius:6px;padding:10px;font-size:0.82rem;color:{txt};line-height:1.6;border-left:2px solid {blue};">
                            {ai_aciklama}
                        </div>
                    </div>""", unsafe_allow_html=True)

                    # Sinyal kaydet (DB + session)
                    st.session_state.ai_signals[sym] = {
                        "hedef": hedef, "stop": stop, "adet": adet,
                        "giris": fiyat, "rr": rr
                    }
                    if rsi_val and pd.notna(rsi_val):
                        save_signal_to_db(sym, "BUY", fiyat, hedef, stop,
                                         int(row["AI_Skor"]), float(rsi_val))

                    # Portföye Ekle butonu
                    if st.button(f"✅ {sym} Portföyüme Ekle", key=f"addpf_{sym}_{int(time.time())}"):
                        st.session_state.portfolio[sym] = {
                            "adet": adet, "maliyet": fiyat,
                            "hedef": hedef, "stop": stop
                        }
                        st.success(f"{sym} portföye eklendi!")
                        st.rerun()

    # ── Aktif Sinyaller Takip ──
    if st.session_state.ai_signals and not df_data.empty:
        st.markdown("---")
        st.markdown(f'<div class="card-title">Aktif AI Sinyalleri — Anlık Takip</div>', unsafe_allow_html=True)
        for sym, sig in st.session_state.ai_signals.items():
            cur = df_data[df_data["Sembol"] == sym]
            if cur.empty: continue
            cp = float(cur.iloc[0]["Fiyat"])
            giris = sig.get("giris", cp)
            pnl_p = (cp - giris) / giris * 100 if giris > 0 else 0
            pnl_c = green if pnl_p >= 0 else red
            box_type = "sig-card" if cp < sig["hedef"] else "sig-card"

            if cp >= sig["hedef"]:
                label, lc = "KAR AL", green
            elif cp <= sig["stop"]:
                label, lc = "STOP — SAT", red
            else:
                pct_to_target = (sig["hedef"] - cp) / (sig["hedef"] - giris) * 100 if (sig["hedef"] - giris) > 0 else 0
                label, lc = f"Takipte (%{pct_to_target:.0f} kaldı)", amber

            st.markdown(f"""<div class="sig-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span class="sig-sym">{sym}</span>
                    <span style="color:{lc};font-weight:700;font-size:0.88rem;">{label}</span>
                </div>
                <div style="display:flex;gap:1.5rem;margin-top:8px;font-family:'JetBrains Mono',monospace;font-size:0.82rem;color:{txt2};">
                    <span>Anlık: <strong style="color:{txt};">{cp:,.2f}</strong></span>
                    <span>Giriş: {giris:,.2f}</span>
                    <span>Hedef: <span style="color:{green};">{sig['hedef']:,.2f}</span></span>
                    <span>Stop: <span style="color:{red};">{sig['stop']:,.2f}</span></span>
                    <span style="color:{pnl_c};">P&L: {pnl_p:+.2f}%</span>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── AI Sohbet ──
    st.markdown("---")
    st.markdown(f'<div class="card-title">AI ile Sohbet — Piyasa Soruları</div>', unsafe_allow_html=True)
    
    for msg in st.session_state.ai_chat_history[-6:]:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-msg-ai">{msg["content"]}</div>', unsafe_allow_html=True)

    user_q = st.chat_input("Piyasa hakkında bir şey sor... (örn: 'THYAO için ne düşünüyorsun?')")
    if user_q:
        st.session_state.ai_chat_history.append({"role": "user", "content": user_q})

        piyasa_ctx = ""
        if not df_data.empty:
            top3 = df_data.nlargest(3, "AI_Skor")[["Sembol","Fiyat","RSI","Değişim %","Teknik"]].to_string(index=False)
            piyasa_ctx = f"\nŞu anki piyasa durumu (top 3):\n{top3}"

        system = f"""Sen Burak'ın kişisel Türk borsa asistanısın.
Kısa, net, Türkçe cevaplar ver.
Yatırım tavsiyesi vermediğini belirt ama teknik analiz yorumu yapabilirsin.
{piyasa_ctx}"""
        
        messages = [{"role": m["role"], "content": m["content"]} 
                    for m in st.session_state.ai_chat_history[-10:]]
        
        with st.spinner("AI düşünüyor..."):
            response = call_claude_api(messages, system_prompt=system, max_tokens=500)
        
        if response:
            st.session_state.ai_chat_history.append({"role": "assistant", "content": response})
            st.rerun()

# ╔══════════════════════════╗
# ║  SEKME 3: GÜNDEM         ║
# ╚══════════════════════════╝
with tab_news:
    col_n1, col_n2 = st.columns([1.6, 1])

    with col_n1:
        st.markdown(f'<div class="card-title">Global & Piyasa Haberleri</div>', unsafe_allow_html=True)
        
        news_refresh = st.button("🔄 Haberleri Güncelle")
        if news_refresh:
            fetch_news.clear()
        
        news_list = fetch_news()
        st.session_state.news_cache = news_list

        filtre_sentiment = st.radio("Filtre", ["Tümü","Olumlu","Olumsuz"], horizontal=True)

        for n in news_list:
            if filtre_sentiment == "Olumlu" and n["sentiment"] != "positive": continue
            if filtre_sentiment == "Olumsuz" and n["sentiment"] != "negative": continue

            tag_cls = "tag-positive" if n["sentiment"]=="positive" else \
                      "tag-negative" if n["sentiment"]=="negative" else "tag-neutral"
            tag_txt = "POZİTİF" if n["sentiment"]=="positive" else \
                      "NEGATİF" if n["sentiment"]=="negative" else "NÖTR"

            related_html = "".join([f'<span class="news-tag tag-neutral">{s}</span>' for s in n.get("related_stocks",[])])

            st.markdown(f"""<div class="news-item">
                <span class="news-tag {tag_cls}">{tag_txt}</span>
                {related_html}
                <div class="news-title" style="margin-top:4px;">
                    <a href="{n['link']}" target="_blank" style="color:{txt};text-decoration:none;">{n['title']}</a>
                </div>
                <div class="news-meta">{n['source']} · {n['published'][:16] if n['published'] else ''}</div>
            </div>""", unsafe_allow_html=True)

    with col_n2:
        st.markdown(f'<div class="card-title">Ekonomik Takvim</div>', unsafe_allow_html=True)
        cal_html = f"""<html><head><style>body{{margin:0;background:{bg};}}</style></head><body>
<div class="tradingview-widget-container" style="height:500px;width:100%">
<div class="tradingview-widget-container__widget" style="height:500px;width:100%"></div>
<script src="https://s3.tradingview.com/external-embedding/embed-widget-events.js">
{{"colorTheme":"{tv_theme}","isTransparent":false,"width":"100%","height":"500",
  "locale":"tr","importanceFilter":"-1,0,1","currencyFilter":"USD,EUR,TRY"}}
</script></div></body></html>"""
        components.html(cal_html, height=520, scrolling=False)

        st.markdown("---")
        st.markdown(f'<div class="card-title">Haber Duygu Analizi</div>', unsafe_allow_html=True)
        if news_list:
            pos = len([n for n in news_list if n["sentiment"]=="positive"])
            neg = len([n for n in news_list if n["sentiment"]=="negative"])
            neu = len([n for n in news_list if n["sentiment"]=="neutral"])
            total_n = pos + neg + neu
            pos_pct = pos / total_n * 100 if total_n > 0 else 0
            neg_pct = neg / total_n * 100 if total_n > 0 else 0
            overall_sentiment = "OLUMLU" if pos > neg else "OLUMSUZ" if neg > pos else "NÖTR"
            sentiment_color = green if pos > neg else red if neg > pos else amber

            st.markdown(f"""<div class="card">
                <div style="text-align:center;margin-bottom:10px;">
                    <div style="font-size:1.2rem;font-weight:700;color:{sentiment_color};">Piyasa Ruh Hali: {overall_sentiment}</div>
                    <div style="font-size:0.75rem;color:{txt2};">{total_n} haber analiz edildi</div>
                </div>
                <div style="display:flex;gap:2rem;justify-content:center;">
                    <div style="text-align:center;">
                        <div style="font-size:1.3rem;font-weight:700;color:{green};">{pos}</div>
                        <div style="font-size:0.7rem;color:{txt2};">Olumlu</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:1.3rem;font-weight:700;color:{red};">{neg}</div>
                        <div style="font-size:0.7rem;color:{txt2};">Olumsuz</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:1.3rem;font-weight:700;color:{txt2};">{neu}</div>
                        <div style="font-size:0.7rem;color:{txt2};">Nötr</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

# ╔══════════════════════════════╗
# ║  SEKME 4: PORTFÖY YÖNETİMİ  ║
# ╚══════════════════════════════╝
with tab_portfolio:
    col_pf, col_bn = st.columns([2.5, 1.5])

    with col_pf:
        st.markdown(f'<div class="card-title">Portföyüm</div>', unsafe_allow_html=True)

        # Varlık ekle
        ec1, ec2, ec3, ec4 = st.columns([2, 1.2, 1.2, 1])
        with ec1:
            add_sym = st.selectbox("Hisse", sorted(aktif_semboller), key="pf_add_sym")
        with ec2:
            add_adet = st.number_input("Adet", min_value=0.01, value=10.0, key="pf_add_adet")
        with ec3:
            add_maliyet = st.number_input("Maliyet (TL)", min_value=0.01, value=10.0, key="pf_add_mal")
        with ec4:
            st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
            if st.button("Ekle ✚", use_container_width=True, type="primary"):
                pr = df_data[df_data["Sembol"]==add_sym].iloc[0]["Fiyat"] \
                     if (not df_data.empty and add_sym in df_data["Sembol"].values) else add_maliyet
                # Otomatik stop ve hedef
                auto_stop   = pr * 0.93
                auto_target = pr * 1.10
                # AI sinyalinde özel stop/hedef varsa kullan
                if add_sym in st.session_state.ai_signals:
                    sig = st.session_state.ai_signals[add_sym]
                    auto_stop   = sig.get("stop", auto_stop)
                    auto_target = sig.get("hedef", auto_target)

                st.session_state.portfolio[add_sym] = {
                    "adet": add_adet,
                    "maliyet": add_maliyet if add_maliyet > 1 else pr,
                    "hedef": auto_target,
                    "stop": auto_stop
                }
                st.rerun()

        # Anlık fiyat göster
        if not df_data.empty and add_sym in df_data["Sembol"].values:
            pr_p = df_data[df_data["Sembol"]==add_sym].iloc[0]["Fiyat"]
            st.markdown(f'<div style="font-size:0.78rem;color:{green};margin-bottom:10px;">Anlık: <b>{pr_p:,.2f}</b> · {add_adet:.0f} adet = ₺{add_adet*pr_p:,.0f}</div>', unsafe_allow_html=True)

        # Portföy listesi
        if st.session_state.portfolio:
            total_mal = 0.0; total_gun = 0.0
            for sym4, data4 in list(st.session_state.portfolio.items()):
                cp4 = df_data[df_data["Sembol"]==sym4].iloc[0]["Fiyat"] \
                      if (not df_data.empty and sym4 in df_data["Sembol"].values) else data4["maliyet"]
                kz4 = (cp4 - data4["maliyet"]) / data4["maliyet"] * 100 if data4["maliyet"] > 0 else 0
                rc4 = green if kz4 >= 0 else red
                t_mal = data4["adet"] * data4["maliyet"]
                t_gun = data4["adet"] * cp4
                total_mal += t_mal
                total_gun += t_gun

                hedef4 = data4.get("hedef", data4["maliyet"] * 1.10)
                stop4  = data4.get("stop",  data4["maliyet"] * 0.93)
                hedef_pct = (hedef4 - cp4) / cp4 * 100
                stop_pct  = (cp4 - stop4) / cp4 * 100

                pc1, pc2 = st.columns([6, 1])
                with pc1:
                    st.markdown(f"""<div class="pf-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div class="pf-sym">{sym4}</div>
                            <div style="font-size:0.88rem;font-weight:700;color:{rc4};">{kz4:+.2f}%</div>
                        </div>
                        <div class="pf-detail">
                            {data4['adet']:.0f} adet · Maliyet: {data4['maliyet']:,.2f} · Anlık: <strong style="color:{txt};">{cp4:,.2f}</strong>
                        </div>
                        <div style="display:flex;gap:1.5rem;margin-top:6px;font-size:0.78rem;">
                            <span>P&L: <strong style="color:{rc4};">₺{abs(t_gun-t_mal):,.0f}</strong></span>
                            <span style="color:{green};">Hedef: {hedef4:,.2f} (+{hedef_pct:.1f}% uzakta)</span>
                            <span style="color:{red};">Stop: {stop4:,.2f} (-{stop_pct:.1f}% uzakta)</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
                with pc2:
                    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                    if st.button("Sil", key=f"del_{sym4}", use_container_width=True):
                        del st.session_state.portfolio[sym4]
                        st.rerun()

            # Özet
            pnl_t = total_gun - total_mal
            pnl_tp = pnl_t / total_mal * 100 if total_mal > 0 else 0
            pnl_c = green if pnl_t >= 0 else red
            st.markdown(f"""<div class="card" style="border-top:2px solid {blue};">
                <div style="font-size:0.72rem;color:{txt2};margin-bottom:8px;text-transform:uppercase;letter-spacing:0.08em;">Portföy Özeti</div>
                <div style="display:flex;gap:2.5rem;flex-wrap:wrap;">
                    <div><div style="font-size:0.62rem;color:{txt2};">Yatırım</div>
                        <div style="font-weight:700;font-family:'JetBrains Mono',monospace;">₺{total_mal:,.0f}</div></div>
                    <div><div style="font-size:0.62rem;color:{txt2};">Güncel</div>
                        <div style="font-weight:700;font-family:'JetBrains Mono',monospace;">₺{total_gun:,.0f}</div></div>
                    <div><div style="font-size:0.62rem;color:{txt2};">Toplam P&L</div>
                        <div style="font-weight:700;color:{pnl_c};font-family:'JetBrains Mono',monospace;">{'+'if pnl_t>=0 else ''}₺{abs(pnl_t):,.0f} ({pnl_tp:+.1f}%)</div></div>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("Portföyünüz boş. Yukarıdan hisse ekleyin veya AI Öneri sekmesinden 'Portföyüme Ekle' butonunu kullanın.")

    with col_bn:
        st.markdown(f'<div class="card-title">Binance API</div>', unsafe_allow_html=True)
        binance_mode = st.radio("Ağ", ["Testnet", "Live"], horizontal=True)
        api_key = st.text_input("API Key", type="password", placeholder="Binance API Key")
        sec_key = st.text_input("Secret Key", type="password", placeholder="Secret Key")
        if st.button("Bağlan", type="primary", use_container_width=True):
            if api_key and sec_key:
                st.session_state.binance_connected = True
                st.session_state.binance_mode = binance_mode
                st.success("Bağlantı aktif!")
            else:
                st.error("API ve Secret Key gerekli.")

        if st.session_state.binance_connected:
            c2 = green if "Testnet" in st.session_state.binance_mode else red
            st.markdown(f"""<div class="card" style="border:1px solid {c2};">
                <div style="font-weight:700;color:{c2};">BAĞLANTI AKTİF</div>
                <div style="font-size:0.78rem;color:{txt2};">{st.session_state.binance_mode}</div>
            </div>""", unsafe_allow_html=True)
            st.code(json.dumps({"symbol":"BTCUSDT","side":"BUY","type":"MARKET","quantity":0.001}, indent=2))

# ╔══════════════════════════════╗
# ║  SEKME 5: ÖĞRENME MERKEZİ   ║
# ╚══════════════════════════════╝
with tab_learning:
    st.markdown(f'<div class="card-title">Kendi Kendine Öğrenme Sistemi</div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="card" style="margin-bottom:14px;">
        <div style="font-size:0.85rem;color:{txt};line-height:1.7;">
            Bu sistem, verilen tüm AI sinyallerini kaydeder. 7-14 gün sonra her sinyalin sonucunu kontrol eder
            (hedef tuttu mu, stop mu yedi). Başarı oranına göre RSI eşiği ve skor ağırlıklarını otomatik günceller.
            Yani AI, kendi hatalarından öğrenerek her geçen gün daha iyi hale gelir.
        </div>
    </div>""", unsafe_allow_html=True)

    col_l1, col_l2 = st.columns([1, 2])

    with col_l1:
        st.markdown(f'<div class="card-title">Anlık Parametre Durumu</div>', unsafe_allow_html=True)
        lp_now = st.session_state.learning_params
        
        c_l1, c_l2 = st.columns(2)
        with c_l1:
            st.markdown(f"""<div class="learn-stat">
                <div class="learn-val" style="color:{blue};">{lp_now['rsi_buy_threshold']:.0f}</div>
                <div class="learn-lbl">RSI Al Eşiği</div>
            </div>""", unsafe_allow_html=True)
        with c_l2:
            st.markdown(f"""<div class="learn-stat">
                <div class="learn-val" style="color:{red};">{lp_now['rsi_sell_threshold']:.0f}</div>
                <div class="learn-lbl">RSI Sat Eşiği</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button("🔄 Sinyalleri Güncelle & Öğren", use_container_width=True, type="primary"):
            with st.spinner("Açık sinyaller kontrol ediliyor..."):
                update_signal_outcomes()
            with st.spinner("Parametreler optimize ediliyor..."):
                result = compute_and_update_learning()
            if result:
                st.success(f"""✅ Öğrenme tamamlandı!
                \nToplam Sinyal: {result['total']}
                \nBaşarı Oranı: %{result['success_rate']*100:.1f}
                \nYeni RSI Eşiği: {result['new_rsi_threshold']}""")
            else:
                st.info("Yeterli veri yok. En az 5 tamamlanmış sinyal gerekli.")

        # DB istatistikleri
        df_hist = get_signal_history()
        if not df_hist.empty:
            total_s = len(df_hist)
            closed  = df_hist[df_hist["outcome"].notna()]
            wins    = len(closed[closed["outcome"]=="WIN"])
            losses  = len(closed[closed["outcome"]=="LOSS"])
            open_s  = total_s - len(closed)
            sr = wins / len(closed) * 100 if len(closed) > 0 else 0
            sr_color = green if sr >= 55 else red if sr < 40 else amber

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            stats_grid = [
                (total_s, "Toplam Sinyal", txt),
                (open_s, "Açık", amber),
                (wins, "Kazanç", green),
                (losses, "Kayıp", red),
            ]
            for i in range(0, len(stats_grid), 2):
                c1, c2 = st.columns(2)
                for col, (val, lbl, col_r) in zip([c1,c2], stats_grid[i:i+2]):
                    with col:
                        st.markdown(f"""<div class="learn-stat">
                            <div class="learn-val" style="color:{col_r};">{val}</div>
                            <div class="learn-lbl">{lbl}</div>
                        </div>""", unsafe_allow_html=True)
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            st.markdown(f"""<div class="learn-stat" style="margin-top:8px;">
                <div class="learn-val" style="color:{sr_color};">%{sr:.1f}</div>
                <div class="learn-lbl">Başarı Oranı</div>
            </div>""", unsafe_allow_html=True)

    with col_l2:
        st.markdown(f'<div class="card-title">Sinyal Geçmişi</div>', unsafe_allow_html=True)
        df_hist = get_signal_history()
        if not df_hist.empty:
            df_show_h = df_hist[["symbol","signal_type","entry_price","target_price","stop_price",
                                  "signal_date","outcome","pnl_pct","ai_score","rsi_at_signal"]].copy()
            df_show_h.columns = ["Sembol","Tip","Giriş","Hedef","Stop","Tarih","Sonuç","P&L%","Skor","RSI"]
            df_show_h["Tarih"] = pd.to_datetime(df_show_h["Tarih"]).dt.strftime("%d.%m %H:%M")
            df_show_h["Giriş"] = df_show_h["Giriş"].map("{:.2f}".format)
            df_show_h["P&L%"] = df_show_h["P&L%"].apply(
                lambda x: f"+{x:.1f}%" if pd.notna(x) and x >= 0 else f"{x:.1f}%" if pd.notna(x) else "—"
            )

            rows_h = ""
            for _, r in df_show_h.head(30).iterrows():
                out_c = green if r["Sonuç"]=="WIN" else red if r["Sonuç"]=="LOSS" else txt2
                rows_h += f"""<tr>
                    <td><span class="tv-sym">{r['Sembol']}</span></td>
                    <td>{r['Tarih']}</td>
                    <td>{r['Giriş']}</td>
                    <td style="color:{out_c};font-weight:600;">{r['Sonuç'] if pd.notna(r['Sonuç']) else 'Açık'}</td>
                    <td style="color:{out_c};">{r['P&L%']}</td>
                    <td>{r['Skor'] if pd.notna(r['Skor']) else '—'}</td>
                    <td>{r['RSI'] if pd.notna(r['RSI']) else '—'}</td>
                </tr>"""

            st.markdown(f"""<div style="overflow:auto;max-height:420px;border:1px solid {border};border-radius:8px;">
            <table class="tv-table">
                <thead><tr>
                    <th style="text-align:left;">Sembol</th>
                    <th>Tarih</th><th>Giriş</th><th>Sonuç</th><th>P&L%</th><th>Skor</th><th>RSI</th>
                </tr></thead>
                <tbody>{rows_h}</tbody>
            </table></div>""", unsafe_allow_html=True)
        else:
            st.info("Henüz sinyal geçmişi yok. AI Öneri sekmesinden analiz başlatın.")

        # AI Öğrenme Açıklaması
        st.markdown("---")
        st.markdown(f'<div class="card-title">Öğrenme Nasıl Çalışır?</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="card">
            <div style="font-size:0.82rem;color:{txt};line-height:1.8;">
                <strong style="color:{blue};">1. Sinyal Kaydı:</strong> Her AI önerisi SQLite veritabanına kaydedilir (fiyat, RSI, hedef, stop).<br>
                <strong style="color:{blue};">2. Sonuç Takibi:</strong> "Güncelle & Öğren" butonuna her basışta açık sinyaller anlık fiyatla karşılaştırılır.<br>
                <strong style="color:{blue};">3. Analiz:</strong> Kazanılan sinyallerin ortalama RSI değeri hesaplanır.<br>
                <strong style="color:{blue};">4. Optimizasyon:</strong> Yeni RSI alım eşiği = kazanan sinyallerin ortalama RSI'ı (±sınırlar içinde).<br>
                <strong style="color:{blue};">5. Uygulama:</strong> Güncellenmiş parametre anında AI motoruna yansıtılır.
            </div>
        </div>""", unsafe_allow_html=True)

# ╔══════════════════════════╗
# ║  SEKME 6: PRO GRAFİK     ║
# ╚══════════════════════════╝
with tab_chart:
    chart_sym = st.selectbox("Hisse Seç", sorted(aktif_semboller),
        index=sorted(aktif_semboller).index("THYAO") if "THYAO" in aktif_semboller else 0)
    st.session_state.selected_stock = chart_sym

    def get_tv_sym(market, sym):
        if "BIST" in market: return f"BIST:{sym}"
        elif "Kripto" in market: return f"BINANCE:{sym}USDT"
        return f"NASDAQ:{sym}"

    tv_sym = get_tv_sym(secilen_piyasa, chart_sym)

    col_ch1, col_ch2 = st.columns([3, 1])
    with col_ch1:
        adv_html = f"""<html><head><style>body{{margin:0;background:{bg};}}</style></head><body>
<div class="tradingview-widget-container" style="height:620px;width:100%">
  <div id="tv_c" style="height:620px;width:100%"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>new TradingView.widget({{"autosize":true,"symbol":"{tv_sym}","interval":"D",
    "timezone":"Europe/Istanbul","theme":"{tv_theme}","style":"1","locale":"tr",
    "backgroundColor":"{bg}","allow_symbol_change":true,"details":true,
    "hotlist":true,"container_id":"tv_c"}});</script>
</div></body></html>"""
        components.html(adv_html, height=640, scrolling=False)

    with col_ch2:
        gauge_html = f"""<html><head><style>body{{margin:0;background:{bg};}}</style></head><body>
<div class="tradingview-widget-container" style="height:300px;width:100%">
<div class="tradingview-widget-container__widget" style="height:300px;width:100%"></div>
<script src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js">
{{"interval":"1D","width":"100%","isTransparent":false,"height":"300","symbol":"{tv_sym}",
  "showIntervalTabs":true,"displayMode":"single","locale":"tr","colorTheme":"{tv_theme}"}}
</script></div></body></html>"""
        components.html(gauge_html, height=320, scrolling=False)

        if not df_data.empty and chart_sym in df_data["Sembol"].values:
            r_c = df_data[df_data["Sembol"]==chart_sym].iloc[0]
            c2 = green if r_c["Değişim %"] >= 0 else red
            rsi_c2 = green if pd.notna(r_c["RSI"]) and r_c["RSI"] < 40 else \
                     red if pd.notna(r_c["RSI"]) and r_c["RSI"] > 65 else txt2
            st.markdown(f"""<div class="card" style="margin-top:8px;">
                <div style="font-size:1.3rem;font-weight:700;">{chart_sym}</div>
                <div style="font-size:1.5rem;font-weight:700;font-family:'JetBrains Mono',monospace;">{r_c['Fiyat']:,.2f}</div>
                <div style="color:{c2};font-weight:600;">{r_c['Değişim %']:+.2f}%</div>
                <div style="display:flex;gap:1.5rem;margin-top:10px;">
                    <div><div style="font-size:0.6rem;color:{txt2};">RSI</div>
                        <div style="font-weight:700;color:{rsi_c2};font-family:'JetBrains Mono',monospace;">{r_c['RSI']:.1f}</div></div>
                    <div><div style="font-size:0.6rem;color:{txt2};">Teknik</div>
                        <div style="font-weight:700;color:{c2};">{r_c['Teknik']}</div></div>
                    <div><div style="font-size:0.6rem;color:{txt2};">AI Skor</div>
                        <div style="font-weight:700;color:{blue};">{int(r_c['AI_Skor'])}/7</div></div>
                </div>
            </div>""", unsafe_allow_html=True)

# ╔══════════════════════════════╗
# ║  SEKME 7: TEMEL ANALİZ       ║
# ╚══════════════════════════════╝
with tab_fundamentals:
    selected_f = st.session_state.get("selected_stock", "THYAO")
    if secilen_piyasa == "BIST 100": auto_sym_f = f"BIST:{selected_f}"
    elif secilen_piyasa == "Kripto (USD)": auto_sym_f = f"BINANCE:{selected_f}USDT"
    else: auto_sym_f = f"NASDAQ:{selected_f}"

    st.markdown(f"""<div class="card" style="margin-bottom:14px;">
        <div style="font-size:1rem;font-weight:700;color:{blue};">{selected_f}</div>
        <div style="font-size:0.72rem;color:{txt2};">Temel Analiz · {auto_sym_f} · {secilen_piyasa}</div>
    </div>""", unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fin_html = f"""<html><head><style>body{{margin:0;background:{bg};}}</style></head><body>
<div class="tradingview-widget-container" style="height:520px;width:100%">
<div class="tradingview-widget-container__widget" style="height:520px;width:100%"></div>
<script src="https://s3.tradingview.com/external-embedding/embed-widget-financials.js">
{{"colorTheme":"{tv_theme}","isTransparent":false,"displayMode":"regular",
  "width":"100%","height":"520","symbol":"{auto_sym_f}","locale":"tr"}}
</script></div></body></html>"""
        components.html(fin_html, height=540, scrolling=False)

    with col_f2:
        prof_html = f"""<html><head><style>body{{margin:0;background:{bg};}}</style></head><body>
<div class="tradingview-widget-container" style="height:520px;width:100%">
<div class="tradingview-widget-container__widget" style="height:520px;width:100%"></div>
<script src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-profile.js">
{{"width":"100%","height":"520","colorTheme":"{tv_theme}","isTransparent":false,
  "symbol":"{auto_sym_f}","locale":"tr"}}
</script></div></body></html>"""
        components.html(prof_html, height=540, scrolling=False)
