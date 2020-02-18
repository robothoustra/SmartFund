# -*- coding: utf-8 -*-

import argparse
import pandas as pd
import numpy as np
import dateCalc
import utils
import Model_Calcs
import csv
import time
import PlotPrtf


def load_arguments(**kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument("-pu","--fichier_univers", help="Chemin vers le fichier des historiques de l'univers", type=str, default=r'C:\Users\alexi\Dropbox\Informatique\Blockchain\Projet Smart Funds\Programmation\SmartFund\selection\test\data\Histo_Univers.csv')
    parser.add_argument("-pc","--fichier_cours", help="Chemin vers le fichier des historiques de cours", type=str, default=r'C:\Users\alexi\Dropbox\Informatique\Blockchain\Projet Smart Funds\Programmation\SmartFund\selection\test\data\Histo_Cours.csv')
    parser.add_argument("-pb", "--fichier_bench", help="Chemin vers le fichier de l'historiqe du benchmark", type=str, default=r'C:\Users\alexi\Dropbox\Informatique\Blockchain\Projet Smart Funds\Programmation\SmartFund\selection\test\data\Histo_Bench.csv')
    parser.add_argument("-dd", "--date_debut", help="Date de début des calculs", type=str, default='01/01/2016')
    parser.add_argument("-df", "--date_fin", help="Date de fin des calculs", type=str, default='01/01/2020')
    parser.add_argument("-tper", "--type_periode_calc", help="Type de période pour les calculs", type=str, choices=['days','months','years'], default='months')
    parser.add_argument("-per", "--periodicite", help="Nombre de pédiodes pour chaque calcul de portefeuille", type=int, default=6)
    parser.add_argument("-tp", "--type_pas", help="type de pas entre chaque portefeuille", type=str, choices=['days','months','years'], default='months')
    parser.add_argument("-np", "--nb_pas", help="Nombre de pas entre chaque portefeuille", type=int, default=1)
    parser.add_argument("-nb", "--nb_titres", help="Nombre de titres dans le portefeuille", type=int, default=50)
    parser.add_argument("-nbt", "--nb_titres_turnover", help="Nombre de titres à changer chaque mois", type=int, default=5)
    parser.add_argument("-pna", "--prct_na", help="Pourcentage max de N/A dans l'historique", type=float, default=0.25)
    parser.add_argument("-perf", "--calc_perf", help="Calcul la performance du ou des portefeuilles", action="store_true", default=False)
    parser.add_argument("-of", "--output_file", help="Fichier de sortie si -v actif", default="Ouput_Perf.csv")
    parser.add_argument("-wp", "--write_prtf", help="Écrit le(s) portefeuille(s) dans un fichier de sortie", action="store_true", default=False)

    for key, value in kwargs.items():
        for action in parser._actions:
            if action.dest == key:
                action.choices == value
                
    return parser

# L'algorithme calculera pour chaque mois le portefeuille contenant le nombre de titres spécifié.
#La date indique la période du premier portefeuille calculé.
#   Exemple 1 : pas mensuel, periode 6 mois, date_debut 01/12/2019 => le premier portefeuille aura comme date de fin le 31/11/2019 et donc si la période de calcul
#                            est de 6 mois, les fichiers d'historique devront au moins contenir le 31/05/2019.
#   Exemple 2 : pas hebdo et date_début 01/12/2019 => 
#             ** Même chose si la date est le 31/12/2019... **

dfResultats = pd.DataFrame()

def Get_PRTF(**kwargs):

    strCsvPrtf = 'prtfs.csv'
        
    parser = load_arguments(**kwargs)
    args = parser.parse_args()
        
    with open('csvRmks.csv','w', newline='') as csvRmks:
        fstPrtf = True
        csvRmkswriter = csv.writer(csvRmks, delimiter=';')
        csvRmkswriter.writerow(['DATE_CALC', 'TICKER','REMARQUE'])
        dfPrtf = pd.DataFrame(columns=['TICKER','SEMI_VAR','POIDS','DATE_PRTF']).set_index('TICKER')
        
        dfUniv = pd.read_csv(args.fichier_univers,header=[0], sep=';', index_col=0, parse_dates=True)
        dfCours = pd.read_csv(args.fichier_cours,header=[0], sep=';',index_col=0, parse_dates=True)
        dfBench = pd.read_csv(args.fichier_bench, header=[0], sep=';',index_col=0, parse_dates=True)
        
        dfUniv = utils.CleanAndSortDF(dfUniv,sortIndex=True, supRowNaIndex=True, supColNaIndex=True)
        dfCours = utils.CleanAndSortDF(dfCours,sortIndex=True, supRowNaIndex=True,supColNaIndex=True)
        dfBench = utils.CleanAndSortDF(dfBench,sortIndex=True, supRowNaIndex=True,supColNaIndex=True)
        
        #Initialise l'objet "dates" avec la classe SetDates
        dates = dateCalc.SetDates(args.date_debut, args.date_fin, args.type_pas, args.nb_pas, type_periode=args.type_periode_calc, periodicite=args.periodicite)
        
        seuilNA = (1-args.prct_na)
        dfLastPrtf= pd.DataFrame()
        
        while (dates.dateInterCalc() <= dates.dateFinCalc()):
            
            perUniv = utils.GetPerUnivers(dfUniv,dates.dateFinCalc())
            perCours = utils.CutBDD(dfCours,dates.dateDebPeriod(),dates.dateFinPeriod(),dfUniv=perUniv)
            perBench = utils.CutBDD(dfBench,dates.dateDebPeriod(),dates.dateFinPeriod())
        
            if len(perCours) != len(perBench):
                raise ValueError("nombre de lignes différent entre le vecteur du benchmark et la matrice des prix pour la date du {0:%d-%m-%Y}".format(dates.dateInterCalc()))
            
            #Nettoie les données
            perCours = utils.ApplyDataConstraint(perCours,seuilNA,dates.dateInterCalc(),csvRmkswriter)
    
            #Récupère la matrice de données nécessaire à la selection
            dfData = Model_Calcs.GetData(perCours, perBench)
    
            #Sélectionne les valeurs du portefeuille de la période
            dfLastPrtf = Model_Calcs.GetNextPrtf(dfLastPrtf,args.nb_titres,args.nb_titres_turnover, dfData,csvRmkswriter,dates.dateInterCalc())
            
            #Ajoute la colonne contenant la date du portefeuille
            dfLastPrtf.insert(len(dfLastPrtf.columns),'DATE_PRTF',dates.dateInterCalc())
                
            dfPrtf = dfPrtf.append(dfLastPrtf)
            print(dates.dateInterCalc())
            #Passe à la prochaine période
            dates.nextStep()

        #Écrit les résultats dans un csv
        if args.write_prtf:
            if fstPrtf:
                dfPrtf.to_csv(strCsvPrtf, mode='w',header=True, sep=';', float_format='%.15f')
                fstPrtf=False
            else:
                dfPrtf.to_csv(strCsvPrtf, mode='a',header=False, sep=';', float_format='%.15f')
    
    if args.calc_perf:   
        
        #Si on a choisi de ne pas écrire les portefeuilles calculés dans un fichier,
        #Il faut alors ajouter l'ensemble des portefeuilles contenu dans dfPrtf en argument
        dict_args = args.__dict__
        if args.write_prtf==False:
            dict_args['Portefeuilles'] = dfPrtf
            
        #Récupère les vecteurs de cours du portefeuille et du benchmark
        vPrtf, vBench = PlotPrtf.Calc_Perf(**dict_args)
        
        #Ecrit dans le fichier de sortie
        fieldnames=list(args.__dict__.keys())
        fieldnames.append('Perf_PRTF')
        fieldnames.append('Perf_Bench')
        
        fields = args.__dict__
        fields['Perf_PRTF'] = vPrtf[len(vPrtf)-1] / vPrtf[0] - 1
        fields['Perf_Bench'] = vBench[len(vPrtf)-1] / vBench[0] - 1 
        
        if len(dfResultats) == 0:
            dfResultats.columns = fieldnames
        dfResultats = dfResultats.append(fields)
        
        print(fields)
        #with open(args.output_file,'a+', newline='') as out_file:
        #    out_file_writer = csv.DictWriter(out_file, fieldnames=fieldnames, delimiter=';')
             #Met le pointeur en début de fichier
        #    out_file.seek(0)
            
             #S'il n'y a rien, écrit les headers
        #    if out_file.readline() == '':
        #        out_file_writer.writeheader()
        #    else:
        #        out_file.seek(0,2)
                
        #    out_file_writer.writerow(fields)

def GetDfResultBackTest():
    return dfResultats

if __name__ == '__main__':
    Get_PRTF()
    