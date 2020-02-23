import Selection
import PlotPrtf
import time
import numpy as np
import pandas as pd
from multiprocessing import Pool, freeze_support, Value
import copy

fieldnames = ['fichier_univers', 'fichier_cours', 'fichier_bench','date_debut', 'date_fin',
               'type_periode_calc','periodicite', 'type_pas', 'nb_pas', 'nb_titres',
               'nb_titres_turnover', 'prct_na', 'Perf_PRTF', 'Perf_Bench']

def callback_error(result):
    print('error', result)

def init(args):
    ''' store the counter for later use '''
    global counter
    counter = args


def BackTest(args):
    #print(args)
    selection = Selection.Selection(**args)
    dfPrtf = selection.Get_PRTF()
    
    new_args = selection.GetArgs()
    args_perf = copy.deepcopy(new_args)
    args_perf['Portefeuilles'] = dfPrtf.reset_index()
            
    #Récupère les vecteurs de cours du portefeuille et du benchmark
    perfOutput = PlotPrtf.Calc_Perf(**args_perf)
    
    #La valeur des arguments correspondants aux champs de sortie (fieldnames)
    fields = []
    for arg in fieldnames:
        value = selection.GetValueOfArg(arg)
        if not value is None:
            fields.append(value)
    
    for cle in perfOutput:
        if cle in fieldnames:
            fields.append(perfOutput[cle])
    
    global counter
    # += operation is not atomic, so we need to get a lock:
    with counter.get_lock():
        counter.value += 1
    print(counter.value)

    return fields
    
if __name__ == '__main__':
    start_time = time.time()

    #dfResults = pd.DataFrame(columns=fieldnames)
    freeze_support()
    counter = Value('i', 0)

    pool = Pool(processes=4, initializer = init, initargs = (counter, ))
    
    list_dict = []
    #nb_pas
    for i in [1,2,3]:
        #Périodicité
        for j in np.arange(3,13,3):
            #nb_titre_turnover
            for k in np.arange(3,11,1):
                d_args = dict()
                d_args['write_prtf'] = False
                d_args['write_rmks'] = False
                d_args['date_debut'] = '01/01/2016'
                d_args['date_fin'] = '01/01/2020'
                d_args['nb_pas'] = i
                d_args['periodicite'] = j
                d_args['nb_titres_turnover']=k

                list_dict.append(d_args)
    
    print(len(list_dict))
    result = pool.map_async(BackTest,list_dict, error_callback=callback_error)
    result.wait()
    
    dfResults = pd.DataFrame(result.get(),columns=fieldnames)
    
    dfResults.to_csv('./output/resultat_backtest.csv', mode='w',header=True, sep=';', float_format='%.15f')    
    print(dfResults)
    
    print("--- %s seconds ---" % (time.time() - start_time))

