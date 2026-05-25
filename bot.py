import ccxt
import pandas as pd
import warnings
import time
from datetime import datetime

warnings.filterwarnings('ignore')

# ==========================================
# CONNEXION BINANCE
# ==========================================
plateforme = ccxt.binance({
    'enableRateLimit': True,
})

def telecharger_donnees_multiples(symbole):
    """Télécharge la vue Hélicoptère (1 Heure) ET la vue Sniper (1 Minute)."""
    # 1. Le GPS Macro (1 Heure)
    bougies_macro = plateforme.fetch_ohlcv(symbole, timeframe='1h', limit=100)
    df_macro = pd.DataFrame(bougies_macro, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    
    # 2. Le Viseur Micro (1 Minute)
    bougies_micro = plateforme.fetch_ohlcv(symbole, timeframe='1m', limit=100)
    df_micro = pd.DataFrame(bougies_micro, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    
    return df_macro, df_micro

def calculer_tendance_macro(df_macro):
    """Analyse le GPS global (Graphique 1 Heure)."""
    # Moyenne Mobile à 50 Heures (Le juge de paix institutionnel)
    df_macro['EMA_50_Macro'] = df_macro['Close'].ewm(span=50, adjust=False).mean()
    
    prix_actuel_macro = df_macro['Close'].iloc[-1]
    ema_50_macro = df_macro['EMA_50_Macro'].iloc[-1]
    
    # Si le prix est au-dessus de l'EMA 50, le fond de l'air est à l'achat.
    return prix_actuel_macro > ema_50_macro

def calculer_indicateurs_micro(df_micro):
    """Analyse la zone de tir (Graphique 1 Minute)."""
    df_micro['EMA_20'] = df_micro['Close'].ewm(span=20, adjust=False).mean()
    df_micro['EMA_50'] = df_micro['Close'].ewm(span=50, adjust=False).mean()
    
    delta = df_micro['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perte = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / perte
    df_micro['RSI_14'] = 100 - (100 / (1 + rs))
    
    df_micro['Volume_MA_20'] = df_micro['Volume'].rolling(window=20).mean()
    return df_micro.round(2)

def generer_signal_expert(df_micro, tendance_macro_haussiere):
    """Le cerveau final : croise le Micro et le Macro."""
    aujourd_hui = df_micro.iloc[-1]
    hier = df_micro.iloc[-2]
    
    # Critères de base (Scalping 1 Minute)
    creux_rsi = aujourd_hui['RSI_14'] < 45
    tendance_micro_ok = aujourd_hui['Close'] > aujourd_hui['EMA_50']
    volume_ok = aujourd_hui['Volume'] > aujourd_hui['Volume_MA_20']
    
    # Le bot N'A LE DROIT d'acheter que si le GPS (Macro) lui donne le feu vert
    if tendance_macro_haussiere and creux_rsi and tendance_micro_ok and volume_ok:
        return '🟢 ACHAT (Validé par Tendance 1H)'
        
    # Vente : On prend nos profits rapidement (RSI > 70) 
    # OU on vend en urgence si la petite tendance se retourne.
    elif (aujourd_hui['RSI_14'] > 70) or ((aujourd_hui['EMA_20'] < aujourd_hui['EMA_50']) and (hier['EMA_20'] >= hier['EMA_50'])):
        return '🔴 VENTE'
        
    return '➖ NEUTRE'

if __name__ == "__main__":
    print("\n=======================================================")
    print("🧠 RADAR EXPERT : FILTRE MULTI-TIMEFRAME ACTIVÉ")
    print("=======================================================\n")
    
    liste_cryptos = ["BTC/USDT", "ETH/USDT"] 
    memoire_signaux = {crypto: "➖ NEUTRE" for crypto in liste_cryptos}
    
    while True:
        try:
            heure_actuelle = datetime.now().strftime("%H:%M:%S")
            print(f"--- Scan de {heure_actuelle} ---")
            
            for crypto in liste_cryptos:
                # 1. On aspire les deux réalités (Macro et Micro)
                df_macro, df_micro = telecharger_donnees_multiples(crypto)
                
                # 2. On vérifie le climat global sur 1 Heure
                macro_est_haussiere = calculer_tendance_macro(df_macro)
                etat_climat = "☀️ Haussier" if macro_est_haussiere else "🌧️ Baissier"
                
                # 3. On calcule la précision à la minute
                df_micro = calculer_indicateurs_micro(df_micro)
                
                # 4. Décision finale
                signal_actuel = generer_signal_expert(df_micro, macro_est_haussiere)
                
                aujourd_hui = df_micro.iloc[-1]
                nom_propre = crypto.replace("/USDT", "")
                
                # Affichage enrichi avec le climat global
                print(f"▸ {nom_propre} | Climat 1H: {etat_climat} | Prix: {aujourd_hui['Close']:,.2f} USDT | Tendance 1M: {signal_actuel}")
                
                # Alerte visuelle forte
                if signal_actuel != memoire_signaux[crypto]:
                    if signal_actuel in ['🟢 ACHAT (Validé par Tendance 1H)', '🔴 VENTE']:
                        print(f"\n🚨🚨 ALERTE {nom_propre} : {signal_actuel} 🚨🚨")
                        print(f"👉 Prix : {aujourd_hui['Close']:,.2f} USDT | RSI : {aujourd_hui['RSI_14']}\n")
                    
                    memoire_signaux[crypto] = signal_actuel
            
            print("")
            time.sleep(60)
            
        except Exception as e:
            print(f"⚠️ Perturbation réseau... ({e})")
            time.sleep(60)