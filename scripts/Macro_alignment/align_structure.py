import os
import shutil

import lxml.etree as ET
import glob
import json

import tqdm

tei_ns = "http://www.tei-c.org/ns/1.0"
ns_decl = {"tei": tei_ns}


def main():
    main_file = "../../data/to_tei/main.xml"
    as_tree = ET.parse(main_file)
    as_tree.xinclude()
    groups_of_lessons = as_tree.xpath("/tei:TEI/child::tei:TEI", namespaces=ns_decl)
    for group in groups_of_lessons:
        lessons = group.xpath("descendant::tei:TEI", namespaces=ns_decl)
        for lesson in lessons:
            print(f"\n\nNew lesson: {lesson}\n")
            filename = lesson.xpath("@xml:id")[0]
            directory_name = filename
            tree = lesson
            print(f"Treating {filename}")
            for division in tree.xpath("descendant::tei:div", namespaces=ns_decl):
                print("New div")
                try:
                    division_level = int(division.xpath("@type")[0])
                    print(f"Div level: {division_level}")
                except IndexError:
                    print("Index error")
                    print(division.xpath("@type"))
                    print(ET.tostring(division, pretty_print=True))
                    print(f"firefox ../../data/to_tei/{filename}/{filename}.xml")
                    print(f"firefox ../../data/tei_aligned/{filename}/{filename}.xml")
                    continue
                div_position = int(
                    division.xpath(f"count(preceding-sibling::tei:div[@type='{division_level}'])",
                                   namespaces=ns_decl)) + 1
                print(f"Div position: {div_position}")
                if division_level == 2:
                    identifier = div_position
                elif division_level == 3:
                    parent = division.xpath("parent::tei:div", namespaces=ns_decl)[0]
                    parent_div_position = int(
                        parent.xpath(f"count(preceding-sibling::tei:div[@type='{division_level - 1}'])",
                                     namespaces=ns_decl)) + 1
                    identifier = f"{parent_div_position}.{div_position}"
                elif division_level == 4:
                    parent = division.xpath("parent::tei:div", namespaces=ns_decl)[0]
                    grandparent = parent.xpath("parent::tei:div", namespaces=ns_decl)[0]
                    parent_div_position = int(
                        parent.xpath(f"count(preceding-sibling::tei:div[@type='{division_level - 1}'])",
                                     namespaces=ns_decl)) + 1
                    grandparent_div_position = int(
                        grandparent.xpath(f"count(preceding-sibling::tei:div[@type='{division_level - 2}'])",
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
                    print(division_level)
                    continue
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
                
                for text_file in glob.glob(f"../../data/to_tei/{filename}/*.txt"):
                    shutil.copy(text_file, f"../../data/tei_aligned/{filename}/")
                
                with open(f"../../data/tei_aligned/{filename}/{filename}.xml", "w") as structured_div:
                    print(f"Saving to ../../data/tei_aligned/{filename}/{filename}.xml")
                    structured_div.write(ET.tostring(tree, pretty_print=True, encoding="utf-8").decode('utf8'))


def copy_main_file():
    new_tree = ET.parse("../../data/to_tei/main.xml")
    xi_namespace={"xi": "http://www.w3.org/2001/XInclude"}
    for inclusion in new_tree.xpath("//xi:include", namespaces=xi_namespace):
        url = inclusion.xpath("@href")[0]
        inclusion.set("href", url.replace("to_tei", "tei_aligned"))

    with open(f"../../data/tei_aligned/main.xml", "w") as structured_div:
        structured_div.write(ET.tostring(new_tree, pretty_print=True, encoding="utf-8").decode('utf8'))

if __name__ == '__main__':
    main()
    copy_main_file()
