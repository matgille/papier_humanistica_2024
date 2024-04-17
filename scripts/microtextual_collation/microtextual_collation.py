import json

import torch
import transformers
import itertools
import lxml.etree as ET
model = transformers.BertModel.from_pretrained('Geotrend/bert-base-10lang-cased')
tokenizer = transformers.BertTokenizer.from_pretrained('Geotrend/bert-base-10lang-cased')


def run_align(src, tgt):
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
    align_layer = 8
    threshold = .00001
    model.eval()
    with torch.no_grad():
        out_src = model(ids_src.unsqueeze(0), output_hidden_states=True)[2][align_layer][0, 1:-1]
        out_tgt = model(ids_tgt.unsqueeze(0), output_hidden_states=True)[2][align_layer][0, 1:-1]

        dot_prod = torch.matmul(out_src, out_tgt.transpose(-1, -2))

        softmax_srctgt = torch.nn.Softmax(dim=-1)(dot_prod)
        softmax_tgtsrc = torch.nn.Softmax(dim=-2)(dot_prod)

        softmax_inter = (softmax_srctgt > threshold) * (softmax_tgtsrc > threshold)

    align_subwords = torch.nonzero(softmax_inter, as_tuple=False)
    align_words = set()
    for i, j in align_subwords:
        align_words.add((sub2word_map_src[i], sub2word_map_tgt[j]))

    # printing
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

    for i, j in sorted(align_words):
        print(f'{color.BOLD}{color.BLUE}{sent_src[i]}{color.END}==={color.BOLD}{color.RED}{sent_tgt[j]}{color.END}')

def main():

    main_file = "../../data/tei_sentences_tokenized/main.xml"
    as_tree = ET.parse(main_file)
    as_tree.xinclude()
    for sent in as_tree.xpath(f"descendant::tei:TEI[@type='original']/descendant::tei:s", namespaces=namespaces)[:10]:
        all_texts = []
        corresp_sent_id = sent.xpath("@corresp")[0]
        corresp_dict = json.loads(corresp_sent_id.replace("'", "\""))
        print(corresp_dict)
        print(list(corresp_dict.values())[0][0])
        corresponding_sentence = as_tree.xpath(f"descendant::tei:s[@xml:id='{list(corresp_dict.values())[0][0]}']", namespaces=namespaces)[0]
        all_texts.append(text_from_tokens(sent))
        as_text = text_from_tokens(corresponding_sentence)
        all_texts.append(as_text)
        print(all_texts)
    
        for text in all_texts[1:]:
            source = all_texts[0]
            target = text
            print("\n\n")
            run_align(source, target)

def text_from_tokens(sentence):
    as_list = []
    for element in sentence.xpath("descendant::node()[self::tei:w or self::tei:pc]", namespaces=namespaces):
        as_list.append(element.text)
    return " ".join(as_list)

if __name__ == '__main__':
    namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
    main()