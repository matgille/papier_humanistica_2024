# Microtextual collation


## Tokenization

Script: **sentences_tokenization.py**

*Input*: `../../data/tei_aligned/main.xml`

*Ouput*: `../../data/tei_sentences_tokenized/main.xml`

The data is gathered from `../../data/tei_aligned`. Each lesson is 
first tokenized by word and then by punctuation (only strong punctuation is used: `?¿!¡.`)
Each sentence is represented as a `s` node, which is identified by a unique ID.


**Todo:** the `s` element cannot appear in some nodes (`desc` for instance). To be fixed.



## Sentence alignment

Script: **sentences_alignment.py**

*Input*: `../../data/tei_sentences_tokenized/main.xml`

*Ouput*: `../../data/aligned_sentences/main.xml`


For each lesson the model is aligned with its translations. For now the translations
are not aligned between them.