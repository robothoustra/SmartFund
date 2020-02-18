import Main
import time
import numpy as np
from multiprocessing import Pool, freeze_support

if __name__ == '__main__':
    start_time = time.time()
    freeze_support()
    pool = Pool()
    list_dict = []
    #nb_pas
    for i in [1,2,3]:
        #Périodicité
        for j in np.arange(3,13,3):
                #nb_titre_turnover
                for k in np.arange(3,11,1):
                    args = dict()
                    args['nb_pas'] = i
                    args['periodicite'] = j
                    args['nb_titres_turnover']=k

                    list_dict.append(args)
    
    #args = (x for x in list_dict)
    pool.map_async(Main.Get_PRTF,[x for x in list_dict])
    pool.close()
    pool.join()
    
    results = Main.GetDfResultBackTest()

    results.to_csv('resultat_backtest', mode='w',header=True, sep=';', float_format='%.15f')    
    print(results)
    print("--- %s seconds ---" % (time.time() - start_time))

