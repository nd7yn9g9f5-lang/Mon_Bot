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
EMAIL_EXPEDITEUR = "ton_adresse@gmail.com" 
MOT_DE_PASSE_APP = "sqkr pviv ctrt ektp"  
EMAIL_DESTINATAIRE = "ton_adresse@gmail.com"
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
        print("✉️  ALERTE EMAIL ENVOYÉE AVEC SUCCÈS !")
    except Exception as e:
        print(f"❌ Erreur critique email : {e}")

def telecharger_donnees(symbole="BTC-USD"):
    """Téléchargement des prix ET des volumes."""
    data = yf.download(symbole, period="5d", interval="1m", progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    return data

def ajouter_indicateurs_pro(df):
    """Calcul des indicateurs avec intégration du Volume."""
    # 1. Moyennes Mobiles Classiques
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    # 2. RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perte = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / perte
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # 3. NOUVEAU : Moyenne du Volume sur 20 minutes
    df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()
    
    return df.round(2)

def generer_signaux(df):
    """Logique ultra-stricte : Tendance + Survente + VOLUME."""
    df['Signal'] = '➖ NEUTRE'
    
    # Le bot n'achète QUE si le volume actuel est supérieur à la moyenne des 20 dernières minutes
    achat = (df['Close'] > df['EMA_200']) & (df['RSI_14'] < 30) & (df['Volume'] > df['Volume_MA_20'])
    vente = (df['RSI_14'] > 75) | ((df['EMA_20'] < df['EMA_50']) & (df['EMA_20'].shift(1) >= df['EMA_50'].shift(1)))
    
    df.loc[achat, 'Signal'] = '🟢 ACHAT FORT (Volume Confirmé)'
    df.loc[vente, 'Signal'] = '🔴 VENTE'
    return df

if __name__ == "__main__":
    print("\n=======================================================")
    print("🛡️ RADAR INSTITUTIONNEL ACTIVÉ (Filtre de Volume ON)")
    print("=======================================================\n")
    
    dernier_signal_connu = "➖ NEUTRE" 
    
    while True:
        try:
            df = telecharger_donnees()
            df = ajouter_indicateurs_pro(df)
            df = generer_signaux(df)
            
            aujourd_hui = df.iloc[-1]
            signal_actuel = aujourd_hui['Signal']
            prix_actuel = aujourd_hui['Close']
            volume_actuel = aujourd_hui['Volume']
            heure_actuelle = datetime.now().strftime("%H:%M:%S")
            
            # Affichage enrichi avec l'état du volume
            print(f"[{heure_actuelle}] Prix: {prix_actuel:,.2f} $ | Vol: {volume_actuel:,.0f} | Tendance: {signal_actuel}")
            
            if signal_actuel != dernier_signal_connu:
                if signal_actuel in ['🟢 ACHAT FORT (Volume Confirmé)', '🔴 VENTE']:
                    sujet = f"🚨 ALERTE CONFIRMÉE : {signal_actuel} BTC"
                    contenu = f"Mouvement massif détecté avec confirmation des volumes.\n\nHeure : {heure_actuelle}\nPrix : {prix_actuel:,.2f} $\nRSI : {aujourd_hui['RSI_14']}\n\nGo sur ta plateforme."
                    envoyer_email(sujet, contenu)
                
                dernier_signal_connu = signal_actuel
            
            time.sleep(60)
            
        except Exception as e:
            print(f"⚠️ Perturbation, reprise dans 60s... ({e})")
            time.sleep(60)