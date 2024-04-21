import json
import os
import re
import sys

import torch
import tqdm
import transformers
import itertools
import lxml.etree as ET
from nltk import ngrams
from collections import defaultdict

model = transformers.BertModel.from_pretrained('google-bert/bert-base-multilingual-cased')
tokenizer = transformers.BertTokenizer.from_pretrained('google-bert/bert-base-multilingual-cased')


def run_align(src, tgt, align_layer, threshold):
    # pre-processing
    sent_src, sent_tgt = src.strip().split(), tgt.strip().split()
    token_src, token_tgt = [tokenizer.tokenize(word) for word in sent_src], [tokenizer.tokenize(word) for word in
                                                                             sent_tgt]
    wid_src, wid_tgt = [tokenizer.convert_tokens_to_ids(x) for x in token_src], [tokenizer.convert_tokens_to_ids(x) for
                                                                                 x in token_tgt]
    ids_src, ids_tgt = tokenizer.prepare_for_model(list(itertools.chain(*wid_src)), return_tensors='pt',
                                                   model_max_length=tokenizer.model_max_length, truncation=True)[
                           'input_ids'], \
                       tokenizer.prepare_for_model(list(itertools.chain(*wid_tgt)), return_tensors='pt',
                                                   truncation=True, model_max_length=tokenizer.model_max_length)[
                           'input_ids']

    sub2word_map_src = []
    for i, word_list in enumerate(token_src):
        sub2word_map_src += [i for x in word_list]
    sub2word_map_tgt = []
    for i, word_list in enumerate(token_tgt):
        sub2word_map_tgt += [i for x in word_list]

    # alignment
    model.to(device)
    model.eval()
    if device != "cpu":
        ids_src = ids_src.cuda()
        ids_tgt = ids_tgt.cuda()
    with torch.no_grad():
        out_src = model(ids_src.unsqueeze(0), output_hidden_states=True)[2][align_layer][0, 1:-1]
        out_tgt = model(ids_tgt.unsqueeze(0), output_hidden_states=True)[2][align_layer][0, 1:-1]

        dot_prod = torch.matmul(out_src, out_tgt.transpose(-1, -2))

        softmax_srctgt = torch.nn.Softmax(dim=-1)(dot_prod)
        softmax_tgtsrc = torch.nn.Softmax(dim=-2)(dot_prod)

        softmax_inter = (softmax_srctgt > threshold) * (softmax_tgtsrc > threshold)

    align_subwords = torch.nonzero(softmax_inter, as_tuple=False)
    align_subwords.to(device)
    align_words = set()
    for i, j in align_subwords:
        align_words.add((sub2word_map_src[i], sub2word_map_tgt[j]))

    # write_to_loging
    class color:
        PURPLE = '\033[95m'
        CYAN = '\033[96m'
        DARKCYAN = '\033[36m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        END = '\033[0m'

    alignment_list = []
    for i, j in sorted(align_words):
        alignment_list.append((i, sent_src[i], j, sent_tgt[j]))
        write_to_log(
            f'[{i}] {sent_src[i]}==={sent_tgt[j]} [{j}]')
    return alignment_list



def write_log_file(log_list):
    if progressive_logging is True:
        return
    else:
        with open(".logs/log.txt", "a") as log_file:
            log_file.write("\n".join(log_list))

def write_to_log(string):
    global log_list
    if progressive_logging is True:
        with open(".logs/log.txt", "a") as log_file:
            if type(string) != str:
                if type(string) in [list, dict]:
                    json.dump(string, log_file)
                else:
                    log_file.write(str(string))
            else:
                log_file.write(string)
            log_file.write("\n")
    else:
        if type(string) != str:
            if type(string) in [list, dict]:
                log_list.append((json.dumps(string)))
            else:
                log_list.append(str(string))
        else:
            log_list.append(string)


def main():
    try:
        os.mkdir(".logs/")
    except FileExistsError:
        pass
    with open(".logs/log.txt", "w") as log_file:
        log_file.truncate(0)
    concepts_file = "../../data/concepts.json"
    with open(concepts_file, "r") as concepts:
        concepts = json.load(concepts)
    main_file = "../../data/tei_sentences_aligned/main.xml"
    as_tree = ET.parse(main_file)
    as_tree.xinclude()
    concepts_dictionary = dict()
    test_query = "descendant::tei:TEI[descendant::tei:TEI[@xml:id='extrair-paginas-ilustradas-com-python']]/tei:TEI[" \
                 "@type='original'] "
    full_query = "descendant::tei:TEI/tei:TEI[@type='original']"
    for lesson in tqdm.tqdm(
            as_tree.xpath(test_query, namespaces=namespaces)):
        lesson_lang = lesson.xpath("descendant::tei:text/@xml:lang", namespaces=namespaces)[0]
        write_to_log(f"Lesson lang: {lesson_lang}")
        write_to_log(f"Corresponding concepts: {concepts[lesson_lang]}")
        for sent in lesson.xpath(f"descendant::tei:s", namespaces=namespaces):
            write_to_log("\nNew sentence\n---")
            all_texts = []
            original_sent = clean_text_from_tokens(sent)
            all_texts.append(original_sent)
            write_to_log(original_sent)
            try:
                corresp_sent_id = sent.xpath("@corresp")[0]
            except:
                continue
            replaced = corresp_sent_id.replace("'", "\"").replace("\'", "\"")
            write_to_log(replaced)
            corresp_dict = json.loads(rf"{replaced}")
            write_to_log(f"Corresp dict: {corresp_dict}")
            for witness, identifiers in corresp_dict.items():
                corresponding_text = ""
                for sentence in identifiers:
                    corresponding_sentence = \
                        as_tree.xpath(f"descendant::tei:s[@xml:id='{sentence}']", namespaces=namespaces)[0]
                    corresponding_lang = \
                        corresponding_sentence.xpath("ancestor::tei:text[1]/@xml:lang", namespaces=namespaces)[0]
                    write_to_log(f"Corresponding lang: {corresponding_lang}")
                    corresponding_sent_as_text = clean_text_from_tokens(corresponding_sentence)
                    corresponding_text += f" {corresponding_sent_as_text}".strip()
                    write_to_log(corresponding_sent_as_text)
                all_texts.append((corresponding_lang, corresponding_text))
            for lang, text in all_texts[1:]:
                source = all_texts[0]
                target = text
                write_to_log("\n\n")
                write_to_log(f"Source text: '{source}'")
                write_to_log(f"Target text: '{target}'")
                align_layer = 6
                threshold = .000001
                alignment_results = run_align(source, target, align_layer, threshold)
                write_to_log(alignment_results)
                concepts_dictionary = merge_dicts(concepts_dictionary,
                                                  retrieve_translated_concepts(alignment_results, concepts, lesson_lang,
                                                                               lang,
                                                                               original_sent, target,
                                                                               concepts_dictionary))

    write_to_log(concepts_dictionary)
    for key, value in concepts_dictionary.items():
        concepts_dictionary[key] = list(set(value))
    write_to_log(concepts_dictionary)

    with open("../../data/aligned_concepts.json", "w") as output_file:
        json.dump(concepts_dictionary, output_file)


def retrieve_translated_concepts(alignment_results, concepts, src_lang, tgt_lang, original_sent, translated_sent,
                                 concept_dict):
    translated_sent = re.sub(r"\s+", " ", translated_sent)
    found = False
    keywords_in_sentence = []
    for concept in concepts[src_lang]:
        concept_length = len(concept.split(" "))
        n_grams = [" ".join(ngram) for ngram in ngrams(original_sent.split(), concept_length)]
        if len(original_sent.split(" ")) < concept_length:
            continue
        elif concept_length == 1:
            if any([concept == word for word in original_sent.split(" ")]):
                keywords_in_sentence.extend([(concept, index) for index, word in enumerate(original_sent.split(" ")) if concept == word])
                found = True
        else:
            if any([ngram == concept for ngram in n_grams]):
                keywords_in_sentence.extend([(ngram, index) for index, ngram in enumerate(n_grams) if ngram == concept])
                found = True
    keywords_in_sentence = list(set(keywords_in_sentence))
    if found:
        found_keywords = keywords_in_sentence
        write_to_log("Concept found in original lang.")
        write_to_log(found_keywords)
        write_to_log(original_sent)
        write_to_log(translated_sent)

        # TODO: this is done without context if a keyword is repeated, there may be a problem.
        for keyword, start_index in found_keywords:
            write_to_log(f"\nNew keyword: {keyword}")

            # If the keyword is a composed word
            if " " in keyword:
                write_to_log("Composed keyword")
                
                # Check with alignment table better, and index of matching element.
                first_alignment_unit = start_index
                last_alignment_unit = start_index + len(keyword.split(" "))
                write_to_log(first_alignment_unit)
                write_to_log(last_alignment_unit)
                corresponding_span_of_text = ""
                all_targets = []
                for unit in range(first_alignment_unit, last_alignment_unit):
                    target = [item for item in alignment_results if item[0] == unit]
                    write_to_log(f"Target: {target}")
                    # If the target is empty, the word is not identified by awesome-align OR 
                    # it has been omitted in the translation
                    if len(target) == 0:
                        continue
                    target_indices = [target_index for source_index, source_word, target_index, target_word in target]
                    target_indices.extend([target_indices[-1] + 1])
                    write_to_log(target_indices)
                    ranges = range(target_indices[0], target_indices[-1])
                    write_to_log(f"Target indices: {target_indices}")
                    write_to_log(ranges)
                    write_to_log(translated_sent)
                    all_targets.append((target[0][-2], ' '.join([translated_sent.split(' ')[idx] for idx in ranges])))
                all_targets.sort(key=lambda x: x[0])
                write_to_log(f"After sorting: {all_targets}")

                # On va trouver le texte qui est inclus entre le premier et le dernier mot de la phrase cible
                try:
                    corresponding_span_of_text = " ".join(translated_sent.split(' ')[idx] for idx in
                                                          range(all_targets[0][0], all_targets[-1][0] + 1)).strip()
                except IndexError:
                    write_to_log("Something may have been wrong here, passing.")
                    continue
                write_to_log(f"Corresponding span for keyword '{keyword}': '{corresponding_span_of_text}'")
                # We check if the identified target is not too different in length -- meaning a probable error
                if len(corresponding_span_of_text.split(" ")) - len(keyword.split(" ")) > 4:
                    write_to_log("Possible error, target keyword is too long")
                    continue
                try:
                    concept_dict[keyword].append((tgt_lang, corresponding_span_of_text))
                except KeyError:
                    concept_dict[keyword] = [(tgt_lang, corresponding_span_of_text)]
                write_to_log(concept_dict)
            else:
                corresponding_alignment_unit = [index for index, element in enumerate(original_sent.split()) if
                                                keyword == element]
                write_to_log(corresponding_alignment_unit)
                for unit in corresponding_alignment_unit:

                    # When there is a one to many alignment, the word is repeated in the source: 
                    # 1 keywords palabras 3
                    # 2 keywords clave 4
                    target = [item for item in alignment_results if item[0] == unit]

                    # If the target is empty, the word is not identified by awesome-align OR 
                    # it has been omitted in the translation
                    if len(target) == 0:
                        continue
                    # We search the first and last
                    target_indices = [target_index for source_index, source_word, target_index, target_word in target]
                    write_to_log(f"Target indices: {target_indices}")
                    target_indices.extend([target_indices[-1] + 1])
                    ranges = range(target_indices[0], target_indices[-1])
                    write_to_log(ranges)
                    corresponding_span_of_text = " ".join([translated_sent.split(" ")[idx] for idx in ranges])
                    write_to_log(f"Corresponding span for keyword '{keyword}': '{corresponding_span_of_text}'")

                    # We check if the identified target is not too different in length -- meaning a probable error
                    if len(corresponding_span_of_text.split(" ")) - len(keyword.split(" ")) > 4:
                        write_to_log("Possible error, target keyword is too long")
                        continue
                    try:
                        concept_dict[keyword].append((tgt_lang, corresponding_span_of_text))
                    except KeyError:
                        concept_dict[keyword] = [(tgt_lang, corresponding_span_of_text)]

    else:
        write_to_log("Nothing found")
    return concept_dict


def merge_dicts(dict_a, dict_b):
    """
    This function merges two dicts and their values when the keys are the same.
    :param dict_a: 
    :param dict_b: 
    :return: 
    """
    # https://stackoverflow.com/a/5946322
    merged_dict = defaultdict(list)
    for d in (dict_a, dict_b):  # you can list as many input dicts as you want here
        for concept, translations in d.items():
            try:
                merged_dict[concept].extend(translations)
                updated = list(set(merged_dict[concept]))
                merged_dict[concept] = updated
            except KeyError:
                merged_dict[concept] = list(set(translations))
    return dict(merged_dict)


def clean_text_from_tokens(sentence):
    as_list = []
    multiple_spaces_pattern = re.compile(r"\s+")
    for element in sentence.xpath("descendant::node()[self::tei:w or self::tei:pc]", namespaces=namespaces):
        as_list.append(element.text.lower())
    cleaned = re.sub(multiple_spaces_pattern, " ", " ".join(as_list))
    cleaned = cleaned.strip().replace(' " ', "").replace(" ' ", "").replace("`", "")
    cleaned = cleaned.replace(" - ", " ").replace(">", "").replace("<", "")
    return cleaned


if __name__ == '__main__':
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    progressive_logging = False
    global log_list
    log_list = []
    device = sys.argv[1]
    main()
    write_log_file(log_list)
