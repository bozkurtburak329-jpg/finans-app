"""
Otonom Yapay Zeka Botu - Model Eğitimi (v1.0)
Bu script verileri çeker, veritabanına kaydeder ve AI modelini eğitir.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# 1. AYARLAR VE VERİ ÇEKME
hisseler = ["THYAO.IS", "EREGL.IS"] # Test için iki sağlam hisse
baslangic_tarihi = "2024-01-01"

print("📡 1. Aşama: Yahoo Finance'ten Veriler Çekiliyor...")
tum_veriler = []

for hisse in hisseler:
    df = yf.download(hisse, start=baslangic_tarihi, progress=False)
    if not df.empty:
        # MultiIndex sütunları düzeltme (yfinance bazen böyle döndürür)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        df['Sembol'] = hisse
        tum_veriler.append(df)

df_ana = pd.concat(tum_veriler)

# 2. ÜCRETSİZ VERİTABANINA (SQLite) KAYIT
print("💾 2. Aşama: Veriler SQLite Veritabanına Kaydediliyor...")
conn = sqlite3.connect('borsa_hafiza.db')
df_ana.to_sql('gecmis_veriler', conn, if_exists='replace', index=True)
conn.close()

# 3. ÖZNİTELİK MÜHENDİSLİĞİ (Yapay Zekanın Bakacağı Veriler)
print("⚙️ 3. Aşama: İndikatörler Hesaplanıyor...")

def rsi_hesapla(data, periyot=14):
    fark = data.diff()
    yukselis = fark.clip(lower=0)
    dusus = -1 * fark.clip(upper=0)
    ema_yukselis = yukselis.ewm(com=periyot-1, min_periods=periyot).mean()
    ema_dusus = dusus.ewm(com=periyot-1, min_periods=periyot).mean()
    rs = ema_yukselis / ema_dusus
    return 100 - (100 / (1 + rs))

# Her hisse için ayrı ayrı hesaplama yapıyoruz
df_islenmis = pd.DataFrame()
for hisse in hisseler:
    hisse_df = df_ana[df_ana['Sembol'] == hisse].copy()
    
    # Teknik İndikatörler
    hisse_df['RSI'] = rsi_hesapla(hisse_df['Close'])
    hisse_df['SMA_20'] = hisse_df['Close'].rolling(window=20).mean()
    hisse_df['SMA_50'] = hisse_df['Close'].rolling(window=50).mean()
    
    # MACD
    ema_12 = hisse_df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = hisse_df['Close'].ewm(span=26, adjust=False).mean()
    hisse_df['MACD'] = ema_12 - ema_26
    hisse_df['MACD_Signal'] = hisse_df['MACD'].ewm(span=9, adjust=False).mean()
    
    # HEDEF BELİRLEME (Yapay zeka neyi tahmin edecek?)
    # 3 Gün sonraki kapanış fiyatı bugünden yüksekse 1 (AL), düşükse 0 (SAT/BEKLE)
    hisse_df['Gelecek_Fiyat'] = hisse_df['Close'].shift(-3)
    hisse_df['Hedef'] = (hisse_df['Gelecek_Fiyat'] > hisse_df['Close']).astype(int)
    
    df_islenmis = pd.concat([df_islenmis, hisse_df])

# Boş (NaN) verileri temizle
df_islenmis = df_islenmis.dropna()

# 4. YAPAY ZEKA MODELİNİ EĞİTME
print("🧠 4. Aşama: Yapay Zeka (Random Forest) Eğitiliyor...")

# Modelin bakacağı özellikler (Features)
X = df_islenmis[['RSI', 'SMA_20', 'SMA_50', 'MACD', 'MACD_Signal']]
# Modelin bulmaya çalışacağı sonuç (Target)
y = df_islenmis['Hedef']

# Veriyi test ve eğitim olarak ikiye bölüyoruz (%80 eğitim, %20 test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

# Random Forest Algoritması
model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# Modelin Başarısını Ölçme
tahminler = model.predict(X_test)
basari = accuracy_score(y_test, tahminler)
print(f"🎯 Modelin Yön Tahmin Başarısı: %{basari * 100:.2f}")

# 5. BEYNİ KAYDETME
print("📦 5. Aşama: Eğitilen Model 'bas_ekonomist_modeli.pkl' Olarak Kaydediliyor...")
joblib.dump(model, 'bas_ekonomist_modeli.pkl')

print("✅ İŞLEM TAMAMLANDI! Beyin hazırlandı.")
