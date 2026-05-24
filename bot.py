import yfinance as yf
import pandas as pd
import warnings
import time
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime

warnings.filterwarnings('ignore')

# ==========================================
# ⚙️ CONFIGURATION EMAIL (À REMPLIR)
# ==========================================
EMAIL_EXPEDITEUR = "clement.cabriere30@gmail.com" 
MOT_DE_PASSE_APP = "sqkr pviv ctrt ektp"  
EMAIL_DESTINATAIRE = "clement.cabriere30@gmail.com"
# ==========================================

def envoyer_email(sujet, contenu):
    """Envoie un email sécurisé."""
    msg = EmailMessage()
    msg.set_content(contenu)
    msg['Subject'] = sujet
    msg['From'] = EMAIL_EXPEDITEUR
    msg['To'] = EMAIL_DESTINATAIRE

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_EXPEDITEUR, MOT_DE_PASSE_APP.replace(" ", ""))
            server.send_message(msg)
        print(f"✉️  ALERTE EMAIL ENVOYÉE AVEC SUCCÈS !")
    except Exception as e:
        print(f"❌ Erreur critique email : {e}")

def telecharger_donnees(symbole):
    """Téléchargement des prix ET des volumes pour un symbole précis."""
    data = yf.download(symbole, period="5d", interval="1m", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    return data

def ajouter_indicateurs_pro(df):
    """Calcul des indicateurs."""
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perte = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / perte
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
    return df.round(2)

def generer_signaux(df):
    """Logique ultra-stricte."""
    df['Signal'] = '➖ NEUTRE'
    
    achat = (df['Close'] > df['EMA_200']) & (df['RSI_14'] < 30) & (df['Volume'] > df['Volume_MA_20'])
    vente = (df['RSI_14'] > 75) | ((df['EMA_20'] < df['EMA_50']) & (df['EMA_20'].shift(1) >= df['EMA_50'].shift(1)))
    
    df.loc[achat, 'Signal'] = '🟢 ACHAT FORT (Volume Confirmé)'
    df.loc[vente, 'Signal'] = '🔴 VENTE'
    return df

if __name__ == "__main__":
    print("\n=======================================================")
    print("🛡️ RADAR MULTI-CIBLES ACTIVÉ (BTC & ETH)")
    print("=======================================================\n")
    
    # 1. On définit la liste des cryptos à surveiller
    liste_cryptos = ["BTC-USD", "ETH-USD"]
    
    # 2. Le bot crée une mémoire séparée pour chaque crypto
    memoire_signaux = {crypto: "➖ NEUTRE" for crypto in liste_cryptos}
    
    while True:
        try:
            heure_actuelle = datetime.now().strftime("%H:%M:%S")
            print(f"--- Scan de {heure_actuelle} ---")
            
            # 3. Le bot analyse chaque crypto l'une après l'autre
            for crypto in liste_cryptos:
                df = telecharger_donnees(crypto)
                df = ajouter_indicateurs_pro(df)
                df = generer_signaux(df)
                
                aujourd_hui = df.iloc[-1]
                signal_actuel = aujourd_hui['Signal']
                prix_actuel = aujourd_hui['Close']
                volume_actuel = aujourd_hui['Volume']
                
                # Nom raccourci pour un affichage plus propre (ex: BTC au lieu de BTC-USD)
                nom_propre = crypto.replace("-USD", "")
                
                print(f"▸ {nom_propre} | Prix: {prix_actuel:,.2f} $ | Vol: {volume_actuel:,.0f} | Tendance: {signal_actuel}")
                
                # 4. Vérification de la mémoire spécifique à CETTE crypto
                if signal_actuel != memoire_signaux[crypto]:
                    if signal_actuel in ['🟢 ACHAT FORT (Volume Confirmé)', '🔴 VENTE']:
                        sujet = f"🚨 ALERTE {nom_propre} : {signal_actuel}"
                        contenu = f"Mouvement massif détecté sur {nom_propre}.\n\nHeure : {heure_actuelle}\nPrix : {prix_actuel:,.2f} $\nRSI : {aujourd_hui['RSI_14']}\n\nGo sur ta plateforme."
                        envoyer_email(sujet, contenu)
                    
                    # Mise à jour de la mémoire pour cette crypto uniquement
                    memoire_signaux[crypto] = signal_actuel
            
            print("") # Ligne vide pour aérer la lecture
            time.sleep(60)
            
        except Exception as e:
            print(f"⚠️ Perturbation réseau, reprise dans 60s... ({e})")
            time.sleep(60)