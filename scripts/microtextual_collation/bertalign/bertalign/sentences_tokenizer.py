import json
import re

# On cherche un alignement au niveau du syntagme et non pas de la phrase; l'identification des propositions est donc une bonne façon 
# de procéder à une tokénisation de la phrase. Il faut donc réécrire 
# la fonction de tokénisation pour intégrer les subordonnants, etc ainsi que plus d'éléments de ponctuation, 
# que ce soit en latin ou en castillan.

# Le but est donc de trouver la façon la plus propre d'identifier formellement les propositions, on va donc cibler les
# subordonnants, etc.

# Le présupposé est que les unités syntaxiques et sémantiques ne se chevauchent pas, c'est-à-dire que le découpage 
# en unités syntaxiques (propositions) ne va pas entrer en contradiction avec la sémantique du texte, sur laquelle
# se fonde l'aligneur. L'alignement sera donc plus précis et plus efficace si l'on identifie 
# au préalable la structure syntaxique des documents (faire des tests là dessus, c'est probablement ce qu'on peut
# apporter).

class SubSentencesTokenizer():
    def __init__(self, input_text):
        self.punctation_delimiters = r""
        self.tokens_delimiters = r""
        self.input_text = input_text
        self.create_delimiters_regex()
        self.clean_input_text()
    
    
    def create_delimiters_regex(self):
        with open("bertalign/delimiters.json", "r") as input_json:
            dictionary = json.load(input_json)
        single_tokens_punctuation = [punct for punct in dictionary['punctuation'] if len(punct) == 1]
        multiple_tokens_punctuation = [punct for punct in dictionary['punctuation'] if len(punct) != 1]
        single_token_punct = "".join(single_tokens_punctuation)
        multiple_tokens_punct = "|".join(multiple_tokens_punctuation)
        punctuation_subregex = f"{multiple_tokens_punct}|[{single_token_punct}]"
        tokens_subregex = " | ".join(dictionary['word_delimiters'])
        self.punctation_delimiters = rf"({punctuation_subregex})"
        self.tokens_delimiters = rf"({tokens_subregex})"
        print(self.punctation_delimiters)
        print(self.tokens_delimiters)

    def tokenize(self):
        tokens_separation = re.sub(self.tokens_delimiters, r"||\1", self.input_text)
        tokens_and_punctuation_separation = re.sub(self.punctation_delimiters, r"\1||", tokens_separation)
        splits = re.split("\|\|", tokens_and_punctuation_separation)
        splits = [split for split in splits if len(split) > 1]
        return splits
            
    def clean_input_text(self):
        self.input_text = re.sub(r"\s+", " ", self.input_text)
    

if __name__ == '__main__':
    spanish = "text+berg/latin_castilian/Val_S_3_3_5.txt"
    latin = "text+berg/latin_castilian/Rome_W_3_3_5.txt"

    with open(spanish, "r") as input_spanish:
        spanish_text = input_spanish.read()
        
    with open(latin, "r") as input_latin:
        latin_text = input_latin.read()
    
    Tokenizer = SubSentencesTokenizer(spanish_text)
    splits = Tokenizer.tokenize()
    print(splits)
    Tokenizer = SubSentencesTokenizer(latin_text)
    splits = Tokenizer.tokenize()
    print(splits)
    
    