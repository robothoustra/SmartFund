# -*- coding: utf-8 -*-

import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta        
from numpy import std, cov, var
import csv

def GetDerJourMois(dateMois, jourOuvre):
    dateTemp = datetime.strptime("1/" + datetime.strftime(dateMois,'%m/%Y'),'%d/%m/%Y')
    dateTemp = dateTemp - relativedelta(days=1)
    
    if jourOuvre == True:
        while dateTemp.weekday() == 5 or dateTemp.weekday() == 6:
            dateTemp = dateTemp - relativedelta(days=1)
        
    return dateTemp

def CutBDD(df, DateMin, DateMax, *args, **kwargs):
    #Rajouter si filtreCol alors filtrer les colonnes (dfUniv)
    
    lastDate = df.index[len(df.index)-1].to_pydatetime()
    fstDate = df.index[0].to_pydatetime()

    if fstDate > DateMin:
        raise ValueError("L\'historique n\'est pas assez long:\nDate de debut {0:%d-%m-%Y} inférieure à la première date du fichier : {1:%d-%m-%Y}".format(DateMin,fstDate))
    elif  lastDate < DateMax:
        raise ValueError("L\'historique n\'est pas assez long:\nDate de fin {0:%d-%m-%Y} supérieure à la dernière date du fichier : {1:%d-%m-%Y}".format(DateMax,lastDate))
    
    dfUniv = kwargs.get('dfUniv',None)

    dfCut = df[(df.index <= DateMax) & (df.index >= DateMin)]
    
    if (dfUniv is not None):
        dfCut = dfCut[dfUniv[dfUniv.columns[0]].values]
    
    return dfCut


def GetPerUnivers(dfUniv,dtFin):
    """ renvoi la liste des titres de l'univers dont la date est antérieure ou égale et la plus proche
        de la date de fin de période. """
    perUniv = dfUniv[(dfUniv.index <= dtFin)]
    perUniv = perUniv[(perUniv.index == perUniv.index.max())]
    return perUniv
    
def CleanAndSortDF(df, *args, **kwargs):
    
    dfClean = df
    
    supRowNaIndex = kwargs.get('supRowNaIndex',False)
    supColNaIndex = kwargs.get('supColNaIndex',False)
    sortIndex = kwargs.get('sortIndex', False)
    
    if (supRowNaIndex):
        dfClean = dfClean.dropna(axis=0,how='all')
    
    if (supColNaIndex):
        dfClean = dfClean.dropna(axis=1,how='all')
        
    if (sortIndex):
        dfClean = dfClean.sort_index(axis=0, ascending=True)
    
    return dfClean

def ApplyDataConstraint(df, seuilNA, dtCalc,csvRmkswriter, **kwargs):
    
        #=============Suprime les colonnes ayant un trop grand nombre de 'NaN'======================
        toleranceNA = int(len(df)*seuilNA)
        newDF = df.dropna(axis=1, thresh=toleranceNA)
        only_na = df.columns[~df.columns.isin(newDF.columns)]
        if not csvRmkswriter is None:
            for ticker in only_na:
                csvRmkswriter.writerow([datetime.strftime(dtCalc,'%d/%m/%Y'), ticker, 'Nombre de N/A sup au seuil (' + str((1-seuilNA)) + ')'])
        #===========================================================================================
        
        #Lisse les données manquantes
        df.fillna(method='ffill', inplace=True)
        #df.fillna(method='bfill', inplace=True)

        return newDF
    
def RemoveZeroVariance(dfCours,dfVar,dtCalc,csvRmkswriter, **kwargs):
        #Enlève toutes les columns de la matrice dfVar et dfCOurs ayant une variance de 0
        col_sup = []
        for i in dfVar:
            if var(dfVar[i]) == 0:
                col_sup.append(i[0])
                if not csvRmkswriter is None:
                    csvRmkswriter.writerow([dtCalc, i[0], 'Variance=0'])
                 
        if (not len(col_sup)==0):
            dfVar.drop(col_sup, axis=1, level=0, inplace=True)
            dfCours.drop(col_sup, axis=1, level=0, inplace=True)
            if not csvRmkswriter is None:
                for ticker in col_sup:
                    csvRmkswriter.writerow([datetime.strftime(dtCalc,'%d/%m/%Y'), ticker, 'variance égale à zero'])

def GetLastPrtf(dfPrtfs,dfCours,dtCalc):
    """ Fonction renvoyant la matrice du dernier portefeuille connu avec les poids et cours """
    
    #Récupère le dernier portefeuille
    dfPrtf = dfPrtfs[['TICKER','POIDS']].loc[dfPrtfs['DATE_PRTF']==dtCalc]
    dfPrtf.set_index('TICKER',inplace=True)
    
    #Stock la date des cours la plus proche de la dtCalc
    dtMaxCours = max(dfCours[dfCours.index<=dtCalc].index)
    
    #Récupère les cours de chaque ligne du portefeuille à la dtMaxCours
    dfCoursDtCalc = dfCours[(dfCours.index == dtMaxCours)]
    dfCoursDtCalc = dfCoursDtCalc[dfPrtf.index].stack().to_frame()
    dfCoursDtCalc.reset_index(level=dfCoursDtCalc.columns[0], inplace=True)
    dfCoursDtCalc.drop(dfCoursDtCalc.columns[0], axis=1, inplace=True)
    
    #Joint le dataframe du portefeuille (matCalc) et celle des cours
    matCalc = pd.concat([dfPrtf,dfCoursDtCalc], axis=1)
    matCalc.rename(columns = {matCalc.columns[1] : 'COURS'}, inplace=True)
    
    return matCalc

def GetLastCours(dfPrtf,dfCours,dtCalc):
    
    #Stock la date des cours la plus proche de la dtCalc
    dtMaxCours = max(dfCours[dfCours.index<=dtCalc].index)
    
    #Récupère les cours de chaque ligne du portefeuille à la dtMaxCours
    dfCoursDtCalc = dfCours[(dfCours.index == dtMaxCours)]
    dfCoursDtCalc = dfCoursDtCalc[dfPrtf.index].stack().to_frame()
    dfCoursDtCalc.reset_index(level=dfCoursDtCalc.columns[0], inplace=True)
    dfCoursDtCalc.drop(dfCoursDtCalc.columns[0], axis=1, inplace=True)
    
    #Supprime l'ancienne colonne des cours et ajoute la nouvelle
    dfTemp = dfPrtf.drop(labels='COURS', axis=1)
    matCalc = pd.concat([dfTemp,dfCoursDtCalc], axis=1)
    matCalc.rename(columns = {matCalc.columns[1] : 'COURS'}, inplace=True)
    
    return matCalc

def AddBenchPerf(lBench,dfBench,dtCalc,base):
    
    #Stock la date des cours la plus proche de la dtCalc
    dtMaxCours = max(dfBench[dfBench.index<=dtCalc].index)
    
    #Récupère le cours du benchmark correspondant à la dtMaxCours
    dfCoursDtCalc = dfBench[(dfBench.index == dtMaxCours)]
    t1_bench = dfCoursDtCalc.values.item(0)
    
    if (len(lBench) == 0):
        t = (base, t1_bench)

    else:
        last_t = lBench[len(lBench)-1]
        t0_bench = last_t[1]
        new_bench = last_t[0] * t1_bench / t0_bench
        t = (new_bench, t1_bench)

    lBench.append(t)