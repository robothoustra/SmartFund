-Le script doit crééer des ordres en fonction du portefeuille réel et du portefeuille cible.
-La technique consiste à minimiser les écarts entre les poids réel et les poids cibles.
-Possibilité de rajouter des contraintes (cash, expo ...)
-Liste des contraintes :
	-Colonnes à récupérer (ticker, quantité, prix, poids, dec (décimalisable))
	-Titres décimalisables
	-Arrondi sur les quantités
- Gestion de la couverture

Colonnes Portefeuille réel (ancien protefeuille) :
	DATE_PRTF
	TICKER
	TYPE (ACTIONS, OBLIG ...)
	QUANTITE	

Colonnes Portefeuille théorique :
	DATE_PRTF
	TICKER
	POIDS
	PRIX (nouveaux)

NB : la date du portefeuille réel doit etre égale à celle du portefeuille théorique.

Doit fournir un fichier de contrainte : 
	col 1 = ticker
	col 2 = prix (pour une quantité)
	col 3 = décimalisable (booléen)
	col 4 = Min Qte

Montant à répartir entre les actifs.

Appliquer la méthode des moindres carré pour chaque catégorie d'actifs en fonction de la somme qui leur
ait attribuée.