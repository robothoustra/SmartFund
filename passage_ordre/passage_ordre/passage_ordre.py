import argparse
import pandas as pd
import numpy as np
import os
from datetime import datetime

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
    list_col_reel = ['TCIKER','QTE']
    
    #Lecture des données        
    dfPtfReel = pd.read_csv(args.ptf_reel,header=[0], sep=';', parse_dates=['DATE_PRTF'])
    dfPtfCible = pd.read_csv(args.ptf_th, header=[0], sep=';', parse_dates=['DATE_PRTF'])
    
    dfPtfReel = dfPtfReel[(dfPtfReel['DATE_PRTF'] == dtPTF_old)]
    dfPtfReel = dfPtfReel[list_col_reel]
    
    dfPtfCible = dfPtfCible[(dfPtfCible['DATE_PRTF'] == dtPTF_cible)]
    dfPtfCible = dfPtfCible[list_col_th]
    
    print(dfPtfCible)
    
if __name__ == '__main__':
    GetOrders()
    
    