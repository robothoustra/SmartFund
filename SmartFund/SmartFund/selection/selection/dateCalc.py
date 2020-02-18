# -*- coding: utf-8 -*-

import os
from numpy import std, cov, var
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, YEARLY, MONTHLY, DAILY
    
class SetDates:
    """ Classe gérant les dates utiles au calcul de chaque période. """
    
    """La date indique la période du premier portefeuille calculé."""        
    
    """ VOIR dateutil : https://dateutil.readthedocs.io/en/stable/ """
    
    def __init__(self, dtDeb, dtFin, type_pas, nb_pas, *args, **kwargs):
        self.type_pas = type_pas
        self.nb_pas = nb_pas
        self.dtInterCalc = datetime.strptime(dtDeb,'%d/%m/%Y')
        self.dtFinCalc = datetime.strptime(dtFin,'%d/%m/%Y')
        self.dtDebCalc = datetime.strptime(dtDeb,'%d/%m/%Y') 
        
        self.type_periode = kwargs.get('type_periode',None)
        self.periodicite = kwargs.get('periodicite',None)
        if not (self.periodicite is None or self.type_periode is None):
            self.dtFinPeriod = datetime.strptime(dtDeb,'%d/%m/%Y') + relativedelta(days=-1)
            self.dtDebPeriod = datetime.strptime(dtDeb,'%d/%m/%Y') + relativedelta(**{self.type_periode: -int(self.periodicite)}) + relativedelta(days=-1)
        
    def nextStep(self):
        """ La date de fin de période se déduit toujours à partir de la dtInterCalc
        qui est la date de début (date_debut) incrémentée du pas.
        On lui retranche 1 jour pour avoir la date de fin de période. """
        
        self.dtInterCalc = self.dtInterCalc + relativedelta(**{self.type_pas: int(self.nb_pas)})
        self.dtFinPeriod = self.dtInterCalc + relativedelta(days=-1)
        self.dtDebPeriod = self.dtFinPeriod + relativedelta(**{self.type_periode: -int(self.periodicite)})
        
    def GetDateListe(self):
        if (self.type_pas == 'years'):
            rFreq = YEARLY
        elif (self.type_pas == 'months'):
            rFreq = MONTHLY
        elif (self.type_pas == 'days'):
            rFreq = DAILY
        
        return list(rrule(freq=rFreq, dstart=self.dtDebCalc, until=self.dtFinCalc))
        
    def dateFinCalc(self):
        return self.dtFinCalc
    
    def dateInterCalc(self):
        return self.dtInterCalc
    
    def dateDebPeriod(self):
        #lever une erreur si periode=None
        return self.dtDebPeriod
    
    def dateFinPeriod(self):
        #lever une erreur si periode=None
        return self.dtFinPeriod
    
    def periodicite(self):
        #lever une erreur si periode=None
        return self.periodicite

