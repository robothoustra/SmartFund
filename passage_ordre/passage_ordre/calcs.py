import pandas as pd

def CalculPoids(dfPtfReel):

    #Calcul de l'actif net du portefeuille réel
    actif_net = sum(dfPtfReel['QTE']*dfPtfReel['COURS'])
    dfPtfReel['PRCT_ACT_NET'] = dfPtfReel['QTE']*dfPtfReel['COURS']/actif_net

def residus(quantite_reel, cours, montant_cible):
    return montant_cible - quantite_reel*cours

def get_montant_cible(dfPtfCible, actif_net):
    df_montant_cible = dfPtfCible['POIDS']*actif_net
    df_montant_cible.sort_index(ascending=True,inplace=True)
    return df_montant_cible.values