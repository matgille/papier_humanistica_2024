#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 21:52:23 2024

@author: cringwal
"""

import os 
import os.path
from gliner import GLiNER

import lxml.etree as ET
struct_files_path="/user/cringwal/home/Desktop/ProgrammingHistorian/papier_humanistica_2024-main/data/to_tei/struct_aligned"

model = GLiNER.from_pretrained("urchade/gliner_base")
labels = ["technical terms","methodological"]
dict_results={}
dir_lessons=os.listdir(struct_files_path)
for dir_less in dir_lessons:
    print("-----------------------------", dir_less)
    dict_results[dir_less]={}
    lesson_current=os.path.join(struct_files_path,dir_less)
    dir_versions=os.listdir(lesson_current)
    for version in dir_versions:
        version_path=os.path.join(lesson_current,version)
        tree = ET.parse(version_path) 
        text = tree.findall('//{https://tei-c.org/ns/1-0/}text')
        LANG=text[0].attrib['{http://www.w3.org/XML/1998/namespace}lang']
        dict_results[dir_less][LANG]={}
        print("============> ", LANG)
        
        entity_dict={}
        for body in text[0]:
            for div in body:
                #print(div.tag)
                #print(div.attrib)
                
                content=""
                for p in div:
                    current_txt=''.join(p.itertext())
                    #print(p.tag)
                    if("{https://tei-c.org/ns/1-0/}head"==p.tag):
                        content=current_txt+" \n "
                     #   print("HEY")
                    else:
                        content+=current_txt
                try:
                    entities = model.predict_entities(content, labels, threshold=0.2)
                    new_entities= list(set([ent["text"] for ent in entities]))
                    for new_ent in new_entities:
                        if(new_ent not in entity_dict.keys()):
                            entity_dict[new_ent]=1
                        entity_dict[new_ent]+=1
                except:
                    print("PB with GLiner")
        dict_results[dir_less][LANG]=entity_dict
        print(entity_dict)
import json
with open("/user/cringwal/home/Desktop/ProgrammingHistorian/papier_humanistica_2024-main/data/term_extracted/1shot.json", 'w', encoding='utf-8')  as f:
     json.dump(dict_results, f)
     
     