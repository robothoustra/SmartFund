# -*- coding: utf-8 -*-

import argparse
import pandas as pd
import numpy as np
import date_calc
import utils
import model_calcs
import csv
import time
import plot_prtf
import os

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
    parser.add_argument("-pu","--fichier_univers", help="Chemin vers le fichier des historiques de l'univers", type=str, default='./data/Histo_Univers.csv')
    parser.add_argument("-pc","--fichier_cours", help="Chemin vers le fichier des historiques de cours", type=str, default='./data/Histo_Cours.csv')
    parser.add_argument("-pb", "--fichier_bench", help="Chemin vers le fichier de l'historiqe du benchmark", type=str, default='./data/Histo_Bench.csv')
    parser.add_argument("-dd", "--date_debut", help="Date de début des calculs", type=str, default='01/12/2019')
    parser.add_argument("-df", "--date_fin", help="Date de fin des calculs", type=str, default='01/01/2020')
    parser.add_argument("-tper", "--type_periode_calc", help="Type de période pour les calculs", type=str, choices=['days','months','years'], default='months')
    parser.add_argument("-per", "--periodicite", help="Nombre de pédiodes pour chaque calcul de portefeuille", type=int, default=6)
    parser.add_argument("-tp", "--type_pas", help="type de pas entre chaque portefeuille", type=str, choices=['days','months','years'], default='months')
    parser.add_argument("-np", "--nb_pas", help="Nombre de pas entre chaque portefeuille", type=int, default=1)
    parser.add_argument("-nb", "--nb_titres", help="Nombre de titres dans le portefeuille", type=int, default=50)
    parser.add_argument("-nbt", "--nb_titres_turnover", help="Nombre de titres à changer chaque mois", type=int, default=5)
    parser.add_argument("-pna", "--prct_na", help="Pourcentage max de N/A dans l'historique", type=float, default=0.25)
    parser.add_argument("-wp", "--write_prtf", help="Écrit le(s) portefeuille(s) dans un fichier de sortie", type=bool, default=True)
    parser.add_argument("-wrm", "--write_rmks", help="Écrit dans le fichier de remarques", type=bool, default=True)
    parser.add_argument("-po", "--path_output", help="Chemin des fichiers de sortie", action=readable_dir, default='./output/')
    parser.add_argument("-v", "--verbosity", help="Mode verbeux", action="store_true", default=True)
    
    for key, value in kwargs.items():
        for action in parser._actions:
            if action.dest == key:
                action.choices = value
                action.default = value
                
    return parser
    
class Selection:

    def __init__(self, **kwargs):
        parser = load_arguments(**kwargs)
        self.args = parser.parse_args()
        self.dict_args = vars(self.args)
    
    def GetArgs(self):
        return self.dict_args
    
    def GetValueOfArg(self, arg):

        if arg in self.dict_args:
            return self.dict_args[arg]
        else:
            return None
    
    # L'algorithme calculera pour chaque mois le portefeuille contenant le nombre de titres spécifié.
    #La date indique la période du premier portefeuille calculé.
    #   Exemple 1 : pas mensuel, periode 6 mois, date_debut 01/12/2019 => le premier portefeuille aura comme date de fin le 31/11/2019 et donc si la période de calcul
    #                            est de 6 mois, les fichiers d'historique devront au moins contenir le 31/05/2019.
    #   Exemple 2 : pas hebdo et date_début 01/12/2019 => 
    #             ** Même chose si la date est le 31/12/2019... **
    
    def Get_PRTF(self,**kwargs):
    
        strCsvPrtf = 'prtfs.csv'
            
        args = self.args

        csvRmks = None
        csvRmkswriter = None
        
        if not args.write_rmks==True:
            strRmk = os.path.join(args.path_output.strip(), 'csvRmks.csv')
            csvRmks = open(strRmk,'w', newline='')
            csvRmkswriter = csv.writer(csvRmks, delimiter=';')
            csvRmkswriter.writerow(['DATE_CALC', 'TICKER','REMARQUE'])
        
        fstPrtf = True
        dfPrtf = pd.DataFrame(columns=['TICKER','SEMI_VAR','POIDS','DATE_PRTF']).set_index('TICKER')
        
        #Lecture des données
        dfUniv = pd.read_csv(args.fichier_univers,header=[0], sep=';', index_col=0, parse_dates=True)
        dfCours = pd.read_csv(args.fichier_cours,header=[0], sep=';',index_col=0, parse_dates=True)
        dfBench = pd.read_csv(args.fichier_bench, header=[0], sep=';',index_col=0, parse_dates=True)
        
        #Nétoyage des dataframe
        dfUniv = utils.CleanAndSortDF(dfUniv,sortIndex=True, supRowNaIndex=True, supColNaIndex=True)
        dfCours = utils.CleanAndSortDF(dfCours,sortIndex=True, supRowNaIndex=True,supColNaIndex=True)
        dfBench = utils.CleanAndSortDF(dfBench,sortIndex=True, supRowNaIndex=True,supColNaIndex=True)
        
        #Initialise l'objet "dates" avec la classe SetDates
        dates = date_calc.SetDates(args.date_debut, args.date_fin, args.type_pas, args.nb_pas, type_periode=args.type_periode_calc, periodicite=args.periodicite)
        
        seuilNA = (1-args.prct_na)
        dfLastPrtf= pd.DataFrame()
        
        while (dates.dateInterCalc() <= dates.dateFinCalc()):
            
            if args.verbosity == True:
                print('Composition du PRTF : {0}'.format(dates.dateInterCalc()))
                
            #Récupère les sous-dataframe concernant la période de calcul
            perUniv = utils.GetPerUnivers(dfUniv,dates.dateFinCalc())
            perCours = utils.CutBDD(dfCours,dates.dateDebPeriod(),dates.dateFinPeriod(),dfUniv=perUniv)
            perBench = utils.CutBDD(dfBench,dates.dateDebPeriod(),dates.dateFinPeriod())

            if len(perCours) != len(perBench):
                raise ValueError("nombre de lignes différent entre le vecteur du benchmark et la matrice des prix pour la date du {0:%d-%m-%Y}".format(dates.dateInterCalc()))
            
            #Nettoie les données
            perCours = utils.ApplyDataConstraint(perCours,seuilNA,dates.dateInterCalc(),csvRmkswriter)
    
            #Récupère la matrice de données nécessaire à la selection
            dfData = model_calcs.GetData(perCours, perBench)
    
            #Sélectionne les valeurs du portefeuille de la période
            dfLastPrtf = model_calcs.GetNextPrtf(dfLastPrtf,args.nb_titres,args.nb_titres_turnover, dfData,csvRmkswriter,dates.dateInterCalc())
            
            #Ajoute la colonne contenant la date du portefeuille
            dfLastPrtf.insert(len(dfLastPrtf.columns),'DATE_PRTF',dates.dateInterCalc())
                
            dfPrtf = dfPrtf.append(dfLastPrtf)
            #print(dates.dateInterCalc())
            
            #Passe à la prochaine période
            dates.nextStep()
    
        #Écrit les résultats dans un csv
        if args.write_prtf:
            if fstPrtf:
                dfPrtf.to_csv(args.path_output + strCsvPrtf, mode='w',header=True, sep=';', float_format='%.15f')
                fstPrtf=False
            else:
                dfPrtf.to_csv(args.path_output + strCsvPrtf, mode='a',header=False, sep=';', float_format='%.15f')
        
        return dfPrtf

if __name__ == '__main__':
    selection = Selection()
    dfPrtf = selection.Get_PRTF()