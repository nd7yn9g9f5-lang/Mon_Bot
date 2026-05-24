import yfinance as yf
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

def telecharger_donnees(symbole="BTC-USD", periode="60d"):
    """On télécharge 60 jours de données, mais découpées HEURE par HEURE."""
    print("📡 Connexion aux marchés (HAUTE PRÉCISION - 1 HEURE)...\n")
    # C'est ici que la magie de la précision opère : interval="1h"
    data = yf.download(symbole, period=periode, interval="1h", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    return data

def ajouter_indicateurs_pro(df):
    """Calcul des indicateurs sur des données horaires."""
    # Les EMA représentent maintenant des HEURES et non plus des jours.
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perte = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / perte
    df['RSI_14'] = 100 - (100 / (1 + rs))
    return df.round(2)

def generer_signaux(df):
    """Logique ultra-réactive pour le court terme."""
    df['Signal'] = '➖ NEUTRE (Pas d\'opportunité immédiate)'
    
    # Pour le court terme, on est un peu plus agressif sur le RSI (40 au lieu de 45)
    achat = (df['Close'] > df['EMA_200']) & (df['RSI_14'] < 40)
    vente = (df['RSI_14'] > 75) | ((df['EMA_20'] < df['EMA_50']) & (df['EMA_20'].shift(1) >= df['EMA_50'].shift(1)))
    
    df.loc[achat, 'Signal'] = '🟢 ACHAT COURT TERME (Sniper)'
    df.loc[vente, 'Signal'] = '🔴 VENTE COURT TERME'
    return df

# --- DÉMARRAGE DU TABLEAU DE BORD ---
if __name__ == "__main__":
    print("\n=======================================================")
    print("🎯 ASSISTANT SNIPER - DAY TRADING (Intervalle : 1 Heure)")
    print("=======================================================\n")
    
    df = telecharger_donnees(symbole="BTC-USD", periode="60d")
    df = ajouter_indicateurs_pro(df)
    df = generer_signaux(df)
    
    # La toute dernière ligne correspond à l'heure ACTUELLE
    aujourd_hui = df.iloc[-1]
    
    print(f"▶ Prix instantané du Bitcoin : {aujourd_hui['Close']:,.2f} $\n")
    
    print("--- INDICATEURS SUR LES TOUTES DERNIÈRES HEURES ---")
    print(f"▸ RSI Actuel (Surchauffe) : {aujourd_hui['RSI_14']}")
    print(f"▸ Tendance Courte (20h)   : {aujourd_hui['EMA_20']:,.2f} $")
    print(f"▸ Tendance Longue (200h)  : {aujourd_hui['EMA_200']:,.2f} $\n")
    
    print("=======================================================")
    print(f"🎯 DÉCISION IMMÉDIATE : {aujourd_hui['Signal']}")
    print("=======================================================\n")