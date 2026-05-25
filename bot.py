import ccxt
import yfinance as yf
import pandas as pd
import warnings
import time
from datetime import datetime

warnings.filterwarnings('ignore')

# ==========================================
# 1. CONNEXIONS (BINANCE + YAHOO)
# ==========================================
plateforme = ccxt.binance({
    'enableRateLimit': True,
})

def telecharger_donnees_crypto(symbole):
    """Téléchargement ultra-précis via Binance."""
    bougies = plateforme.fetch_ohlcv(symbole, timeframe='1m', limit=100)
    df = pd.DataFrame(bougies, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    return df

def telecharger_donnees_tradi(symbole):
    """Téléchargement via Yahoo Finance pour la bourse classique."""
    data = yf.download(symbole, period="5d", interval="1m", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    return data.tail(100) # On garde les 100 dernières minutes pour correspondre à Binance

def ajouter_indicateurs_pro(df):
    """Calcul des indicateurs."""
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perte = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / perte
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
    return df.round(2)

def generer_signaux(df):
    """Logique de Scalping."""
    df['Signal'] = '➖ NEUTRE'
    
    achat = (df['Close'] > df['EMA_50']) & (df['RSI_14'] < 45) & (df['Volume'] > df['Volume_MA_20'])
    vente = (df['RSI_14'] > 70) | ((df['EMA_20'] < df['EMA_50']) & (df['EMA_20'].shift(1) >= df['EMA_50'].shift(1)))
    
    df.loc[achat, 'Signal'] = '🟢 ACHAT'
    df.loc[vente, 'Signal'] = '🔴 VENTE'
    return df

if __name__ == "__main__":
    print("\n=======================================================")
    print("🌍 RADAR HYBRIDE : CRYPTO (Binance) + TRADI (Yahoo)")
    print("⚠️  Rappel : L'Or et l'ETF dorment la nuit et le week-end !")
    print("=======================================================\n")
    
    # Séparation des marchés
    liste_cryptos = ["BTC/USDT", "ETH/USDT"] 
    # GC=F : Gold Futures (Or) | CW8.PA : Amundi MSCI World PEA (Euronext Paris)
    liste_tradi = ["GC=F", "CW8.PA"] 
    
    # Mémoire commune
    memoire_signaux = {crypto: "➖ NEUTRE" for crypto in (liste_cryptos + liste_tradi)}
    
    while True:
        try:
            heure_actuelle = datetime.now().strftime("%H:%M:%S")
            print(f"--- Scan de {heure_actuelle} ---")
            
            # --- SCAN CRYPTO (Binance) ---
            for crypto in liste_cryptos:
                df = telecharger_donnees_crypto(crypto)
                df = ajouter_indicateurs_pro(df)
                df = generer_signaux(df)
                
                aujourd_hui = df.iloc[-1]
                nom_propre = crypto.replace("/USDT", "")
                
                print(f"▸ {nom_propre} (Crypto) | Prix: {aujourd_hui['Close']:,.2f} $ | Vol: {aujourd_hui['Volume']:,.2f} | Tendance: {aujourd_hui['Signal']}")
                memoire_signaux[crypto] = aujourd_hui['Signal']

            # --- SCAN TRADI (Yahoo) ---
            for actif in liste_tradi:
                df = telecharger_donnees_tradi(actif)
                if df.empty:
                    continue # Sécurité si Yahoo ne répond pas
                    
                df = ajouter_indicateurs_pro(df)
                df = generer_signaux(df)
                
                aujourd_hui = df.iloc[-1]
                
                # Jolis noms pour le terminal
                nom_propre = "OR" if actif == "GC=F" else "MSCI PEA"
                devise = "$" if actif == "GC=F" else "€"
                
                # Si le volume est à 0, la bourse est probablement fermée ou en pause
                etat_bourse = " (Bourse Fermée/Illiquide)" if aujourd_hui['Volume'] == 0 else ""
                
                print(f"▸ {nom_propre} (Tradi)  | Prix: {aujourd_hui['Close']:,.2f} {devise} | Vol: {aujourd_hui['Volume']:,.0f}{etat_bourse} | Tendance: {aujourd_hui['Signal']}")
                memoire_signaux[actif] = aujourd_hui['Signal']
            
            print("")
            time.sleep(60)
            
        except Exception as e:
            print(f"⚠️ Perturbation réseau... ({e})")
            time.sleep(60)