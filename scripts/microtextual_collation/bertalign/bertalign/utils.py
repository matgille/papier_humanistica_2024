import re
import string
import random
import lxml.etree as etree
import json
import itertools
from numpyencoder import NumpyEncoder

def save_alignment_results(results, first_text: list, second_text: list, name:str, out_dir) -> None:
    with open(f"result_dir/{out_dir}/alignment_{name}.csv", "w") as output_alignment:
        for alignment_unit in results:
            first_alignment_id = "|".join([str(alignment) for alignment in alignment_unit[0]])
            first_span = "|".join([str(first_text[id]) for id in alignment_unit[0]])
            second_alignment_id = "|".join([str(alignment) for alignment in alignment_unit[1]])
            second_span = "|".join([str(second_text[id]) for id in alignment_unit[1]])
            output_alignment.write(str(first_alignment_id))
            output_alignment.write("\t")
            output_alignment.write(first_span)
            output_alignment.write("\t")
            output_alignment.write(second_span)
            output_alignment.write("\t")
            output_alignment.write(str(second_alignment_id))
            output_alignment.write("\n")

    with open(f"result_dir/{out_dir}/{name}_as_index.tsv", "w") as output_text:
        output_text.write("A\tB\n")
        for alignment_unit in results:
            output_text.write("|".join([str(id) for id in alignment_unit[0]]))
            output_text.write("\t")
            output_text.write("|".join([str(id) for id in alignment_unit[1]]))
            output_text.write("\n")


def normalize_text(text):
    text = text.replace("’", " ")
    text = text.replace("-", " ")
    text = text.replace("/", " / ")
    text = text.replace(" /", " / ")
    return text

def clean_tokenized_content(tokenized_doc: list):
    print(len(tokenized_doc))
    digit_pattern = re.compile(r"\d+")
    pattern_full = re.compile(r"[—;,:\.]\s+[«»]|![«»]|»")
    pattern_start = re.compile(r"^[-;,:\.\!\?]\s*[-;,:\.\!\?]?\s*")
    alt_pattern_start = re.compile(r"»\s+\d+")
    punct_pattern = re.compile("^[\.,;!:?·]$")
    spaces_pattern = re.compile("\s+")
    cleaned_doc = []
    for line in tokenized_doc:
        cleaned = re.sub(digit_pattern, "", line)
        cleaned = re.sub(pattern_full, "", cleaned)
        cleaned = re.sub(pattern_start, "", cleaned)
        cleaned = re.sub(alt_pattern_start, "\1", cleaned)
        cleaned = cleaned.replace(".", " ")
        cleaned = cleaned.replace(",", " ")
        cleaned = cleaned.replace("/", " ")
        cleaned = cleaned.replace("-", " ")
        cleaned = cleaned.replace("\u0001", " ")
        cleaned = re.sub(spaces_pattern, " ", cleaned)
        cleaned = cleaned.strip()
        if re.match(punct_pattern, cleaned):
            print(f"Removing: {cleaned}")
            cleaned = re.sub(punct_pattern, "", cleaned)
        if cleaned != "":
            cleaned_doc.append(cleaned)
    print(cleaned_doc)
    print(len(cleaned_doc))
    return cleaned_doc

def pretty_print_xml_tree(file):
    try:
        parsed = etree.parse(file)
    except OSError:
        print(f"File {file} not found, exiting")
        exit(0)
    with open(file, "w") as output_file:
        output_file.write(etree.tostring(parsed, pretty_print=True).decode())

def save_tree_to_file(tree, filepath):
    print(f"Saving tree to {filepath}.")
    with open(filepath, "w") as out_file:
        out_file.write(etree.tostring(tree, pretty_print=True).decode())
        
def write_json(path, object:json):
    with open(path, "w") as output_file:
        json.dump(object, output_file, cls=NumpyEncoder)

def read_json(path):
    print("Chargement 3")
    with open(path, "r") as output_file:
        liste = json.load(output_file)
    return liste

def write_tokenized_text(path, tokenized_text:list):
    with open(path, "w") as output_file:
        output_file.write("\n".join(tokenized_text))




def construct_pairs(my_list):
    combinations = list(itertools.combinations(my_list, 2))
    return combinations


def clean_text(text):
    clean_text = []
    text = text.strip()
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if line:
            line = re.sub('\s+', ' ', line)
            clean_text.append(line)
    return "\n".join(clean_text)
  
def yield_overlaps(lines, num_overlaps):
    lines = [_preprocess_line(line) for line in lines]
    for overlap in range(1, num_overlaps + 1):
        for out_line in _layer(lines, overlap):
            # check must be here so all outputs are unique
            out_line2 = out_line[:10000]  # limit line so dont encode arbitrarily long sentences
            yield out_line2

def _layer(lines, num_overlaps, comb=' '):
    if num_overlaps < 1:
        raise Exception('num_overlaps must be >= 1')
    out = ['PAD', ] * min(num_overlaps - 1, len(lines))
    for ii in range(len(lines) - num_overlaps + 1):
        out.append(comb.join(lines[ii:ii + num_overlaps]))
    return out
    
def _preprocess_line(line):
    line = line.strip()
    if len(line) == 0:
        line = 'BLANK_LINE'
    return line
    

def generateur_lettre_initiale(chars=string.ascii_lowercase):
    # Génère une lettre aléatoire
    return random.choice(chars)[0]


def generateur_id(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits) -> str:
    random_letter = generateur_lettre_initiale()
    random_string = ''.join(random.choice(chars) for _ in range(size))
    return random_letter + random_string



def test_tables_consistency(align_dict, witnesses):
    """
    Cette fonction teste si tous les témoins contiennent bien l'intégralité du texte dans le bon ordre à la fin du processus
    """
    for witness in witnesses:
        print(witness)
        wit_table = []
        for alignment_unit in align_dict:
            wit_table.extend(int(item) for item in alignment_unit[witness])
        last_pos = wit_table[-1]
        ranges = list(range(last_pos + 1))
        is_equal = wit_table == ranges
        if is_equal is False:
            print("Not right")
            print(list(zip(ranges, wit_table)))
            print(type(ranges), type(wit_table))
            print([(a, b) for a, b in list(zip(ranges, wit_table)) if a!=b])
            print(align_dict)
        else:
            print("OK")
    return 

class LANG:
    SPLITTER = {
        'ca': 'Catalan',
        'zh': 'Chinese',
        'cs': 'Czech',
    'la': 'Latin',
        'da': 'Danish',
        'nl': 'Dutch',
        'en': 'English',
        'fi': 'Finnish',
        'fr': 'French',
        'de': 'German',
        'el': 'Greek',
        'hu': 'Hungarian',
        'is': 'Icelandic',
        'it': 'Italian',
        'lt': 'Lithuanian',
        'lv': 'Latvian',
        'no': 'Norwegian',
        'pl': 'Polish',
        'pt': 'Portuguese',
        'ro': 'Romanian',
        'ru': 'Russian',
        'sk': 'Slovak',
        'sl': 'Slovenian',
        'es': 'Spanish',
        'sv': 'Swedish',
        'tr': 'Turkish',
    }
    ISO = {
        'aa': 'Afar',
        'ab': 'Abkhaz',
        'af': 'Afrikaans',
        'ak': 'Akan',
        'am': 'Amharic',
        'an': 'Aragonese',
        'ar': 'Arabic',
        'as': 'Assamese',
        'av': 'Avaric',
        'ay': 'Aymara',
        'az': 'Azerbaijani',
        'ba': 'Bashkir',
        'be': 'Belarusian',
        'bg': 'Bulgarian',
        'bh': 'Bihari',
        'bi': 'Bislama',
        'bm': 'Bambara',
        'bn': 'Bengali',
        'bo': 'Tibetan',
        'br': 'Breton',
        'bs': 'Bosnian',
        'ca': 'Catalan',
        'ce': 'Chechen',
        'ch': 'Chamorro',
        'co': 'Corsican',
        'cr': 'Cree',
        'cs': 'Czech',
        'cv': 'Chuvash',
        'cy': 'Welsh',
        'da': 'Danish',
        'de': 'German',
        'dv': 'Divehi',
        'dz': 'Dzongkha',
        'ee': 'Ewe',
        'el': 'Greek',
        'en': 'English',
        'es': 'Spanish',
        'et': 'Estonian',
        'eu': 'Basque',
        'fa': 'Persian',
        'ff': 'Fula',
        'fi': 'Finnish',
        'fj': 'Fijian',
        'fo': 'Faroese',
        'fr': 'French',
        'fy': 'Western Frisian',
        'ga': 'Irish',
        'gd': 'Scottish Gaelic',
        'gl': 'Galician',
        'gn': 'Guaraní',
        'gu': 'Gujarati',
        'gv': 'Manx',
        'ha': 'Hausa',
        'he': 'Hebrew',
        'hi': 'Hindi',
        'ho': 'Hiri Motu',
        'hr': 'Croatian',
        'ht': 'Haitian',
        'hu': 'Hungarian',
        'hy': 'Armenian',
        'hz': 'Herero',
        'id': 'Indonesian',
        'ig': 'Igbo',
        'ii': 'Nuosu',
        'ik': 'Inupiaq',
        'io': 'Ido',
        'is': 'Icelandic',
        'it': 'Italian',
        'iu': 'Inuktitut',
        'ja': 'Japanese',
        'jv': 'Javanese',
        'ka': 'Georgian',
        'kg': 'Kongo',
        'ki': 'Kikuyu',
        'kj': 'Kwanyama',
        'kk': 'Kazakh',
        'kl': 'Kalaallisut',
        'km': 'Khmer',
        'kn': 'Kannada',
        'ko': 'Korean',
        'kr': 'Kanuri',
        'ks': 'Kashmiri',
        'ku': 'Kurdish',
        'kv': 'Komi',
        'kw': 'Cornish',
        'ky': 'Kyrgyz',
        'la': 'Latin',
        'lb': 'Luxembourgish',
        'lg': 'Ganda',
        'li': 'Limburgish',
        'ln': 'Lingala',
        'lo': 'Lao',
        'lt': 'Lithuanian',
        'lu': 'Luba-Katanga',
        'lv': 'Latvian',
        'mg': 'Malagasy',
        'mh': 'Marshallese',
        'mi': 'Māori',
        'mk': 'Macedonian',
        'ml': 'Malayalam',
        'mn': 'Mongolian',
        'mr': 'Marathi',
        'ms': 'Malay',
        'mt': 'Maltese',
        'my': 'Burmese',
        'na': 'Nauru',
        'nb': 'Norwegian Bokmål',
        'nd': 'North Ndebele',
        'ne': 'Nepali',
        'ng': 'Ndonga',
        'nl': 'Dutch',
        'nn': 'Norwegian Nynorsk',
        'no': 'Norwegian',
        'nr': 'South Ndebele',
        'nv': 'Navajo',
        'ny': 'Chichewa',
        'oc': 'Occitan',
        'oj': 'Ojibwe',
        'om': 'Oromo',
        'or': 'Oriya',
        'os': 'Ossetian',
        'pa': 'Panjabi',
        'pl': 'Polish',
        'ps': 'Pashto',
        'pt': 'Portuguese',
        'qu': 'Quechua',
        'rm': 'Romansh',
        'rn': 'Kirundi',
        'ro': 'Romanian',
        'ru': 'Russian',
        'rw': 'Kinyarwanda',
        'sa': 'Sanskrit',
        'sc': 'Sardinian',
        'sd': 'Sindhi',
        'se': 'Northern Sami',
        'sg': 'Sango',
        'si': 'Sinhala',
        'sk': 'Slovak',
        'sl': 'Slovenian',
        'sm': 'Samoan',
        'sn': 'Shona',
        'so': 'Somali',
        'sq': 'Albanian',
        'sr': 'Serbian',
        'ss': 'Swati',
        'st': 'Southern Sotho',
        'su': 'Sundanese',
        'sv': 'Swedish',
        'sw': 'Swahili',
        'ta': 'Tamil',
        'te': 'Telugu',
        'tg': 'Tajik',
        'th': 'Thai',
        'ti': 'Tigrinya',
        'tk': 'Turkmen',
        'tl': 'Tagalog',
        'tn': 'Tswana',
        'to': 'Tonga',
        'tr': 'Turkish',
        'ts': 'Tsonga',
        'tt': 'Tatar',
        'tw': 'Twi',
        'ty': 'Tahitian',
        'ug': 'Uighur',
        'uk': 'Ukrainian',
        'ur': 'Urdu',
        'uz': 'Uzbek',
        've': 'Venda',
        'vi': 'Vietnamese',
        'wa': 'Walloon',
        'wo': 'Wolof',
        'xh': 'Xhosa',
        'yi': 'Yiddish',
        'yo': 'Yoruba',
        'za': 'Zhuang',
        'zh': 'Chinese',
        'zu': 'Zulu',
    }
