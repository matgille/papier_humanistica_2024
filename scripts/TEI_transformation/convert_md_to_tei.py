import glob
import os
import traceback
import uuid
import lxml.etree as ET
import re
import yaml
import marko
from marko.ext.gfm import gfm

tei_ns = "https://tei-c.org/ns/1-0/"
ns_decl = {"tei": tei_ns}


def pop_element(tree, element_name):
    for element in tree.xpath(f"//{element_name}"):
        element.getparent().remove(element)

def write_to_log(message):
    with open("logs/log.txt", "a") as log_file:
        log_file.write("\n"+message)


def change_element_name(tree, element, replacement, attr=None, attr_value=None, attr_change:tuple=None):
    for element in tree.xpath(f"//{element}"):
        element.tag = replacement
        if attr:
            element.set(attr, attr_value)
        if attr_change:
            orig, reg = attr_change
            current_attr_value = element.xpath(f"@{orig}")[0]
            element.set(reg, current_attr_value)
            element.attrib.pop(orig)
            write_tree(tree, "test")
            


def write_tree(tree, name):
    with open(f"/home/mgl/Documents/test/{name}.xml", "w") as debug:
        debug.write(ET.tostring(tree).decode('utf8'))


def xmlify(path):
    """
    This function takes a md file and returns a TEI-like document (not fully compliant though)
    :param path: path to the md file
    :return: None; creates a TEI file
    """
    # TODO: get back to endnotes
    
    # Getting the path to output file
    with open(path, "r") as input_file:
        as_text = input_file.read()
        
    lesson_name = path.split("/")[-1].replace(".md", "")
    
    ## Metadata management; yaml-xml conversion
    metadata_as_yaml = as_text.split("---")[1]
    python_dict=yaml.load(metadata_as_yaml,Loader=yaml.SafeLoader)
    metadata = ET.Element("metadata")
    for key, values in python_dict.items():
        new_element = ET.Element(key)
        if type(values) is list:
            new_element.text = ",".join(values)
        else:
            new_element.text = str(values)
        metadata.append(new_element)
    metadata_as_xml = ET.tostring(metadata, pretty_print=True, encoding='utf8').decode()
    # We remove the metadata from the text file
    transformed = as_text.replace(metadata_as_yaml, "")
    ## Metadata management
    
    

    
    # Let's remove some unuseful data
    transformed = transformed.replace("{% include toc.html %}", "")
    transformed = transformed.replace("<hr/>", "")
    
    
    ## Next, some regexp-based rules to identify tricky elements (footnotes, etc)
    footnotes_pattern = re.compile(r"\[\^([^\[\]\^]*)\]:([^\n]*)\n", re.DOTALL)
    transformed = re.sub(footnotes_pattern, rf"<note id='\1'>\2</note>\n", transformed)
    
    footnotemarks_pattern = re.compile(r"\[\^([^\[\]\^]*)\]")
    transformed = re.sub(footnotemarks_pattern, rf"<ref type='footnotemark' target='#\1'/>", transformed)
    
    # Inclusions
    inclusion_pattern = re.compile(r"\{% include .* filename=\"(.*)\" caption=\"(.*)\" %\}", re.MULTILINE)
    replacement = rf'<figure><desc>\2</desc><graphic url="\1"></graphic></figure>'
    transformed = re.sub(inclusion_pattern, replacement, transformed)
    
    
    # GFM extension of marko parses tables too.
    converted_doc = gfm.convert(transformed)
    parser = ET.HTMLParser(recover=True)
    
    
    
    # We then Structure the document
    lesson_as_xml_tree = ET.fromstring(converted_doc, parser=parser)
    
    ## First we need to correct the structure. The first level of division will be 1.
    all_headings = []
    for section_level in range(6):
        all_headings.extend([element.tag.replace("h", "") for element in lesson_as_xml_tree.xpath(f"//h{section_level}")])
    different_headings = [int(val) for val in list(set(all_headings))]
    minimal_heading = min(different_headings)
    print(minimal_heading)

    print("Structure check")
    heading_check = True
    minimal_heading_check = True
    structural_jump_check = True
    all_heads = [int(element.tag.replace("h", "")) for element in lesson_as_xml_tree.xpath(f"//node()[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]")]
    if int(all_heads[0]) != 2:
        heading_check = False
    if int(all_heads[0]) != int(minimal_heading):
        minimal_heading_check = False
    if any([all_heads[n] - all_heads[n + 1] < - 1 for n in range(len(all_heads[:-1]))]):
        structural_jump_check = False
    # We modify just in case of 
    
    # Write log
    if all(check is True for check in [minimal_heading_check, structural_jump_check, heading_check]):
        pass
    else:
        write_to_log(f"Lesson {lesson_name}")
        write_to_log(f"Lesson structure: [{','.join([str(head) for head in all_heads])}]")
        if minimal_heading_check is False:
            write_to_log(f"Structural issue. Check heading levels.")
        if heading_check is False:
            write_to_log(f"Lesson  starts with heading of level {str(all_heads[0])}. ")
            if minimal_heading_check is True and structural_jump_check is True:
                write_to_log(f"It can be corrected without supervision.")
            else:
                write_to_log(f"There is another issue that has to be corrected by hand before solving this one.")
        if structural_jump_check is False:
            write_to_log(f"Structural jump. Check heading levels.")
        write_to_log("\n")
        
    # Correct structure    
    if minimal_heading == 1 and all(check is True for check in [minimal_heading_check, structural_jump_check]):
        for section_level in reversed(range(minimal_heading, 7)):
            all_nodes = lesson_as_xml_tree.xpath(f"descendant::h{section_level}")
            for heading in all_nodes:
                heading.tag = f"h{str(section_level + 1)}"
    elif minimal_heading != 2 and all(check is True for check in [minimal_heading_check, structural_jump_check]):
        for section_level in range(minimal_heading, 6):
            difference = minimal_heading - 2
            all_nodes = lesson_as_xml_tree.xpath(f"descendant::h{section_level}")
            for heading in all_nodes:
                heading.tag = f"h{str(section_level - difference)}"
        
    
    # TODO: structure coherence check
    ## First we need to correct the structure. The first level of division will be 1.
    
    ## After that, we can start restructuring the document, using the headers. 
    # Here we start with the larger divisions, narrowing gradually the scope, and parsing each part of the tree
    #  in successive order.
    for section_level in range(0, 6):
        level = section_level + 1
        if level == 1 or level == 2:
            parent_nodes = [lesson_as_xml_tree]
        else:
            # We use the tree updated in a previous run (h1 > div @n=1, then h2 > div @n=2, etc)  
            parent_nodes = lesson_as_xml_tree.xpath(f"//div[@n = '{level - 1}']")
        for parent_node in parent_nodes:
            first_node = parent_node.xpath(f"descendant::h{level}[1]")
            all_same_level_nodes = parent_node.xpath(f"descendant::h{level}[1]/following-sibling::node()")
            filtered_same_level_nodes = first_node + [element for element in all_same_level_nodes if isinstance(element, ET._Element)]
            clustered_nodes = {}
            # This dict method is really usefull, unlike this comment
            for index, node in enumerate(filtered_same_level_nodes):
                if node.tag == f"h{level}":
                    current_heading = node
                    clustered_nodes[current_heading] = []
                else:
                    clustered_nodes[current_heading].append(node)
            for heading, nodes in clustered_nodes.items():
                parent = heading.getparent()
                # Let's replace h{X} with <head/>
                heading_level = heading.tag.replace("h", "")
                heading.tag = "head"
                # Add the division heading
                division_and_descendants = ET.Element(f"div")
                # Attribute n='X'
                division_and_descendants.set("n", heading_level)
                # Append the childs found with the dict method, starting with the new heading
                division_and_descendants.append(heading)
                for node in nodes:
                    division_and_descendants.append(node)
                # Find and append the newly division to its parent
                # We work sequentially, so we can append the division at the end of its parent.
                parent.append(division_and_descendants)
    
    
    
    
    # TODO: move block codes in the previous paragraph (doesnt work, see in the future)
    # for index, block_code in enumerate(lesson_as_xml_tree.xpath("//pre/code", namespaces=ns_decl)):
    #     try:
    #         previous_p = block_code.xpath("parent::pre/preceding-sibling::p[1]")[0]
    #     except IndexError:
    #         traceback.print_exc()
    #         print(lesson_name)
    #         print(index)
    #     nodes_number = int(previous_p.xpath("count(child::node())"))
    #     previous_p.insert(nodes_number, block_code)
    # # Now remove the empty pre
    # for empty_pre in lesson_as_xml_tree.xpath("//pre", namespaces=ns_decl):
    #     empty_pre.getparent().remove(empty_pre)
        
    
    # Let's TEIfy it
    root = lesson_as_xml_tree.xpath("/node()")[0]
    # Converting HTML root to TEI, adding correct namespace
    # TODO: this doesnt affect the whole tree, maybe xslt ? 
    # see https://stackoverflow.com/a/51660868
    root.tag = "TEI"
    root.set('xmlns', tei_ns)
    root.insert(0, ET.fromstring(metadata_as_xml))
    text_element = ET.Element("text")
    body = root.xpath("//body")
    text_element.append(body[0])
    root.insert(1, text_element)

    original_file = lesson_as_xml_tree.xpath("//original")
    if len(original_file) == 1:
        dir_name = original_file[0].text
    else:
        dir_name = lesson_name
    try:
        os.mkdir(f"../../data/to_tei/{dir_name}")
    except FileExistsError:
        pass

    # Block code management: extract them from the document, and write them 
    # to a text file.
    for index, block_code in enumerate(lesson_as_xml_tree.xpath("//pre/code")):
        id = f"code_{lesson_name}_{index}"
        content = block_code.text
        block_code.text = ""
        block_code.set("xml:id", id)
        block_code.set("type", "block")
        block_code.set("corresp", f"{id}.txt")
        with open(f"../../data/to_tei/{dir_name}/{id}.txt", "w") as output_code:
            output_code.write(content)
    
    # Let's modify some tagnames, clean some other
    change_element_name(root, "strong", "hi", "rend", "bold")
    change_element_name(root, "em", "emph")
    change_element_name(root, "code[not(@type)]", "code", "type", "inline")
    change_element_name(root, "a[@href]", "link", attr_change=('href', 'target'))
    pop_element(root, "hr")
    
    
            
    with open(f"../../data/to_tei/{dir_name}/{lesson_name}.xml", "w") as output_file:
        # TODO: single asterisks are not rendered and break the HTML. After ET recovery, they are lost. I suppose the same
        # TODO: happens with other chars. It's annoying.
        # TODO: Another problem with regexp lesson: last urls disapear.
        # TODO: linebreaks in code are removed by lxml. 
        output_file.write(ET.tostring(lesson_as_xml_tree, pretty_print=True).decode('utf-8'))

        
if __name__ == '__main__':
    
    # Let's select the lessons in all languages
    regexp = r"/home/mgl/Bureau/Travail/PH/jekyll/(es|fr|en|pt)/l[^/]*/[^/]*\.md"
    lessons = [f for f in glob.glob("/home/mgl/Bureau/Travail/PH/jekyll/*/l*/*.md") if re.search(regexp, f)]
    # lessons = glob.glob("/home/mgl/Bureau/Travail/PH/jekyll/*/l*/generer-jeu-donnees-texte-ocr.md")
    # Removing log file
    try:
        os.remove("logs/log.txt")
    except FileNotFoundError:
        pass
    for lesson in lessons:
        print(lesson)
        xmlify(lesson)