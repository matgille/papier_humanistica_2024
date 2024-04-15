import os
import re
import shutil
import subprocess

import lxml.etree as ET


# This scripts aims at aligning each lesson with its source (and between them?), sentence by sentence.


def main():
    pass


def word_tokenization(lesson):
    xslt = "tokenization.xsl"
    saxon = "saxon9he.jar"
    with open(".tmp/lesson.xml", "w") as xml_file:
        xml_file.write(ET.tostring(lesson, pretty_print=True).decode())
    subprocess.run(["java", "-jar", saxon, ".tmp/lesson.xml", xslt])


def tokenize_sentences(version_id, lesson_name):
    try:
        os.mkdir(f"../../data/tei_sentences_tokenized")
    except FileExistsError:
        pass
    try:
        os.mkdir(f"../../data/tei_sentences_tokenized/{version_id}")
    except FileExistsError:
        pass
    with open(".tmp/tokenized.xml", "r") as input_file:
        as_tree = ET.parse(input_file)
    for possible_nodes in as_tree.xpath(
            "//tei:body/descendant::node()[child::tei:pc or child::tei:w][not(self::tei:ref | self::tei:emph)]",
            namespaces=namespaces):
        if len(possible_nodes.xpath("descendant::tei:pc", namespaces=namespaces)) == 0:
            sentence = ET.Element("s")
            possible_nodes.append(sentence)
            for node in possible_nodes.xpath("node()[not(self::s)]"):
                sentence.append(node)
        elif len(possible_nodes.xpath("descendant::tei:pc", namespaces=namespaces)) == 1 and possible_nodes.xpath(
                "child::node()[last()][self::tei:pc]", namespaces=namespaces):
            sentence = ET.Element("s")
            possible_nodes.insert(0, sentence)
            for node in possible_nodes.xpath("node()[not(self::s)]"):
                sentence.append(node)
        else:
            sentence = ET.Element("s")
            possible_nodes.insert(0, sentence)
            for node in possible_nodes.xpath(
                    "node()[self::tei:pc or self::tei:w or self::tei:emph or self::tei:ref][not(preceding-sibling::tei:pc)][not(ancestor::tei:s)]",
                    namespaces=namespaces):
                sentence.append(node)
            while len(possible_nodes.xpath("child::tei:w", namespaces=namespaces)) != 0:
                first_w_without_sentence = possible_nodes.xpath("child::node()[self::tei:w or self::tei:emph or self::tei:ref]["
                                                                "preceding-sibling::s]", namespaces=namespaces)[0]
                sentence = ET.Element("s")
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
    main_tree.xinclude()
    print(main_tree)
    all_tei_nodes = main_tree.xpath("/tei:TEI/tei:TEI", namespaces=namespaces)
    shutil.copy("../../data/tei_aligned/main.xml", "../../data/tei_sentences_tokenized/main.xml")
    for lesson in all_tei_nodes:
        print("New lesson")
        all_versions = lesson.xpath("descendant::tei:TEI", namespaces=namespaces)
        print(len(all_versions))
        for version in all_versions:
            version_id = version.xpath("@xml:id")[0]
            word_tokenization(version)
            tokenize_sentences(version_id, f"{version_id}.xml")


if __name__ == '__main__':
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    retrieve_lessons("../../data/tei_aligned/main.xml")
