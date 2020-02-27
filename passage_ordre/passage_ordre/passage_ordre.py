import argparse
import pandas as pd
import numpy as np

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
    parser.add_argument("-ptf","--ptf_reel", help="Chemin vers le fichier contenant le dernier portefeuille",
                        type=str, default='./data/Histo_Univers.csv')

    for key, value in kwargs.items():
        for action in parser._actions:
            if action.dest == key:
                action.choices = value
                action.default = value
                
    return parser

def GetOrders(**kwargs):
    
    parser = load_arguments(**kwargs)
    args = parser.parse_args()
    
    #Liste des colonnes à récupérer dans le fichier du dernier portefeuille
    list_col = []
    
    #Lecture des données
    dfPtfReel = pd.read_csv(args.ptf_reel,header=[0], sep=';')
    
    