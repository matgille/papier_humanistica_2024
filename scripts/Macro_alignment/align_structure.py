import os

import lxml.etree as ET
import glob
import json



tei_ns = "http://www.tei-c.org/ns/1.0"
ns_decl = {"tei": tei_ns}

def main(directory):
    for file in glob.glob(f"{directory}/*.xml"):
        filename = file.split("/")[-1]
        directory_name = directory.split('/')[-1]
        tree = ET.parse(file)
        print(f"Treating {file}")
        for division in tree.xpath("//tei:div", namespaces=ns_decl):
            print("New div")
            try:
                division_level = int(division.xpath("@type")[0])
                print(f"Div level: {division_level}")
            except IndexError:
                print(file)
                exit(0)
            div_position = int(division.xpath(f"count(preceding-sibling::tei:div[@type='{division_level}'])", namespaces=ns_decl)) + 1
            print(f"Div position: {div_position}")
            if division_level == 2:
                identifier = div_position
            elif division_level == 3:
                parent = division.xpath("parent::tei:div", namespaces=ns_decl)[0]
                parent_div_position = int(parent.xpath(f"count(preceding-sibling::tei:div[@type='{division_level - 1}'])",
                                                  namespaces=ns_decl)) + 1
                identifier = f"{parent_div_position}.{div_position}"
            elif division_level == 4:
                parent = division.xpath("parent::tei:div", namespaces=ns_decl)[0]
                grandparent = parent.xpath("parent::tei:div", namespaces=ns_decl)[0]
                parent_div_position = int(parent.xpath(f"count(preceding-sibling::tei:div[@type='{division_level - 1}'])",
                                                  namespaces=ns_decl)) + 1
                grandparent_div_position = int(grandparent.xpath(f"count(preceding-sibling::tei:div[@type='{division_level - 2}'])",
                                                  namespaces=ns_decl)) + 1
                identifier = f"{grandparent_div_position}.{parent_div_position}.{div_position}"

            elif division_level == 5:
                parent = division.xpath("parent::tei:div", namespaces=ns_decl)[0]
                grandparent = parent.xpath("parent::tei:div", namespaces=ns_decl)[0]
                greatgrandparent = grandparent.xpath("parent::tei:div", namespaces=ns_decl)[0]
                parent_div_position = int(
                    parent.xpath(f"count(preceding-sibling::tei:div[@type='{division_level - 1}'])",
                                 namespaces=ns_decl)) + 1
                grandparent_div_position = int(
                    grandparent.xpath(f"count(preceding-sibling::tei:div[@type='{division_level - 2}'])",
                                      namespaces=ns_decl)) + 1
                greatgrandparent_div_position = int(
                    greatgrandparent.xpath(f"count(preceding-sibling::tei:div[@type='{division_level - 3}'])",
                                      namespaces=ns_decl)) + 1
                identifier = f"{greatgrandparent_div_position}.{grandparent_div_position}.{parent_div_position}.{div_position}"
            else:
                print("Something went wrong")
                exit(0)
            print(f"Identifier: {identifier}")
            division.set("n", str(identifier))
            
            # try:
            try:
                os.mkdir(f"../../data/tei_aligned/{directory_name}")
            except FileExistsError:
                pass
            except FileNotFoundError:
                os.mkdir(f"../../data/tei_aligned/")
                os.mkdir(f"../../data/tei_aligned/{directory_name}")
            
            with open(f"../../data/tei_aligned/{directory_name}/{filename}", "w") as structured_div:
                print(f"Saving to ../../data/tei_aligned/{directory_name}/{filename}")
                structured_div.write(ET.tostring(tree, pretty_print=True, encoding="utf-8").decode('utf8'))


if __name__ == '__main__':
    with open("logs/lessons_to_align.json", "r") as lessons:
        lessons_to_align = json.load(lessons)
    print(lessons_to_align)
    for directory in lessons_to_align:
        print(directory)
        main(directory)