import glob
import fasttext.util
from huggingface_hub import hf_hub_download
import numpy as np
import re
import lxml.etree as ET
import langid
import spacy


def download_model():
    hf_hub_download(repo_id="facebook/fasttext-fr-vectors", filename="model.bin")


def extract_text_from_xml_tei(path):
    print(path)
    tei_ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    tree = ET.parse(path)
    print(tree)
    text = tree.xpath("//tei:text", namespaces=tei_ns)
    lesson_text = ""
    for item in text[0].itertext():
        lesson_text += item
    if langid.classify(lesson_text)[0] != 'fr':
        lesson_text = ''
    return lesson_text
    

def alt_ident():
    model_path = hf_hub_download(repo_id="facebook/fasttext-fr-vectors", filename="model.bin")
    model = fasttext.load_model(model_path)
    all_text = ""
    for file in glob.glob("/home/mgl/Bureau/Travail/Communications_et_articles/humanistica_PH/data/tei_aligned/*/*.xml"):
        all_text += extract_text_from_xml_tei(file)
    punctuations = re.compile(r'["\.\!\?\(\):;_,\^\[\]]')
    splitted = re.split(punctuations, all_text)
    sursplitted = [string.split() for string in splitted]
    print(sursplitted)
    final_list = []
    for element in sursplitted:
        for subelement in element:
            final_list.append(subelement)
    final_list = list(set(final_list))

    # On ceralcule les similarites avec un autre mot-cle, pour faire l intersection ensuite
    full_sim = []
    for concept in ['programmation', 'ordinateur', 'code', 'numérique']:
        similarities = []
        for word in final_list:
            cosine_sim = cosine_similarity(word, concept, model)
            similarities.append([word, cosine_sim])
        similarities.sort(key=lambda x: x[1])
        filtered = [word for word, sim in similarities if sim > 0.2]
        full_sim.append(filtered)
    out_list = list(set.intersection(*map(set, full_sim)))
    out_list.sort()
    print(out_list)
    
    
    # We lemmatize the list
    nlp = spacy.load('fr_core_news_sm')
    lemmatized = []
    for element in out_list:
        doc = nlp(element)
        for d in doc:
            lemmatized.append(d.lemma_)
    lemmatized = list(set(lemmatized))
    lemmatized.sort()
    print("Final list: ")
    print(lemmatized)
    print(len(lemmatized))

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
    out_list = list(set.intersection(*map(set, full_sim)))
    out_list.sort()
    print(out_list)
    print(len(out_list))
    
    
def cosine_similarity(word1, word2, model):
    return np.dot(model[word1], model[word2]) / (np.linalg.norm(model[word1]) * np.linalg.norm(model[word2]))

    
    
if __name__ == '__main__':
    alt_ident()