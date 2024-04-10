import glob
import os
import lxml.etree as ET
import re
import yaml
from marko.ext.gfm import gfm

tei_ns = "http://www.tei-c.org/ns/1.0"
ns_decl = {"tei": tei_ns}


def create_new_node(dictionnary:dict, target_node:str, target_attr:tuple, parent_node:ET._Element, sourceKey:str):
    """
    This function updates the XML tree according with a given JSON dict.
    :param dictionnary: 
    :param NodeName: 
    :param target_node: 
    :param target_attr: 
    :param parent_node: 
    :param sourceKey: 
    :return: 
    """
    tgt = ET.Element(target_node)
    try:
        if dictionnary[sourceKey] and len(dictionnary[sourceKey]) == 1:
            tgt.text = dictionnary[sourceKey][0]
        else:
            if dictionnary[sourceKey]:
                for author in dictionnary[sourceKey]:
                    Name_Node = ET.Element("persName")
                    Name_Node.text = author
                    tgt.append(Name_Node)
        parent_node.append(tgt)
        tgt.set(target_attr[0], target_attr[1])
    except KeyError:
        print(f"Error")

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
    
    language = re.search(r"/(es|fr|en|pt)/", path).groups()[0]
    
    # Getting the path to output file
    with open(path, "r") as input_file:
        as_text = input_file.read()
        
    lesson_name = path.split("/")[-1].replace(".md", "")
    
    ## Metadata management; yaml-xml conversion
    minimal_teiHeader = """<teiHeader>
 <fileDesc>
  <titleStmt>
   <title/>
  </titleStmt>
  <publicationStmt>
   <p>Lesson reviewed and published in Programming Historian.</p>
  </publicationStmt>
  <sourceDesc>
  </sourceDesc>
 </fileDesc>
 <profileDesc/>
</teiHeader>
    """
    metadata_as_yaml = as_text.split("---")[1]
    python_dict=yaml.load(metadata_as_yaml,Loader=yaml.SafeLoader)
    print(python_dict)
    new_metadata = ET.fromstring(minimal_teiHeader)
    title_node = new_metadata.xpath("//title")[0]
    title_node.text = python_dict['title']
    titleStmt = new_metadata.xpath("//titleStmt")[0]
    
    publicationStmt =  new_metadata.xpath("//publicationStmt")[0]
    date = ET.Element("date")
    date.set("type", "published")
    try:
        date.text = python_dict['date'].strftime('%m/%d/%Y')
        publicationStmt.insert(0, date)
    except KeyError:
        pass
    

    try:
        date = ET.Element("date")
        date.set("type", "translated")
        date.text = python_dict['translation_date'].strftime('%m/%d/%Y')
        publicationStmt.insert(1, date)
    except KeyError:
        pass
    
    
    
    try:
        doi = python_dict['doi']
        idno = ET.Element("idno")
        idno.set("type", "doi")
        idno.text = doi
        publicationStmt.insert(0, idno)
    except KeyError:
        pass
    
    
    profileDesc =  new_metadata.xpath("//profileDesc")[0]
    try:
        abstract = ET.Element("abstract")
        p_element = ET.Element("p")
        p_element.text = python_dict["abstract"]
        abstract.append(p_element)
        profileDesc.append(abstract)
    except KeyError:
        pass

    try:
        textClass = ET.Element("textClass")
        topics = python_dict["topics"]
        for topic in topics:
            keyword = ET.Element("keyword")
            keyword.set("{http://www.w3.org/XML/1998/namespace}lang", "en")
            keyword.text = topic
            textClass.append(keyword)
        profileDesc.append(textClass)
    except KeyError:
        pass
    
    
    sourceDesc = new_metadata.xpath("//sourceDesc")[0]
    try:
        python_dict['original']
        new_p_text = f"<p>Born digital, in a markdown format. Original file: <ref type='original_file' target='#{python_dict['original']}'/>.</p>"
    except KeyError:
        new_p_text = f"<p>Born digital, in a markdown format. This lesson is original.</p>"
    as_node = ET.fromstring(new_p_text)
    sourceDesc.append(as_node)
    
    
    

    create_new_node(dictionnary=python_dict,
                    target_node="author",
                    target_attr=("type", "original_author"),
                    parent_node=titleStmt,
                    sourceKey='authors')

    create_new_node(dictionnary=python_dict, 
                    target_node="editor", 
                    target_attr=("type","reviewers"),
                    parent_node=titleStmt,
                    sourceKey='reviewers')
    
    create_new_node(dictionnary=python_dict,
                    target_node="author",
                    target_attr=("type", "translators"),
                    parent_node=titleStmt,
                    sourceKey='translator')


    create_new_node(dictionnary=python_dict, 
                    target_node="editor", 
                    target_attr=("type","translation-reviewers"),
                    parent_node=titleStmt,
                    sourceKey='translation-reviewer')


    
    
    create_new_node(dictionnary=python_dict, 
                    target_node="editor", 
                    target_attr=("type","editors"),
                    parent_node=titleStmt,
                    sourceKey='editors')
    
    metadata_as_xml = ET.tostring(new_metadata, pretty_print=True, encoding='utf8').decode()
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
                # heading.tag = f"h{str(section_level)}"
        
    
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
            parent_nodes = lesson_as_xml_tree.xpath(f"//div[@type = '{level - 1}']")
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
                division_and_descendants.set("type", heading_level)
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
    root.set("xml:id", lesson_name.split("/")[-1].split(".")[0])
    root.insert(0, new_metadata)
    text_element = ET.Element("text")
    body = root.xpath("//body")
    text_element.append(body[0])
    root.insert(1, text_element)
    # Let's add the language
    text_element.set("xml:lang", str(language))
    

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
    change_element_name(root, "div[@class='alert alert-warning']", "p", "style", "alert alert-warning")
    change_element_name(root, "div[@class='alert alert-info']", "p", "style", "alert alert-info")
    change_element_name(root, "div[@class='alert alert-block alert-warning']", "p", "style", "alert alert-block alert-warning")
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

def link_lessons():
    """
    This function parses all the trees and links the original lessons and translations. It adds the information 
    to the teiHeader
    :return: None
    """
    print("Linking lessons")
    tei_ns = "http://www.tei-c.org/ns/1.0"
    ns_decl = {"tei": tei_ns}
    all_lessons = dict()
    for lesson in glob.glob("../../data/to_tei/*/*.xml"):
        as_tree = ET.parse(lesson)
        id = as_tree.xpath("@xml:id", namespaces=ns_decl)[0]
        if len(as_tree.xpath("//tei:sourceDesc/descendant::tei:ref", namespaces=ns_decl)) == 0:
            all_lessons[id] = []

    for lesson in glob.glob("../../data/to_tei/*/*.xml"):
        as_tree = ET.parse(lesson)
        id = as_tree.xpath("@xml:id", namespaces=ns_decl)[0]
        if len(as_tree.xpath("//tei:sourceDesc/descendant::tei:ref", namespaces=ns_decl)) != 0:
            corresp = as_tree.xpath("//tei:sourceDesc/descendant::tei:ref/@target", namespaces=ns_decl)[0]
            corresp = corresp.replace("#", "")
            all_lessons[corresp].append(id)
    
    for lesson in glob.glob("../../data/to_tei/*/*.xml"):
        as_tree = ET.parse(lesson)
        id = as_tree.xpath("@xml:id", namespaces=ns_decl)[0]

        # Si il s'agit d'une leçon originale.
        source_desc_p = as_tree.xpath("//tei:sourceDesc/tei:p", namespaces=ns_decl)[0]
        if id in all_lessons:
            refs = " ".join(f"#{element}" for element in all_lessons[id])
            source_desc_p.text = f"{source_desc_p.text} Available translations are the following:"
            ref_element = ET.Element("ref")
            ref_element.set("type", "translations")
            ref_element.set("target", refs)
            source_desc_p.append(ref_element)
        else:
            if any(id in translated for translated in all_lessons.values()):
                source_desc = as_tree.xpath("//tei:sourceDesc", namespaces=ns_decl)[0]
                new_p = ET.Element("p")
                correct_index = [index for index, translated in enumerate(all_lessons.values()) if id in translated][0]
                corresponding_lessons = " ".join([f"#{element}" for element in list(all_lessons.values())[correct_index] if element != id])
                new_ref = ET.Element("ref")
                new_ref.set("target", corresponding_lessons)
                new_p.text = "There are other translations: "
                new_p.append(new_ref)
                source_desc.append(new_p)
                
            
        # Let's serialize the tree.
        with open(lesson, "w") as output_file:
            output_file.write(ET.tostring(as_tree, pretty_print=True).decode('utf-8'))

    
    

        
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
    
    link_lessons()