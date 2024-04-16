import json
import os
import re
import shutil
import subprocess
# from bertalign.Bertalign import Bertalign
import numpy as np

import lxml.etree as ET


# This scripts aims at aligning each lesson with its source (and between them?), sentence by sentence.

def save_file(string, path):
    with open(path, "w") as output_file:
        output_file.write(string)


def pop_attribute(tree, xpath_expression, attribute_name):
    for element in tree.xpath(f"{xpath_expression}[@{attribute_name}]", namespaces=namespaces):
        # Pop can't use prefix namespaces in attributes
        if "xml" in attribute_name:
            attribute_name = attribute_name.replace("xml:", "{http://www.w3.org/XML/1998/namespace}")
        element.attrib.pop(attribute_name, None)


def sentences_to_list(version):
    list_of_sentences = []
    positions_and_ids = {}
    all_sents = version.xpath("descendant::tei:s", namespaces=namespaces)
    for index, sentence in enumerate(all_sents):
        sentence_id = sentence.xpath("@xml:id")[0]
        positions_and_ids[index] = sentence_id
        text = " ".join(
            sentence.xpath("descendant::node()[self::tei:w or self::tei:pc or self::tei:ref or self::tei:code]/text()",
                           namespaces=namespaces))
        list_of_sentences.append(text)
    return list_of_sentences, positions_and_ids


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


def align_lessons(file):
    """
    This script takes a TEI file and identifies the sentences using basic punctuation
    :param file: The main file containing all translations
    :return: None
    """
    print(file)
    main_tree = ET.parse(file)
    main_tree.xinclude()
    pop_attribute(main_tree, "descendant::tei:s", "corresp")
    all_tei_nodes = main_tree.xpath("/tei:TEI/tei:TEI[descendant::tei:TEI[@xml:id = 'jupyter-notebooks']]",
                                    namespaces=namespaces)
    print(len(all_tei_nodes))
    for lesson in all_tei_nodes:
        print("New lesson")
        original_id = lesson.xpath("descendant::tei:TEI[@type='original']/@xml:id", namespaces=namespaces)[0]
        translations_id = lesson.xpath("descendant::tei:TEI[@type='translation']/@xml:id", namespaces=namespaces)
        original_file = lesson.xpath("descendant::tei:TEI[@type='original']", namespaces=namespaces)[0]
        translations = lesson.xpath("descendant::tei:TEI[@type='translation']", namespaces=namespaces)
        print(original_id)
        if len(original_file) == 0:
            continue
        original_file_as_list, original_ids_as_dict = sentences_to_list(original_file)

        all_translations_id = []
        all_translations = []
        for version in translations:
            all_translations.append(sentences_to_list(version)[0])
            all_translations_id.append(sentences_to_list(version)[1])

        for index, translation in enumerate(all_translations):
            current_translation_id = translations_id[index]
            # aligner = Bertalign(original_file_as_list, translation, max_align=3, win=5, skip=-.2)
            # aligner.align_sents()
            # results = aligner.result
            # save_file(json.dumps(results, cls=NpEncoder), f"/home/mgl/Documents/{current_translation_id}.json")
            with open(f"/home/mgl/Documents/{current_translation_id}.json", "r") as input_results:
                results = json.load(input_results)
            aligned_positions_and_ids = []

            for model_idx, translation_idx in results:
                try:
                    original_sentence_id = [original_ids_as_dict[model_idx[index]] for index in
                                            range(len(model_idx))]
                except KeyError:
                    print(original_ids_as_dict)
                    print(model_idx)
                    print("Error")
                    print(exit(0))
                    
                except IndexError:
                    original_sentence_id = None
                try:
                    corresponding_translation_sentence_id = [all_translations_id[index][translation_idx[index]] for
                                                             index in
                                                             range(len(translation_idx))]
                except IndexError:
                    corresponding_translation_sentence_id = None
                aligned_positions_and_ids.append(
                    (original_sentence_id, corresponding_translation_sentence_id))
            print(aligned_positions_and_ids)

            original_as_XML = original_file
            translation_as_xml = translations[index]
            # An xml base is being written before, we'll remove it.
            pop_attribute(original_file, "self::node()", "xml:base")
            pop_attribute(translation_as_xml, "self::node()", "xml:base")
            print(aligned_positions_and_ids[0])
            for original_sent_id, translated_sent_id in aligned_positions_and_ids[:1]:
                print(original_sent_id)
                print(translated_sent_id)
                # We start with the original file
                try:
                    corresponding_sentence_in_original = \
                        original_as_XML.xpath(f"descendant::tei:s[contains(@xml:id, '{''.join(original_sent_id)}')]",
                                              namespaces=namespaces)[0]
                except IndexError:
                    print("Not found")
                    pass
                try:
                    print(translated_sent_id)
                    current_corresp = json.loads(corresponding_sentence_in_original.xpath("@corresp")[0].replace("\'","\""))
                    current_corresp[translations_id[index]] = json.dumps(translated_sent_id)
                    corresponding_sentence_in_original.set("corresp", json.dumps(current_corresp).replace("\"", "\'"))
                except IndexError:
                    corresponding_sentence_in_original.set("corresp",
                                                           json.dumps({translations_id[index]: translated_sent_id}).replace("\"", "\'"))

                # Let's pass to the translation
                try:
                    corresponding_sentence_in_translation = \
                        translation_as_xml.xpath(
                            f"descendant::tei:s[contains(@xml:id,'{''.join(translated_sent_id)}')]",
                            namespaces=namespaces)[0]
                except IndexError:
                    pass
                try:
                    current_corresp = json.loads(corresponding_sentence_in_translation.xpath("@corresp")[0].replace("\'","\""))
                    current_corresp[original_id] = json.dumps(original_sent_id)
                    corresponding_sentence_in_translation.set("corresp", json.dumps(current_corresp).replace("\"", "\'"))
                except IndexError:
                    corresponding_sentence_in_translation.set("corresp",
                                                           json.dumps({original_id: original_sent_id}).replace("\"", "\'"))

            with open(f"../../data/tei_sentences_tokenized/{original_id}/{original_id}.xml",
                      "w") as output_original:
                output_original.write(ET.tostring(original_file, pretty_print=True, encoding='utf8').decode('utf8'))

            with open(f"../../data/tei_sentences_tokenized/{current_translation_id}/{current_translation_id}.xml", "w") \
                    as output_translation:
                output_translation.write(
                    ET.tostring(translation_as_xml, pretty_print=True, encoding='utf8').decode('utf8'))
    print("Done !")

if __name__ == '__main__':
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}

    align_lessons("../../data/tei_sentences_tokenized/main.xml")
