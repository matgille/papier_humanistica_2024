import glob
import os

import lxml.etree as ET
import re
import yaml
import marko
from marko.ext.gfm import gfm

tei_ns = "https://tei-c.org/ns/1-0/"
def xmlify(path):
    with open(path, "r") as input_file:
        as_text = input_file.read()
    lesson_name = path.split("/")[-1].replace(".md", "")
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
    transformed = as_text.replace(metadata_as_yaml, "")
    
    footnotes_pattern = re.compile(r"\[\^([^\[\]\^]*)\]:([^\n]*)\n", re.DOTALL)
    transformed = re.sub(footnotes_pattern, rf"<note id='\1'>\2</note>\n", transformed)
    
    footnotemarks_pattern = re.compile(r"\[\^([^\[\]\^]*)\]")
    transformed = re.sub(footnotemarks_pattern, rf"<ref type='footnotemark' target='#\1'/>", transformed)
    
    # GFM extension parses tables too.
    transformed = gfm.convert(transformed)
    
    inclusion_pattern = re.compile(r"\{% include .* filename=\"([^\"]*)\" caption=\"([^\"]*)\" %\}")
    replacement = rf'<inclusion href="\1"><desc>\2</desc></inclusion>'
    transformed = re.sub(inclusion_pattern, replacement, transformed, re.DOTALL)
    
    
    list_items_pattern = re.compile(r"^\s*[-*]([^\n]*)\n", re.MULTILINE)
    transformed = re.sub(list_items_pattern, rf"<item>\1</item>\n", transformed)
    
    
    inline_code_pattern = re.compile("```([^`\n]*)```")
    transformed = re.sub(inline_code_pattern, rf"`\1`", transformed)
    multiline_code_pattern = re.compile("```([^`]*)```")
    transformed = re.sub(multiline_code_pattern, rf"<span type='block_code'>\1</span>", transformed, re.MULTILINE)
    inline_code_pattern = re.compile("`([^`\n]*)`")
    transformed = re.sub(inline_code_pattern, rf"<span type='code'>\1</span>", transformed)
    
    
    emph_pattern = re.compile(r"\*([^\*]*)\*")
    transformed = re.sub(emph_pattern, rf"<emph>\1</emph>", transformed)
    transformed = transformed.replace("&laquo;&#x202F;", "<soCalled>")
    transformed = transformed.replace("&#x202F;&raquo;", "</soCalled>").replace("&nbsp;", "").replace("&#x202F;", "").replace("«", "<quote>").replace("»", "</quote>")
    
    h1_pattern = re.compile("^# ([^\n]*)", re.MULTILINE)
    transformed = re.sub(h1_pattern, rf"<h1>\1</h1>", transformed)
    h2_pattern = re.compile("^## ([^\n]*)", re.MULTILINE)
    transformed = re.sub(h2_pattern, rf"<h2>\1</h2>", transformed)
    h3_pattern = re.compile("^### ([^\n]*)", re.MULTILINE)
    transformed = re.sub(h3_pattern, rf"<h3>\1</h3>", transformed)
    
    url_pattern = re.compile(r"\[([^\[\]]*)\]\(([^\(\)\s]*)\)")
    transformed = re.sub(url_pattern, rf"<ref target='\2'>\1</ref>", transformed)
    
    numbered_list_pattern = re.compile(r"^(\d+)([^\n]*)\n", re.MULTILINE)
    transformed = re.sub(numbered_list_pattern, rf"<item n='\1'>\2</item>\n", transformed)
    
    print(transformed)
    
    document =  transformed 
    with open("/home/mgl/Documents/test/markdown.xml", "w") as output_file:
        output_file.write(document)
        
    
    parser = ET.HTMLParser(recover=True)
    parsed_doc = ET.fromstring(document, parser=parser)
    for section_level in reversed(range(6)):
        level = section_level + 1
        print(f"Processing level {level}")
        all_headings = parsed_doc.xpath(f"//h{level}")
        first_node = parsed_doc.xpath(f"descendant::h{level}[1]")
        all_same_level_nodes = parsed_doc.xpath(f"descendant::h{level}[1]/following-sibling::node()")
        filtered_same_level_nodes = first_node + [element for element in all_same_level_nodes if isinstance(element, ET._Element)]
        clustered_nodes = {}
        headings_number = 0
        for index, node in enumerate(filtered_same_level_nodes):
            if node.tag == f"h{level}":
                current_heading = node
                headings_number += 1
                clustered_nodes[current_heading] = []
            else:
                clustered_nodes[current_heading].append(node)
        for heading, nodes in clustered_nodes.items():
            anchor = heading.xpath("preceding-sibling::node()[1]")
            parent = heading.getparent()
            heading_level = heading.tag.replace("h", "")
            heading.tag = "head"
            position = int(heading.xpath("count(preceding-sibling::node())"))
            element_and_childs = ET.Element(f"div")
            element_and_childs.set("n", heading_level)
            print(heading_level)
            element_and_childs.append(heading)
            for node in nodes:
                element_and_childs.append(node)
            parent.append(element_and_childs)
    print(ET.tostring(parsed_doc))
    
    # Let's TEIfy it
    root = parsed_doc.xpath("/node()")[0]
    root.tag = "TEI"
    root.set('xmlns', tei_ns)
    root.insert(0, ET.fromstring(metadata_as_xml))
    text_element = ET.Element("text")
    body = root.xpath("//body")
    text_element.append(body[0])
    root.insert(1, text_element)
    
            
    with open(f"/home/mgl/Documents/test/{lesson_name}_clean.xml", "w") as output_file:
        # TODO: single asterisks are not rendered and break the HTML. After ET recovery, they are lost. I suppose the same
        # TODO: happens with other chars. It's annoying.
        # TODO: Another problem with regexp lesson: last urls disapear.
        output_file.write(ET.tostring(parsed_doc, pretty_print=True).decode('utf-8'))

    exit(0)
        
        
if __name__ == '__main__':
    regexp = r"/home/mgl/Bureau/Travail/PH/jekyll/(es|fr|en|pt)/l[^/]*/[^/]*\.md"
    lessons = [f for f in glob.glob("/home/mgl/Bureau/Travail/PH/jekyll/*/l*/*.md") if re.search(regexp, f)]
    for lesson in lessons:
        print(lesson)
        xmlify(lesson)