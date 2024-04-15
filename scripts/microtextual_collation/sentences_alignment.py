import os
import re
import shutil
import subprocess
from bertalign.Bertalign import Bertalign


import lxml.etree as ET


# This scripts aims at aligning each lesson with its source (and between them?), sentence by sentence.


def main():
    pass

def sentences_to_list(version):
    list_of_sentences = []
    all_sents = version.xpath("descendant::tei:s", namespaces=namespaces)
    for sentence in all_sents:
        text = " ".join(sentence.xpath("descendant::node()[self::tei:w or self::tei:pc or self::tei:ref or self::tei:code]/text()", namespaces=namespaces))
        list_of_sentences.append(text)
    return list_of_sentences

def retrieve_lessons(file):
    """
    This script takes a TEI file and identifies the sentences using basic punctuation
    :param file: The main file containing all translations
    :return: None
    """
    print(file)
    main_tree = ET.parse(file)
    main_tree.xinclude()
    print(main_tree)
    all_tei_nodes = main_tree.xpath("/tei:TEI/tei:TEI[count(descendant::tei:TEI) > 1]", namespaces=namespaces)
    for lesson in all_tei_nodes:
        print("New lesson")
        all_versions = lesson.xpath("descendant::tei:TEI", namespaces=namespaces)
        print(len(all_versions))
        all_texts = []
        for version in all_versions:
            all_texts.append(sentences_to_list(version))
        
        print(len(all_texts[0]))
        print(len(all_texts[1]))
        aligner = Bertalign(all_texts[0], all_texts[1], max_align=3, win=5, skip=-.2)
        aligner.align_sents()
        aligner.print_sents()
        exit(0)


if __name__ == '__main__':
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    retrieve_lessons("../../data/tei_sentences_tokenized/main.xml")
