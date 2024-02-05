import re
import csv
import glob
import fasttext.util
import gensim
from huggingface_hub import hf_hub_download
import numpy as np
import re
import keybert

def download_model():
    hf_hub_download(repo_id="facebook/fasttext-fr-vectors", filename="model.bin")
    

def ident():
    model_path = hf_hub_download(repo_id="facebook/fasttext-fr-vectors", filename="model.bin")
    model = fasttext.load_model(model_path)
    french_files = glob.glob("/home/mgl/Bureau/Travail/PH/jekyll/fr/lecons/*.md")
    concat_lessons = ""
    for file in french_files:
        with open(file, "r") as indiv_file:
            concat_lessons += indiv_file.read()
    punctuations = re.compile(r'["\.\!\?\(\):;_,\^\[\]]')
    splitted = re.split(punctuations, concat_lessons)
    sursplitted = [string.split() for string in splitted]
    print(sursplitted)
    final_list = []
    for element in sursplitted:
        for subelement in element:
            final_list.append(subelement)
    final_list = list(set(final_list))
    
    # TODO: essayer de faire 3 ou 4 fois la même chose sur 3
    #  termes différents; choisir un seuil de similarité, et faire l'intersection des listes 
    full_sim = []
    for concept in ['programmation', 'ordinateur', 'code']:
        similarities = []
        for word in final_list:
            cosine_sim = cosine_similarity(word, concept, model)
            similarities.append([word, cosine_sim])
        similarities.sort(key=lambda x:x[1])
        filtered = [word for word, sim in similarities if sim > 0.2]
        full_sim.append(filtered)
        
    print(list(set.intersection(*map(set, full_sim))))
    
    
def cosine_similarity(word1, word2, model):
    return np.dot(model[word1], model[word2]) / (np.linalg.norm(model[word1]) * np.linalg.norm(model[word2]))

    
    
if __name__ == '__main__':
    ident()