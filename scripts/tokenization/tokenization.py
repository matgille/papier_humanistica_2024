import copy
import os
import re
import shutil
import subprocess
import uuid
import lxml.etree as ET
import string
import random
import nltk
import tqdm
from nltk.tokenize import sent_tokenize, word_tokenize

# This scripts aims at aligning each lesson with its source (and between them?), sentence by sentence.



def word_tokenization(lesson):
    """
    This function tokenizes a text using NLTK, and then performs the classification between
    punctuation and words (that is, it identifies the dot, interrogative and exclamative signs as
    a punctuation mark, and the other signs as tei:w, for simplicity reasons.
    :param lesson: the lesson as an XML element.
    :return: None
    """
    lesson_id = lesson.xpath("@xml:id", namespaces=namespaces)[0]
    langs_dict = {"en": "english", "fr": "french", "es": "spanish", "pt": "portuguese"}
    lang = lesson.xpath("descendant::tei:text/@xml:lang", namespaces=namespaces)[0]
    nltk_language = langs_dict[lang]
    all_nodes = lesson.xpath("descendant::tei:text/descendant::node()[not(self::text() or self::comment())]", namespaces=namespaces)
    for index, node in enumerate(all_nodes):
        if node.text is not None:
            tokenized = word_tokenize(node.text, language=nltk_language)
            node.text = ""
            for token in reversed(tokenized):
                if token in '.?!':
                    pc = ET.Element("pc")
                    pc.text = token
                    if index == 0:
                        node.insert(0, pc)
                    else:
                        node.insert(0, pc)
                else:
                    w = ET.Element("w")
                    w.text = token
                    if index == 0:
                        node.insert(0, w)
                    else:
                        try:
                            node.insert(0, w)
                        except TypeError:
                            print(lesson_id)
                            print("Error, exiting.")
                            exit(0)

        if index != 0 and node.tail is not None:
            tokenized = word_tokenize(node.tail, language="french")
            node.tail = ""
            for token in reversed(tokenized):
                if token in '.?!':
                    pc = ET.Element("pc")
                    pc.text = token
                    node.addnext(pc)
                else:
                    w = ET.Element("w")
                    w.text = token
                    node.addnext(w)
    # This is a trick to make all elements of tree inherit tei namespace of root.
    return ET.fromstring(ET.tostring(lesson))


def generateur_id(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits) -> str:
    first_char = "s_"
    random_string = ''.join(random.choice(chars) for _ in range(size))
    return first_char + random_string


def tokenize_sentences(version_id, word_tokenized):
    """
    This function creates sentences after tokenizing an XML-TEI file.
    :param version_id: 
    :param lesson_name: 
    :return: 
    """
    try:
        os.mkdir(f"../../data/tei_sentences_tokenized")
    except FileExistsError:
        pass
    try:
        os.mkdir(f"../../data/tei_sentences_tokenized/{version_id}")
    except FileExistsError:
        pass
    as_tree = word_tokenized
    for possible_nodes in as_tree.xpath(
            "//tei:body/descendant::node()[child::tei:pc or child::tei:w][not(self::tei:ref | self::tei:emph | "
            "self::tei:code)]", 
            namespaces=namespaces):
        if len(possible_nodes.xpath("descendant::tei:pc", namespaces=namespaces)) == 0:
            sentence = ET.Element("s")
            sentence.set("{http://www.w3.org/XML/1998/namespace}id", generateur_id(6))
            possible_nodes.append(sentence)
            for node in possible_nodes.xpath("node()[not(self::s)]"):
                sentence.append(node)
        elif len(possible_nodes.xpath("descendant::tei:pc", namespaces=namespaces)) == 1 and possible_nodes.xpath(
                "child::node()[last()][self::tei:pc]", namespaces=namespaces):
            sentence = ET.Element("s")
            sentence.set("{http://www.w3.org/XML/1998/namespace}id", generateur_id(6))
            possible_nodes.insert(0, sentence)
            for node in possible_nodes.xpath("node()[not(self::s)]"):
                sentence.append(node)
        else:
            sentence = ET.Element("s")
            sentence.set("{http://www.w3.org/XML/1998/namespace}id", generateur_id(6))
            possible_nodes.insert(0, sentence)
            for node in possible_nodes.xpath(
                    "node()[self::tei:pc or self::tei:w or self::tei:emph or self::tei:ref or self::tei:code][not(preceding-sibling::tei:pc)][not(ancestor::tei:s)]",
                    namespaces=namespaces):
                sentence.append(node)
            while len(possible_nodes.xpath("child::tei:w", namespaces=namespaces)) != 0:
                first_w_without_sentence = \
                possible_nodes.xpath("child::node()[self::tei:w or self::tei:emph or self::tei:ref or self::tei:code]["
                                     "preceding-sibling::s]", namespaces=namespaces)[0]
                sentence = ET.Element("s")
                sentence.set("{http://www.w3.org/XML/1998/namespace}id", generateur_id(6))
                first_w_without_sentence.addprevious(sentence)
                for node in first_w_without_sentence.xpath(
                        "following-sibling::node()[self::tei:pc or self::tei:w or self::tei:code or self::tei:ref or self::tei:emph]["
                        "not(preceding-sibling::tei:pc)][not(ancestor::tei:s)]",
                        namespaces=namespaces):
                    sentence.append(node)
                sentence.insert(0, first_w_without_sentence)

    with open(f"../../data/tei_sentences_tokenized/{version_id}/{version_id}.xml", "w") as output_file:
        output_file.write(ET.tostring(as_tree, pretty_print=True, encoding="utf8").decode("utf8"))



def retrieve_lessons(file):
    """
    This script takes a TEI file and identifies the sentences using basic punctuation
    :param file: The main file containing all translations
    :return: None
    """
    print(file)
    main_tree = ET.parse(file)
    new_main_tree = copy.deepcopy(main_tree)
    main_tree.xinclude()
    print(main_tree)
    
    all_tei_lessons = main_tree.xpath("/tei:TEI/tei:TEI",
                                          namespaces=namespaces)
    lessons_to_erase = {}
    for index, lesson in enumerate(all_tei_lessons):
        if len(lesson.xpath("tei:TEI", namespaces=namespaces)) == 1:
            erase = True
        else:
            erase = False
        lessons_to_erase[index] = erase
    
    # Let's erase the good lessons.
    for index, TEI_lesson in enumerate(new_main_tree.xpath("/tei:TEI/tei:TEI", namespaces=namespaces)):
        if lessons_to_erase[index] is True:
            print("Erasing")
            TEI_lesson.getparent().remove(TEI_lesson)
        else:
            pass
        
    with open("../../data/tei_sentences_tokenized/main.xml", "w") as output_TEI:
        output_TEI.write(ET.tostring(new_main_tree, pretty_print=True, encoding='utf8').decode('utf8'))
        
    all_tei_nodes = main_tree.xpath("/tei:TEI/tei:TEI[count(descendant::tei:TEI) > 1]", namespaces=namespaces)
    for lesson in tqdm.tqdm(all_tei_nodes):
        all_versions = lesson.xpath("descendant::tei:TEI", namespaces=namespaces)
        for version in all_versions:
            version_id = version.xpath("@xml:id")[0]
            word_tokenized = word_tokenization(version)
            tokenize_sentences(version_id, word_tokenized)

    
    


if __name__ == '__main__':
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    retrieve_lessons("../../data/tei_with_numbered_divs/main.xml")
