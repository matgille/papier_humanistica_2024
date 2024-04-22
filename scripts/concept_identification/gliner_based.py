import json

import tqdm
from gliner import GLiNER
import sys
import lxml.etree as ET

model = GLiNER.from_pretrained("urchade/gliner_large-v2.1")

ns_decl = {"tei": "http://www.tei-c.org/ns/1.0"}


def text_from_tokens(sentence):
    as_list = []
    for element in sentence.xpath("descendant::node()[not(self::tei:code)]/descendant::tei:w", namespaces=ns_decl):
        as_list.append(element.text.lower())
    return " ".join(as_list)


def extract_terms():
    labels = {"en": ["methodological term", "technical term", "computer", "programming", "code", "informatics"], 
              "es": ["término metodológico","terminología técnica", "computadora", "ordenador", "código", "programación", "informática"],
              "fr": ["terme méthodologique","terme technique", "ordinateur", "programmation", "code", "informatique"],
              "pt": ["termo metodológico","termo técnico", "computador", "código", "programação", "informática"]}
    merged_labels = [keyword for key, value in labels.items() for keyword in value]
    print(labels)
    all_entities = {}
    main_file = ET.parse("../../data/tei_sentences_tokenized/main.xml")
    main_file.xinclude()
    all_lessons = "/tei:TEI/tei:TEI/tei:TEI"
    single_lesson = "/tei:TEI/tei:TEI[descendant::tei:TEI[@xml:id='working-with-web-pages']]/tei:TEI"
    for lesson in tqdm.tqdm(main_file.xpath(all_lessons, namespaces=ns_decl)): 
        for paragraph in lesson.xpath("descendant::tei:s", namespaces=ns_decl):
            lang = lesson.xpath("descendant::tei:text/@xml:lang", namespaces=ns_decl)[0]
            all_words = text_from_tokens(paragraph)
            try:
                identified_ents = model.predict_entities(all_words, labels['en'], threshold=0.3)
            except  IndexError:
                continue
            for entity in identified_ents:
                if len(entity['text']) != 1:
                    try:
                        current_lang_entities = all_entities[lang]
                        current_lang_entities.append(entity['text'])
                        all_entities[lang] = list(set(current_lang_entities))
                    except KeyError:
                        all_entities[lang] = [entity['text']]
        
    with open("../../data/concepts.json", "w", encoding='utf8') as output_json:
        json.dump(all_entities, output_json)


if __name__ == '__main__':
    extract_terms()
