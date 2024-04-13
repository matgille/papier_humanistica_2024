import re
import numpy as np
import fasttext.util
from huggingface_hub import hf_hub_download
# from sentence_transformers import SentenceTransformer
# model = SentenceTransformer("all-MiniLM-L6-v2")



def cosine_similarity(expression_1, expression_2):
    return np.dot(expression_1, expression_2) / (np.linalg.norm(expression_1) * np.linalg.norm(expression_2))


def embed():
    pass

def collate(source_sent:list, target_sent:list, source_spans, max_MWE_length:int) -> list:
    """
    This function allows to collate two sentences, and to identify in the target sentence a mono or multiword expression
    :return: a list with the corresponding indices of the concepts 
    source_sent: the tokenized source sentence, as a list of words
    target_sent: the tokenized target sentence, as a list of words 
    source_spans: a list of tuple containing the index of the word[s] to find in the target sentence
    max_MWE_length: the maximum target length for the expression
    """
    
    # On va créer les expressions à comparer.
    compare_strings = []
    for n_gram in range(1, max_MWE_length + 1):
        for i in range(len(target_sent)):
            compare_strings.append(" ".join(target_sent[i:i+n_gram]))
    print(compare_strings)

    # model_path = hf_hub_download(repo_id="facebook/fasttext-fr-vectors", filename="model.bin")
    # model = fasttext.load_model(model_path)
    
    for begin_index, end_index in source_spans:
        corresponding_expression = " ".join(source_sent[begin_index: end_index])
        source_as_vectors = embed(corresponding_expression)
        print("Source sentence:" + " ".join(corresponding_expression))
        cosine_sims = []
        
        # On va cherche le terme le plus proche dans la cible à partir de la source
        # Il faudrait peut être trouver un encadrement pour gagner en précision. 
        for target_sent in compare_strings:
            target_as_vectors = embed(target_sent)
            cosine_sims.append(cosine_similarity(source_as_vectors, target_as_vectors))
        print(cosine_sims)
            
    

if __name__ == '__main__':
    source_sent = "It is possible to install all these dependencies without Anaconda (or with a lightweight alternative)"
    target_sent = "Il est possible d'obtenir toutes les librairies nécessaires sans installer Anaconda (ou en choisissant plutôt une alternative plus légère)"
    collate(source_sent.split(), target_sent.split(), max_MWE_length=7, source_spans=[(3,8)])