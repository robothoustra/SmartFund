import Selection
import PlotPrtf
import time
import numpy as np
import pandas as pd
from multiprocessing import Pool, freeze_support
import copy

dfResults = None

def CallBack(rslt):
    fieldnames, fields = *rslt
    if dfResults == None:
        dfResults = pd.DataFrame(date=fields, columns=fieldnames)
    else:
        dfResults.append(fields)
    
def worker(arg):
    return arg

def BackTest(args):
    selection = Selection.Selection(**d_args)
    dfPrtf = selection.Get_PRTF()
    args_select = selection.GetArgs()
    
    new_args = vars(args_select)
    args_perf = copy.deepcopy(new_args)
    args_perf['Portefeuilles'] = dfPrtf.reset_index()
            
    #Récupère les vecteurs de cours du portefeuille et du benchmark
    vPrtf, vBench = PlotPrtf.Calc_Perf(**args_perf)
        
    #Ecrit dans le fichier de sortie
    fieldnames=list(new_args.keys())
    fieldnames.append('Perf_PRTF')
    fieldnames.append('Perf_Bench')
    
    fields = list(new_args.values())
    fields.append(vPrtf[len(vPrtf)-1] / vPrtf[0] - 1)
    fields.append(vBench[len(vPrtf)-1] / vBench[0] - 1)
    
    CallBack(fieldnames, fields)
    #print(fieldnames)
    #print(fields)
    
if __name__ == '__main__':
    start_time = time.time()
    #freeze_support()
    #pool = Pool()
    list_dict = []
    #nb_pas
    #for i in [1,2,3]:
        #Périodicité
        #for j in np.arange(3,13,3):
                #nb_titre_turnover
    i = 1
    j = 6
    k = 5
    #for k in np.arange(3,11,1):
    d_args = dict()
    d_args['nb_pas'] = i
    d_args['periodicite'] = j
    d_args['nb_titres_turnover']=k

    list_dict.append(d_args)
    
    
    #args = (x for x in list_dict)
    #pool.map_async(Main.Get_PRTF,[x for x in list_dict])
    #pool.close()
    #pool.join()
    
    #list_selec = [Selection.Selection(**i_args) for i_args in list_dict]
    BackTest(d_args)
    
    d_args['periodicite'] = 9
    BackTest(d_args)
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

