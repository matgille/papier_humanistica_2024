import json
import os

import lxml.etree as ET
import glob



tei_ns = "https://tei-c.org/ns/1-0/"
ns_decl = {"tei": tei_ns}

def write_to_log(message, file):
    with open(f"logs/{file}", "a") as log_file:
        log_file.write("\n"+message)


def main(directory):
    structures = []
    languages = []
    result = ""
    files = glob.glob(f"{directory}/*.xml")
    if len(files) != 1:
        print(directory)
        for file in files:
            parsed = ET.parse(file)
            divisions = parsed.xpath("//tei:div/@type", namespaces=ns_decl)
            lang = parsed.xpath("//tei:text/@xml:lang", namespaces=ns_decl)[0]
            languages.append(lang)
            structures.append((lang,divisions))
        if all([structure == structures[0][1] for lang, structure in structures]):
            if "fr" in languages:
                write_to_log(f"Lesson {directory} can be aligned by structure.", "log.txt")
                result = directory
        elif not(all([structure == structures[0][1] for lang, structure in structures])) and all([len(structure) == len(structures[0][1]) for lang, structure in structures]):
            struct_as_string = '\n'.join([str(item) for item in structures])
            write_to_log(f"Lesson {directory} shows different structure between translations: \n{struct_as_string}", "log_to_correct.txt")
        
    return result


if __name__ == '__main__':
    lessons_to_align = []
    for file in glob.glob("logs/*"):
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
    for base_dir in glob.glob(f"../../data/to_tei/*"):
        result = main(base_dir)
        if result != "":
            lessons_to_align.append(result)
        with open("logs/lessons_to_align.json", "w") as output_json:
            json.dump(lessons_to_align, output_json)