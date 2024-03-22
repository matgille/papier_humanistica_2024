#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 08:40:38 2024

@author: cringwal
"""
import json
import requests
from Levenshtein import distance
import operator
from SPARQLWrapper import SPARQLWrapper, JSON
import re

with open("/user/cringwal/home/Desktop/ProgrammingHistorian/papier_humanistica_2024-main/data/term_extracted/1shot.json",encoding="utf-8") as json_file:
   results_data = json.load(json_file) 

# as per recommendation from @freylis, compile once only
CLEANR = re.compile('<.*?>') 

def cleanhtml(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def getDBpedia(term,lang):
    #term="machine learning"
    #lang="en"
    term=term.lower()
    data={"query":term,"format":"json"}
    if(lang=="fr"):
        url="https://fr.dbpedia.org/lookup/api/search"
    if(lang=="en"):
        url="https://lookup.dbpedia.org/api/search"
        
    r=requests.get(url, data)
    try:
        results=r.json()
        new_res=[]
        for res in results["docs"]:
            temp=res
            label=cleanhtml(res["label"][0])
            dist=distance(label, term)
            temp["dist"]=dist
            new_res.append(temp)
        new_res.sort(key=operator.itemgetter('dist'))
        if(new_res[0]["dist"]<3):
            return new_res[0]
        else:
            return None
    except:
        return None

def getDBpediaEquiv(uri_ref,lang_dest):
    
    #uri_ref='http://dbpedia.org/resource/Natural_language_processing'
    #lang_dest="fr"
    sparql = SPARQLWrapper(
        "https://dbpedia.org/sparql"
    )
    sparql.setReturnFormat(JSON)
 
    # gets the first 3 geological ages
    # from a Geological Timescale database,
    # via a SPARQL endpoint
    if(lang_dest=="en"):
        lang_pattern="http://dbpedia"
        query="""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT ?s 
            WHERE 
            {
               ?s owl:sameAs  <"""+uri_ref+""">.
               FILTER CONTAINS(str(?s), '"""+lang_pattern+"""') 
               
            }
            """
    elif(lang_dest=="fr"):
        lang_pattern="fr.dbpedia"
        
        query="""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            SELECT ?s
            WHERE 
            {
               <"""+uri_ref+"""> owl:sameAs  ?s.
               FILTER CONTAINS(str(?s), '"""+lang_pattern+"""')
            }
            """

    query=query.replace("   ","").replace("\n"," ")
    print(query)
    sparql.setQuery(query)
    result_ressource=None
    try:
        ret = sparql.queryAndConvert()
        result_ressource=ret["results"]["bindings"][0]["s"]["value"]
    except Exception as e:
        print(e)
    return result_ressource


def DBpediaToWikipedia(uri):
    return uri.replace("dbpedia","wikipedia").replace("resource","wiki")
    

dict_wikipedia_ref={}
for less  in results_data.keys():
    for lang in results_data[less]:
        #if(lang=="en"):
        if(lang not in dict_wikipedia_ref.keys()):
            dict_wikipedia_ref[lang]={}
        if(lang=="fr"):
            lang_dest="en"
        if(lang=="en"):
            lang_dest="fr"
        for term in results_data[less][lang].keys():
            if(term not in dict_wikipedia_ref[lang].keys()):
                print(term)
                dict_wikipedia_ref[lang][term]={"wikipedia_uri":None,"wikipedia_equiv_uri":None}
                dbpedia_res=getDBpedia(term,lang)
                try:
                    dbpedia_uri=dbpedia_res["resource"][0]
                    if(dbpedia_uri):            
                        print("found dbpedia")
                        wikipedia_uri=DBpediaToWikipedia(dbpedia_uri)
                        dict_wikipedia_ref[lang][term]["wikipedia_uri"]=wikipedia_uri
                        equiv_uri=getDBpediaEquiv(dbpedia_uri,lang_dest)
    
                        if(equiv_uri):
                            print("found equiv")
                            equiv_wikipedia_uri=DBpediaToWikipedia(equiv_uri)
                            dict_wikipedia_ref[lang][term]["wikipedia_equiv_uri"]=equiv_wikipedia_uri
                except Exception as e:
                    print(e)
                        
with open("/user/cringwal/home/Desktop/ProgrammingHistorian/papier_humanistica_2024-main/data/term_extracted/1shot.json", 'w', encoding='utf-8')  as f:
     json.dump(dict_results, f)
     
     