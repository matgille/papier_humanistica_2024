import copy
import os
import random
import re
import json
import sys
import langid 
import bertalign.utils as utils

def syntactic_tokenization(path, corpus_limit=None, use_punctuation=True):
    name = path.split("/")[-1].split(".")[0]
    with open(path, "r") as input_text:
        text = input_text.read().replace("\n", " ")

    text = utils.normalize_text(text)
    codelang, _ = langid.classify(text[:300])
    print(text)
    print(codelang)
    with open("bertalign/delimiters.json", "r") as input_json:
        dictionary = json.load(input_json)
    # Il ne reconnaît pas toujours le castillan
    if codelang == "an":
        codelang = "es"
    
    single_tokens_punctuation = [punct for punct in dictionary[codelang]['punctuation'] if len(punct) == 1]
    multiple_tokens_punctuation = [punct for punct in dictionary[codelang]['punctuation'] if len(punct) != 1]
    single_token_punct = "".join(single_tokens_punctuation)
    multiple_tokens_punct = "|".join(multiple_tokens_punctuation)
    punctuation_subregex = f"{multiple_tokens_punct}|[{single_token_punct}]"
    if use_punctuation:
        tokens_subregex = "(" + " | ".join(dictionary[codelang]['word_delimiters']) + " |" + punctuation_subregex + ")"
    else:
        tokens_subregex = "(" + " | ".join(dictionary[codelang]['word_delimiters']) + ")"
    print(tokens_subregex)
    delimiter = re.compile(tokens_subregex)
    search = re.search(delimiter, text)
    tokenized_text = []
    if search:
        matches = re.split(delimiter, text)
    tokenized_text.append(matches[0])
    tokenized_text.extend([matches[index] + matches[index+1] for index in range(1, len(matches[:-1]), 2)])
    tokenized_text = [token.strip() for token in tokenized_text]

    # Let's limit the length for test purposes
    if corpus_limit:
        tokenized_text = tokenized_text[:corpus_limit]
    # for index, match in enumerate(matches):
    #     search = re.search(delimiter, match)
    #     if search:
    #         print(search)
    #     else:
    #         print("NO")
    
    return tokenized_text
    
            
            
if __name__ == '__main__':
    syntactic_tokenization(sys.argv[1])