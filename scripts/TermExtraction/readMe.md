# Term Extraction
## GliNER term extraction
* Convert TEI-XML into plain text and parse each paragraph ( a check could be done on the input size : max size 512 tokens)
* Extract for each lesson the technological terms > List could be extended 
```
model = GLiNER.from_pretrained("urchade/gliner_base")
labels = ["technical terms","methodological"]
```
## Wikipedia Interlinking
Limited to EN/FR because of the usage of existing DBpedia Lookup Instance, for PT/ES a DBpedia Lookup must be hosted somewhere
* Query DBpedia Lookup FR/EN and catch DBpedia references
* Query DBpedia EN endpoint for getting equivalent in target languages
