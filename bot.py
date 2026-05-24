import yfinance as yf
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

def telecharger_donnees(symbole="BTC-USD", periode="300d"):
    """Télécharge suffisamment de jours pour calculer la moyenne sur 200 jours."""
    print("📡 Connexion aux marchés en cours...\n")
    data = yf.download(symbole, period=periode, interval="1d", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    return data

def ajouter_indicateurs_pro(df):
    """Calcul des indicateurs mathématiques."""
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
    """Logique de décision V2."""
    df['Signal'] = '➖ NEUTRE (Patiente, pas de mouvement clair)'
    
    achat = (df['Close'] > df['EMA_200']) & (df['RSI_14'] < 45)
    vente = (df['RSI_14'] > 75) | ((df['EMA_20'] < df['EMA_50']) & (df['EMA_20'].shift(1) >= df['EMA_50'].shift(1)))
    
    df.loc[achat, 'Signal'] = '🟢 ACHAT RECOMMANDÉ'
    df.loc[vente, 'Signal'] = '🔴 VENTE RECOMMANDÉE'
    return df

# --- DÉMARRAGE DU TABLEAU DE BORD ---
if __name__ == "__main__":
    print("\n=======================================================")
    print("👁️  ASSISTANT TRADING CRYPTO - ANALYSE EN DIRECT")
    print("=======================================================\n")
    
    # 1. On prépare les données
    df = telecharger_donnees(symbole="BTC-USD", periode="300d")
    df = ajouter_indicateurs_pro(df)
    df = generer_signaux(df)
    
    # 2. On isole la TOUTE DERNIÈRE ligne (le moment présent)
    aujourd_hui = df.iloc[-1]
    
    # 3. Affichage du tableau de bord
    print(f"▶ Prix actuel du Bitcoin : {aujourd_hui['Close']:,.2f} $\n")
    
    print("--- ÉTAT DES INDICATEURS ---")
    print(f"▸ RSI (Surchauffe)       : {aujourd_hui['RSI_14']}")
    print(f"▸ Tendance Courte (20j)  : {aujourd_hui['EMA_20']:,.2f} $")
    print(f"▸ Tendance Longue (200j) : {aujourd_hui['EMA_200']:,.2f} $\n")
    
    print("=======================================================")
    print(f"🎯 DÉCISION POUR AUJOURD'HUI : {aujourd_hui['Signal']}")
    print("=======================================================\n")