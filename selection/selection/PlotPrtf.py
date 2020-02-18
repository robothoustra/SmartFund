# -*- coding: utf-8 -*-
import argparse
import pandas as pd
from dateutil.rrule import rrulestr, rrule
from dateutil.parser import parse
from datetime import datetime
import utils
import matplotlib.pyplot as plt
import numpy as np
import csv

def load_arguments(**kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-pc","--fichier_cours", help="Chemin vers le fichier des historiques de cours", type=str, default='Histo_Cours.csv')
    parser.add_argument("-pb", "--fichier_bench", help="Chemin vers le fichier de l'historiqe du benchmark", type=str, default='Histo_Bench.csv')
    parser.add_argument("-pp", "--fichier_prtfs", help="Chemin vers le fichier del'historique des portefeuilles", type=str, default='prtfs.csv')
    parser.add_argument("-dd", "--date_debut", help="Date de début du calcul des performances", type=str, default='01/01/2016')
    parser.add_argument("-df", "--date_fin", help="Date de fin du calcul des performances", type=str, default='01/02/2020')
    parser.add_argument("-tp", "--type_pas", help="Type de pas entre chaque calcul de perf", type=str, choices=['DAILY','WEEKLY','MONTHLY','YEARLY'], default='WEEKLY')
    parser.add_argument("-nl", "--nb_pas", help="Nombre de pas entre chaque calcul de perf", type=int, default=1)
    parser.add_argument("-b", "--base", help="Base du graphique", type=int, default=100)
    parser.add_argument("-g", "--graphique", help="Créé le graphique", action="store_true", default=True)
    
    for key, value in kwargs.items():
        for action in parser._actions:
            if action.dest == key:
                action.choices == value
                
    return parser
    
def Calc_Perf(**kwargs):
    
    parser = load_arguments(**kwargs)
    args = parser.parse_args()
        
    dfCours = pd.read_csv(args.fichier_cours,header=[0], sep=';',index_col=0, parse_dates=True)
    dfBench = pd.read_csv(args.fichier_bench, header=[0], sep=';',index_col=0, parse_dates=True)
    if kwargs.get('Portefeuilles',None) == None:
        dfPrtfs = pd.read_csv(args.fichier_prtfs,header=[0], sep=';', parse_dates=['DATE_PRTF'])
    else:
        dfPrtfs = kwargs.get('Portefeuilles',None)
    
    #récupère l'ensemble des dates des portefeuilles
    dfPrtfs.sort_values(by=['DATE_PRTF'],ascending=True, inplace=True)
    dtPrtfs = [x.astype('M8[ms]').astype('O') for x in dfPrtfs['DATE_PRTF'].unique()]
    
    dtDeb = datetime.strptime(args.date_debut,'%d/%m/%Y') 
    dtFin = datetime.strptime(args.date_fin,'%d/%m/%Y') 
    
    #vecteur des dates de calcul de perf
    strRule = "FREQ=" + str(args.type_pas) + ";INTERVAL=" + str(args.nb_pas) + ";UNTIL=" + datetime.strftime(dtFin,"%Y%m%d")
    setDates = set(rrulestr(strRule, dtstart=dtDeb))
    
    #S'assure que les dates de chaque portefeuille sont présente dans le set contenant les dates de calcul
    setDates.update(dtPrtfs)
    vDates = list(setDates)
    vDates.sort()
    
    #dfDates = pd.DataFrame.
    
    #initialiser une matrice de trois colonne : Ticker, Poids, Prix
    #retirer la première date de lstDates car elle correspond à la base
    #initialiser un vecteur des cours du portefeuille
    base = args.base
    newMatCalc = pd.DataFrame()#columns=['TICKER','POIDS','COURS'])
    vPrtf = []
    lBench = []
    
    for dtCalc in vDates:
        #Ensemble des dates de portefeuilles inférieures ou égales à la date de calulc
        dtList = [x for x in dtPrtfs if x <= dtCalc]
        
        #S'il existe des dates de portefeuilles inférieurs ou égale à celle de la date de calcul
        if len(dtList) > 0:
            dtLastPrtf = max(dtList)
            
            #Si la date de calcul est une date de rebalancement de portefeuille alors
            if dtCalc == dtLastPrtf:
                #s'il n'y a pas encore de matrice de calcul
                if len(newMatCalc) ==0 :
                    newMatCalc = utils.GetLastPrtf(dfPrtfs,dfCours,dtCalc)
                    vPrtf.append(base)
                else:
                    oldMatCalc = newMatCalc
                    #Récupère la matrice comprenant les tickers et les poids de l'ancien prtf
                    #avec les cours correspondant à la date de calcul (dtCalc)
                    newMatCalc = utils.GetLastCours(oldMatCalc, dfCours, dtCalc)
                    
                    #Calcul la performance pondérée de chaque ligne
                    perfPrtf = sum((newMatCalc['COURS']/oldMatCalc['COURS'] - 1)*oldMatCalc['POIDS'])
                    
                    #Ajout du dernier cours du portefeuille 
                    derPrtfCours = vPrtf[len(vPrtf)-1]
                    derPrtfCours = derPrtfCours * (1+perfPrtf)
                    vPrtf.append(derPrtfCours)
                    
                    #Récupération du nouveau portefeuille
                    newMatCalc = utils.GetLastPrtf(dfPrtfs,dfCours,dtCalc)
            else:
                oldMatCalc = newMatCalc
                #Récupère la matrice comprenant les tickers et les poids de l'ancien prtf
                #avec les cours correspondant à la date de calcul (dtCalc)
                newMatCalc = utils.GetLastCours(oldMatCalc, dfCours, dtCalc)
                
                #Calcul la performance pondérée de chaque ligne
                perfPrtf = sum((newMatCalc['COURS']/oldMatCalc['COURS'] - 1)*oldMatCalc['POIDS'])
                
                #Ajout du dernier cours du portefeuille 
                derPrtfCours = vPrtf[len(vPrtf)-1]
                derPrtfCours = derPrtfCours * (1+perfPrtf)
                vPrtf.append(derPrtfCours)
                
                #Modification des poids au sein du nouveau portefeuille
                sNewPoids = newMatCalc['COURS']/oldMatCalc['COURS']*oldMatCalc['POIDS']
                
                #Rebasement des poids à 100
                sNewPoids = sNewPoids / sum(sNewPoids)
                sNewPoids.rename('POIDS', inplace=True)
                
                #Ajout des nouveaux poids à la nouvelle matrice de calcul
                newMatCalc.drop(labels='POIDS', axis=1, inplace=True)
                newMatCalc = pd.concat([newMatCalc,sNewPoids], axis=1)
    
        else:
            vPrtf.append(base)
        
        #Calcul du benchmark
        utils.AddBenchPerf(lBench,dfBench,dtCalc,base)
    
    vBench = [x for x,y in lBench]
        
    if args.graphique:
        
        plt.plot(vDates,vPrtf, label='PRTF')
        plt.plot(vDates,vBench, label='Bench')
        
        plt.title("PRTF vs Bench")
        
        plt.legend()
        plt.show()
    
    return vPrtf, vBench    
            
if __name__ == '__main__':
    Calc_Perf()