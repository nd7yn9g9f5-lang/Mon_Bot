import ccxt
import pandas as pd
import warnings
import time
from datetime import datetime

warnings.filterwarnings('ignore')

# ==========================================
# 1. CONNEXION DIRECTE À BINANCE (Moteur Pro)
# ==========================================
plateforme = ccxt.binance({
    'enableRateLimit': True, # Sécurité pour ne pas surcharger Binance
})

def telecharger_donnees_binance(symbole):
    """Téléchargement ultra-précis depuis le carnet d'ordres de Binance."""
    # On récupère les 100 dernières minutes (Open, High, Low, Close, Volume)
    bougies = plateforme.fetch_ohlcv(symbole, timeframe='1m', limit=100)
    df = pd.DataFrame(bougies, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    return df

def ajouter_indicateurs_pro(df):
    """Calcul des indicateurs avec le vrai Volume de Binance."""
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perte = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / perte
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # Sécurité Volume réactivée grâce aux vraies données Binance
    df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
    return df.round(2)

def generer_signaux(df):
    """Logique de Scalping avec confirmation de VRAI Volume."""
    df['Signal'] = '➖ NEUTRE'
    
    # ACHAT : L'EMA + le RSI + Le vrai Volume Binance
    achat = (df['Close'] > df['EMA_50']) & (df['RSI_14'] < 45) & (df['Volume'] > df['Volume_MA_20'])
    
    # VENTE : Prise de profit rapide (RSI > 70) ou changement de tendance
    vente = (df['RSI_14'] > 70) | ((df['EMA_20'] < df['EMA_50']) & (df['EMA_20'].shift(1) >= df['EMA_50'].shift(1)))
    
    df.loc[achat, 'Signal'] = '🟢 ACHAT (Validé par Binance)'
    df.loc[vente, 'Signal'] = '🔴 VENTE'
    return df

if __name__ == "__main__":
    print("\n=======================================================")
    print("🏦 RADAR INSTITUTIONNEL CONNECTÉ À BINANCE")
    print("⚡ Mode : 100% Terminal (Alertes e-mail désactivées)")
    print("=======================================================\n")
    
    liste_cryptos = ["BTC/USDT", "ETH/USDT"] 
    memoire_signaux = {crypto: "➖ NEUTRE" for crypto in liste_cryptos}
    
    while True:
        try:
            heure_actuelle = datetime.now().strftime("%H:%M:%S")
            print(f"--- Scan de {heure_actuelle} ---")
            
            for crypto in liste_cryptos:
                df = telecharger_donnees_binance(crypto)
                df = ajouter_indicateurs_pro(df)
                df = generer_signaux(df)
                
                aujourd_hui = df.iloc[-1]
                signal_actuel = aujourd_hui['Signal']
                prix_actuel = aujourd_hui['Close']
                volume_actuel = aujourd_hui['Volume']
                
                nom_propre = crypto.replace("/USDT", "")
                
                # Affichage standard discret
                print(f"▸ {nom_propre} | Prix: {prix_actuel:,.2f} USDT | Vol: {volume_actuel:,.2f} | Tendance: {signal_actuel}")
                
                # Mise en évidence visuelle forte si le signal change (Achat/Vente)
                if signal_actuel != memoire_signaux[crypto]:
                    if signal_actuel in ['🟢 ACHAT (Validé par Binance)', '🔴 VENTE']:
                        print(f"\n🚨🚨 ALERTE {nom_propre} : {signal_actuel} 🚨🚨")
                        print(f"👉 Prix : {prix_actuel:,.2f} USDT | RSI : {aujourd_hui['RSI_14']}\n")
                    
                    memoire_signaux[crypto] = signal_actuel
            
            print("") # Ligne vide pour aérer
            time.sleep(60)
            
        except Exception as e:
            print(f"⚠️ Perturbation réseau avec Binance... ({e})")
            time.sleep(60)