from numpy import std, cov, var
import pandas as pd
from datetime import datetime

def GetCovarMat(stocks_mat, bench_vec):
    """ Retourne la série des covariances entre la matrice de variations des actifs et le vecteur de variations du benchmark """
    if len(stocks_mat) != len(bench_vec):
        raise ValueError("La matrice de variations des actifs comporte un nombre différent de lignes du vecteur de variation du benchmark")
    if str(type(stocks_mat)) != "<class 'pandas.core.frame.DataFrame'>" or str(type(bench_vec)) != "<class 'pandas.core.frame.DataFrame'>":
        raise TypeError('les deux matrices doivent être du même type : \'pandas.core.frame.DataFrame\' ')

    cov_mat = []
    cov_mat = [cov(stocks_mat.iloc[1:,i].values,bench_vec[1:].values.reshape(-1),ddof=0) for i in range(0,len(stocks_mat.columns))]
    return cov_mat

def GetData(perCours, perBench):
    # A ajouter : possibilité de passer dans les arguments (via des booléens)   
    # l'ajout d'autres colonnes au dataframe
    
    #Récupère l'intitulé des colonnes
    intitules = perCours.columns

    #Récupère la matrice de variations
    varCours = perCours.astype(float).pct_change()
    varBench = perBench.astype(float).pct_change()

    #Calcul de la Semi-variance (absolue)
    semivar_list = []
    for i in varCours:
        # Tester aussi en prenant la perf relative par rapport au bench : varBench.iloc[cpt - 1][0] - perf
        dfTemp = pd.concat([varCours[i],varBench],axis=1)
        dfTemp = dfTemp[(dfTemp[dfTemp.columns[0]]-dfTemp[dfTemp.columns[1]]<0) & (dfTemp[dfTemp.columns[1]]<0)]
        semivar_list.append(var(dfTemp[dfTemp.columns[0]]))

    #Mise sous forme de série
    dfData = pd.DataFrame(semivar_list,intitules)

    #Ajout des intitulés de colonne
    dfData.index.names = ['TICKER']
    dfData.columns = ['SEMI_VAR']
    
    return dfData



def GetNextPrtf(dfLastPrtf,nb_titres, nb_titres_turnover,dfData,csvRmkswriter,dtCalc, *args, **kwargs):
    
    #Turnover en fonction de la semi-variance et du nombre de turnover souhaité
    dfData.sort_values(by=['SEMI_VAR'],ascending=True, inplace=True)
    if (dfLastPrtf.empty):
        dfSelect = dfData.iloc[:nb_titres]
    else:
        #Attribue les nouvelles semi-variance aux titres déjà présent en prtf
        #Renvoie également un nombre de titre inférieur si certains ne font plus partie de l'univers.
        dfSelect = dfData.loc[dfLastPrtf.index]
        
        #Si le nombre de titre est inférieur, alors écrit une remarque
        #if len(dfSelect) !=  len(dfLastPrtf):
            #csvRmkswriter.writerow([datetime.strftime(dtCalc,'%d/%m/%Y'), '', str(len(dfLastPrtf)-len(dfSelect)) + ' Titres en prtf abs de l\'univ'])
        

        nbTitreAEnlever = max(len(dfSelect)-(nb_titres - nb_titres_turnover),0)
        #Enlève les nb_titres_turnover ayant la plus faible semi-variance
        dfSelect.sort_values(by=['SEMI_VAR'],ascending=True, inplace=True)
        dfSelect = dfSelect[:len(dfSelect)-nbTitreAEnlever]
        
        nbTitreAAjouter = nb_titres-len(dfSelect)
        #Ajoute les nb_titres_turnover ayant la plus haute semi-variance et n'étant pas 
        #   dans la liste des titres déjà en portefeuille.
        dfTitresPasEnPrtf = dfData[~dfData.index.isin(dfLastPrtf.index.values)]
        dfSelect = dfSelect.append(dfTitresPasEnPrtf.iloc[:nbTitreAAjouter])
        
        #csvRmkswriter.writerow([datetime.strftime(dtCalc,'%d/%m/%Y'), '', str(nbTitreAAjouter) + ' Nouveau titres'])
        
    if kwargs.get('rm_semivar',False):
        dfSelect.drop(['SEMI_VAR'], axis=1, inplace=True)
    
    #Attribution des poids
    dfSelect.insert(len(dfSelect.columns),'POIDS',1/len(dfSelect))
    
    return dfSelect

    