# Macro Alignment

## Première étape: alignement par la structure

On peut dans certains cas arriver à aligner de façon globale 
(à la division d'abord) en s'intéressant à la seule structure 
des documents, en présupposant que la personne qui traduit va
respecter cette structure. 

En faisant des tests, il apparaît que de nombreuses leçons
contiennent des différences structurelles par rapport à la leçon
d'origine:
1. soit parce qu'il s'agit d'une erreur
2. soit en raison d'un choix de traduction/éditorial

Pour 1), il s'agit en général de niveaux de titre qui sont 
erronés.


## Solution au problème 1.
On corrige (dans une branche à part) les problèmes 
d'hétérogénéité et on continue le processus. On peut 
commencer par faire cela pour les groupes de leçon qui
contiennent une traduction française.

On pourra proposer par la suite un ensemble de PR qui 
seront acceptées ou pas par les équipes disciplinaires.

## Solution au problème 2.

On ne pourra pas aller aussi loin que pour 1, en particulier, on ne pourra pas
aligner les structures automatiquement. Il faudra alors travailler à l'alignement à la phrase
en ne prenant pas en compte la structure.


## Autres problèmes

```markdown
Suggested Readings
------------------
```
Apparaît dans `working-with-web-pages.md`; une façon de 
structurer le texte qui n'est pas dans le jeu de règles
orthotypographiques et de mise en page de Programming
Historian. C'est considéré comme un titre de niveau 2 
(https://www.markdownguide.org/basic-syntax/). 
Je convertis ces structures quand je les identifie.