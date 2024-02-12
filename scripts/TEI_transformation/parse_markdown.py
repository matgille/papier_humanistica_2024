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


def write_tree(tree, name):
    with open(f"/home/mgl/Documents/test/{name}.xml", "w") as debug:
        debug.write(ET.tostring(tree).decode('utf8'))


def xmlify(path):
    """
    This function takes a md file and returns a TEI-like document (not fully compliant though)
    :param path: path to the md file
    :return: None; creates a TEI file
    """
    with open(path, "r") as input_file:
        as_text = input_file.read()
        
    lesson_name = path.split("/")[-1].replace(".md", "")
    
    ## Metadata management; yaml-xml conversion
    metadata_as_yaml = as_text.split("---")[1]
    print(metadata_as_yaml)
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
    inclusion_pattern = re.compile(r"\{% include figure.html filename=\"(.*)\" caption=\"(.*)\" %\}")
    replacement = rf'<inclusion href="\1"><desc>\2</desc></inclusion>'
    transformed = re.sub(inclusion_pattern, replacement, transformed)
    
    
    # GFM extension of marko parses tables too.
    transformed = gfm.convert(transformed)
    print(transformed)
    
    document = transformed
    
    
    parser = ET.HTMLParser(recover=True)
    parsed_doc = ET.fromstring(document, parser=parser)
    
    # We then
    write_tree(parsed_doc, "debug_before")
    for section_level in range(6):
        level = section_level + 1
        print(f"Processing level {level}")
        all_headings = parsed_doc.xpath(f"//h{level}")
        print(all_headings)
        if level == 1:
            parent_nodes = [parsed_doc]
        else:
            parent_nodes = parsed_doc.xpath(f"//div[@n = '{level - 1}']")
        for parent_node in parent_nodes:
            first_node = parent_node.xpath(f"descendant::h{level}[1]")
            all_same_level_nodes = parent_node.xpath(f"descendant::h{level}[1]/following-sibling::node()")
            filtered_same_level_nodes = first_node + [element for element in all_same_level_nodes if isinstance(element, ET._Element)]
            clustered_nodes = {}
            print(filtered_same_level_nodes)
            for index, node in enumerate(filtered_same_level_nodes):
                if node.tag == f"h{level}":
                    current_heading = node
                    clustered_nodes[current_heading] = []
                else:
                    clustered_nodes[current_heading].append(node)
            print(f"Found {len(clustered_nodes)} nodes.")
            for heading, nodes in clustered_nodes.items():
                print(heading)
                parent = heading.getparent()
                heading_level = heading.tag.replace("h", "")
                heading.tag = "head"
                element_and_childs = ET.Element(f"div")
                element_and_childs.set("n", heading_level)
                print(heading_level)
                element_and_childs.append(heading)
                for node in nodes:
                    element_and_childs.append(node)
                parent.append(element_and_childs)
    write_tree(parsed_doc, "debug_after")
    exit(0)
    
    # Getting the path to output file
    original_file = parsed_doc.xpath("//original")
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
    for block_code in parsed_doc.xpath("//pre/code"):
        id = "id_" + str(uuid.uuid4()).split("-")[0]
        content = block_code.text
        block_code.text = ""
        block_code.set("xml:id", id)
        block_code.set("corresp", f"{id}.txt")
        with open(f"../../data/to_tei/{dir_name}/{id}.txt", "w") as output_code:
            output_code.write(content)
    
    # TODO: turn the following lines into a function to avoid redundancy
    # Let's move block codes in the previous paragraph
    for block_code in parsed_doc.xpath("//pre/code", namespaces=ns_decl):
        previous_p = block_code.xpath("parent::pre/preceding-sibling::p[1]")[0]
        nodes_number = int(previous_p.xpath("count(child::node())"))
        previous_p.insert(nodes_number, block_code)
    # Now remove the empty pre
    for empty_pre in parsed_doc.xpath("//pre", namespaces=ns_decl):
        empty_pre.getparent().remove(empty_pre)
        
        
    # Let's do the same with the lists
    for index, xml_list in enumerate(parsed_doc.xpath("//node()[self::ul or self::ol]", namespaces=ns_decl)):
        try:
            previous_p = xml_list.xpath("preceding-sibling::p[1]")[0]
            nodes_number = int(previous_p.xpath("count(child::node())"))
            previous_p.insert(nodes_number, xml_list)
        except Exception:
            traceback.print_exc()
            print(lesson_name)
            print(index)
            write_tree(parsed_doc)
            exit(0)
            following_p = xml_list.xpath("following-sibling::p[1]")[0]
            following_p.insert(0, xml_list)
    
        
    # And with the inclusions
    for index, inclusion in enumerate(parsed_doc.xpath("//p/inclusion", namespaces=ns_decl)):
        try:
            previous_p = inclusion.xpath("parent::p/preceding-sibling::p[1]")[0]
            nodes_number = int(previous_p.xpath("count(child::node())"))
            previous_p.insert(nodes_number, inclusion)
        except IndexError as e:
            traceback.print_exc()
            print(lesson_name)
            print(index)
            following_p = inclusion.xpath("parent::p/following-sibling::p[1]")[0]
            following_p.insert(0, inclusion)
            with open("/home/mgl/Documents/test/debug.xml", "w") as debug:
                debug.write(ET.tostring(parsed_doc).decode('utf8'))
    # Now remove the empty pre
    for empty_pre in parsed_doc.xpath("//p[not(node())]", namespaces=ns_decl):
        empty_pre.getparent().remove(empty_pre)
    
    
    # Let's TEIfy it
    root = parsed_doc.xpath("/node()")[0]
    # Converting HTML root to TEI, adding correct namespace
    root.tag = "TEI"
    root.set('xmlns', tei_ns)
    root.insert(0, ET.fromstring(metadata_as_xml))
    text_element = ET.Element("text")
    body = root.xpath("//body")
    text_element.append(body[0])
    root.insert(1, text_element)
    
            
    with open(f"../../data/to_tei/{dir_name}/{lesson_name}.xml", "w") as output_file:
        # TODO: single asterisks are not rendered and break the HTML. After ET recovery, they are lost. I suppose the same
        # TODO: happens with other chars. It's annoying.
        # TODO: Another problem with regexp lesson: last urls disapear.
        # TODO: linebreaks in code are removed by lxml. 
        output_file.write(ET.tostring(parsed_doc, pretty_print=True).decode('utf-8'))

        
if __name__ == '__main__':
    
    # Let's select the lessons in all languages
    regexp = r"/home/mgl/Bureau/Travail/PH/jekyll/(es|fr|en|pt)/l[^/]*/[^/]*\.md"
    lessons = [f for f in glob.glob("/home/mgl/Bureau/Travail/PH/jekyll/*/l*/*.md") if re.search(regexp, f)]
    lessons = glob.glob("/home/mgl/Bureau/Travail/PH/jekyll/*/l*/generating-an-ordered-data-set-from-an-OCR-text-file.md")
    for lesson in lessons:
        print(lesson)
        xmlify(lesson)