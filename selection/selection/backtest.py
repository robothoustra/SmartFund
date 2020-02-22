import Selection
import PlotPrtf
import time
import numpy as np
import pandas as pd
from multiprocessing import Pool, freeze_support
import copy



def CallBack(rslt):
    print(rslt[0])
    dfResults = dfResults.append(rslt[0])
    print('Callback')

def callback_error(result):
    print('error', result)
    
def BackTest(args):
    print(args)
    selection = Selection.Selection(**args)
    dfPrtf = selection.Get_PRTF()
    args_select = selection.GetArgs()
    
    new_args = vars(args_select)
    args_perf = copy.deepcopy(new_args)
    args_perf['Portefeuilles'] = dfPrtf.reset_index()
            
    #Récupère les vecteurs de cours du portefeuille et du benchmark
    vPrtf, vBench = PlotPrtf.Calc_Perf(**args_perf)
        
    #Ecrit dans le fichier de sortie
    #fieldnames=list(new_args.keys())
    #fieldnames.append('Perf_PRTF')
    #fieldnames.append('Perf_Bench')
    
    fields = list(new_args.values())
    fields.append(vPrtf[len(vPrtf)-1] / vPrtf[0] - 1)
    fields.append(vBench[len(vPrtf)-1] / vBench[0] - 1)
    
    return fields
    #print(fieldnames)
    #print(fields)
def test(num):
    return num
    
if __name__ == '__main__':
    start_time = time.time()

    fieldnames = ['fichier_univers', 'fichier_cours', 'fichier_bench','date_debut', 'date_fin',
                   'type_periode_calc','periodicite', 'type_pas', 'nb_pas', 'nb_titres',
                   'nb_titres_turnover', 'prct_na', 'write_prtf', 'Perf_PRTF', 'Perf_Bench']
    #dfResults = pd.DataFrame(columns=fieldnames)
    #freeze_support()
    pool = Pool()
    
    list_dict = []
    #nb_pas
    #for i in [1,2,3]:
        #Périodicité
        #for j in np.arange(3,13,3):
                #nb_titre_turnover
    i = 1
    j = 6
    #k = 5
    #for k in np.arange(3,11,1):
    for k in [3,40]:
        d_args = dict()
        d_args['nb_pas'] = i
        d_args['periodicite'] = j
        d_args['nb_titres_turnover']=k

        list_dict.append(d_args)
    
    #list_selec = [Selection.Selection(**i_args) for i_args in list_dict]
    result = pool.map_async(BackTest,list_dict, error_callback=callback_error)
    result.wait()
    
    dfResults = pd.DataFrame(result.get(),columns=fieldnames)
    #GetResultatsCalcPerf(fieldnames,fields)
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


    #results.to_csv('resultat_backtest', mode='w',header=True, sep=';', float_format='%.15f')    
    print(dfResults)
    
    print("--- %s seconds ---" % (time.time() - start_time))

