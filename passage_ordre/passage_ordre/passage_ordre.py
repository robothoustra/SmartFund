import argparse
import pandas as pd
import numpy as np
import os
import calcs
from datetime import datetime
import scipy.optimize as opt

# https://docs.scipy.org/doc/scipy/reference/optimize.html
# https://docs.scipy.org/doc/scipy/reference/tutorial/optimize.html
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html

class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))

def load_arguments(**kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-pr","--ptf_reel", help="Chemin vers le fichier contenant le dernier portefeuille",
                        type=str, default='../../selection/selection/output/prtfs_reels.csv')
    parser.add_argument("-pt","--ptf_th", help="Chemin vers le fichier contenant le portefeuille théorique",
                        type=str, default='../../selection/selection/output/prtfs.csv')
    parser.add_argument("-po","--path_output",help="Chemin du fichier de sortie",
                        type=str, default='./output/')
    #parser.add_argument("-ic","--inst_const", help="Chemin vers le fichier contenant la liste des instruments avec leur contraintes en colonne",
                        #type=str, default='./output/contraintes.csv')
    parser.add_argument("-dtn","--date_new", help="Date du portefeuille cible",
                        type=str, default='01/01/2020')
    parser.add_argument("-dto","--date_old", help="Date du dernier portefeuille réel",
                        type=str, default='01/12/2019')

    for key, value in kwargs.items():
        for action in parser._actions:
            if action.dest == key:
                action.choices = value
                action.default = value
                
    return parser

def GetOrders(**kwargs):
    
    parser = load_arguments(**kwargs)
    args = parser.parse_args()
    
    dtPTF_cible = datetime.strptime(args.date_new,"%d/%m/%Y")
    dtPTF_old = datetime.strptime(args.date_old,"%d/%m/%Y")
    
    #Liste des colonnes à récupérer dans le fichier du dernier portefeuille
    list_col_th = ['TICKER','POIDS','COURS']
    list_col_reel = ['TICKER','QTE','COURS']
    
    #Lecture des données.
    #La colonne "COURS" du dfPtfReel doit contenir les (dernier) cours à partir desquels seront 
    #recalculé les poids pour en déduire le nombre de titre à vendre et à acheter.
    #Les "COURS" du dfPtfReel doivent être les mêmes que les cours
    dfPtfReel = pd.read_csv(args.ptf_reel,header=[0], sep=';', parse_dates=['DATE_PRTF'])
    dfPtfCible = pd.read_csv(args.ptf_th, header=[0], sep=';', parse_dates=['DATE_PRTF'])
    
    dfPtfReel = dfPtfReel[(dfPtfReel['DATE_PRTF'] == dtPTF_old)]
    dfPtfReel = dfPtfReel[list_col_reel].set_index(['TICKER'])
    
    dfPtfCible = dfPtfCible[(dfPtfCible['DATE_PRTF'] == dtPTF_cible)]
    dfPtfCible = dfPtfCible[list_col_th].set_index(['TICKER'])
    
    #Prévention pour les virgules à la place des points
    if not pd.api.types.is_numeric_dtype(dfPtfReel['QTE']) :     
        dfPtfReel['QTE'] = dfPtfReel['QTE'].str.replace(',','.').astype(float)
    if not pd.api.types.is_numeric_dtype(dfPtfReel['COURS']):     
       dfPtfReel['COURS'] = dfPtfReel['COURS'].str.replace(',','.').astype(float)
    dfPtfReel.sort_values(['TICKER'])
    
    #Calcul les poids en fonction des quantités et des cours
    calcs.CalculPoids(dfPtfReel)
    
    actif_net = sum(dfPtfReel['QTE']*dfPtfReel['COURS'])
    
    #Titres à vendre (ceux qui ne sont pas dans le protefeuille cible)
    dfSell = dfPtfReel[~dfPtfReel.index.isin(dfPtfCible.index.values)]
    
    #Ajout des titres à vendre à l'order book
    order_book = dfSell['QTE'].to_frame()
    order_book['SENS'] = "S"
    
    #Retrait des titres qui ne sont plus présent dans le nouveau portefeuille
    dfPtfTemp = dfPtfCible['COURS']
    
    #Joint les quantité réelles aux tickers cibles et rempli les quantités des nouveaux ticker par "0"
    dfPtfTemp = dfPtfTemp.to_frame().join(dfPtfReel['QTE']).fillna(value=0).sort_values(['TICKER'], ascending=True)
    
    #Methode des moindres carrés pour trouver les quantités cibles
    montant_cible = np.array(calcs.get_montant_cible(dfPtfCible,actif_net))
    quantite_reel = np.array(dfPtfTemp['QTE'])
    cours = np.array(dfPtfTemp['COURS'])
    
    res = opt.least_squares(calcs.residus, quantite_reel,bounds=(0,np.inf), args=(cours,montant_cible), verbose=1)

    dfPtfTemp['QTE_CIBLE'] = res.x
    dfPtfTemp['DIFF_QTE'] = round(dfPtfTemp['QTE_CIBLE']-dfPtfTemp['QTE'])
    dfPtfTemp['SENS'] = ['S' if x<0 else 'B' for x in dfPtfTemp['DIFF_QTE']]
    dfPtfTemp['DIFF_QTE'] = abs(dfPtfTemp['DIFF_QTE'])
    dfPtfTemp = dfPtfTemp[['DIFF_QTE','SENS']].loc[(dfPtfTemp['DIFF_QTE'] !=0)]
    dfPtfTemp.rename(columns={'SENS': 'SENS', 'DIFF_QTE': 'QTE'}, inplace=True)
    order_book = pd.concat([order_book, dfPtfTemp])
    
    #Sortie
    #print(order_book)
    strCsvPrtf = 'order_book_' + datetime.strftime(datetime.now(),'%Y%m%d_%H%M.csv') 
    order_book.to_csv(args.path_output + strCsvPrtf, mode='w',header=True, sep=';')
        
if __name__ == '__main__':
    GetOrders()
    
    