import glob
import os
import lxml.etree as ET
import re
import yaml
from marko.ext.gfm import gfm

tei_ns = "http://www.tei-c.org/ns/1.0"
ns_decl = {"tei": tei_ns}


def remove_parent_keep_self(tree, ancestors, node):
    print(ancestors)
    ancestors = tree.xpath(ancestors)
    print(ancestors)
    for ancestor in ancestors:
        # We have to reverse the list to get the order correct
        for elem in reversed(ancestor.xpath("*")):
            print(elem)
            ancestor.addnext(elem)
        ancestor.getparent().remove(ancestor)


def create_new_node(dictionnary: dict, target_node: str, target_attr: tuple, parent_node: ET._Element, sourceKey: str):
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
        log_file.write("\n" + message)


def pop_attribute(tree, element, attribute_name):
    for element in tree.xpath(f"//{element}[@{attribute_name}]"):
        element.attrib.pop(attribute_name, None)


def pop_element(tree, element):
    for element in tree.xpath(f"//{element}"):
        element.getparent().remove(element)


def wrap_element(tree, target_element, wrapping_element):
    for element in tree.xpath(target_element):
        wrapper = ET.Element(wrapping_element)
        element.addprevious(wrapper)
        wrapper.append(element)
        print("Wrapped.")


def change_element_name(tree, element, replacement, attr=None, attr_value=None, attr_change: dict = None):
    for element in tree.xpath(f"//{element}"):
        element.tag = replacement
        if attr:
            element.set(attr, attr_value)
        if attr_change:
            for orig, reg in attr_change.items():
                try:
                    current_attr_value = element.xpath(f"@{orig}")[0]
                    element.set(reg, current_attr_value)
                    element.attrib.pop(orig)
                except IndexError:
                    pass


def write_tree(tree, name):
    with open(f"/home/mgl/Documents/test/{name}.xml", "w") as debug:
        debug.write(ET.tostring(tree).decode('utf8'))


def save_file(string, path):
    with open(path, "w") as output_file:
        output_file.write(string)


def xmlify(path):
    """
    This function takes a md file and returns a TEI document. It is the core of this python script.
    :param path: path to the md file
    :return: None; creates a TEI file
    """

    language = re.search(r"/(es|fr|en|pt)/", path).groups()[0]

    # Getting the path to output file
    with open(path, "r") as input_file:
        as_text = input_file.read()

    lesson_name = path.split("/")[-1].replace(".md", "")

    print(f"../../data/to_tei/{lesson_name}/{lesson_name}.xml")

    ## Metadata management; yaml-xml conversion
    minimal_teiHeader = """<teiHeader>
 <fileDesc>
  <titleStmt>
   <title/>
  </titleStmt>
  <publicationStmt/>
  <sourceDesc>
  </sourceDesc>
 </fileDesc>
 <profileDesc/>
</teiHeader>
    """
    metadata_as_yaml = as_text.split("---")[1]
    python_dict = yaml.load(metadata_as_yaml, Loader=yaml.SafeLoader)
    print(python_dict)
    new_metadata = ET.fromstring(minimal_teiHeader)
    title_node = new_metadata.xpath("//title")[0]
    title_node.text = python_dict['title']
    titleStmt = new_metadata.xpath("//titleStmt")[0]

    publicationStmt = new_metadata.xpath("//publicationStmt")[0]

    distributor = ET.Element("distributor")
    distributor.text = "Programming Historian"
    publicationStmt.append(distributor)
    try:
        doi = python_dict['doi']
        idno = ET.Element("idno")
        idno.set("type", "doi")
        idno.text = doi
        publicationStmt.append(idno)
    except KeyError:
        pass

    try:
        date = ET.Element("date")
        date.set("type", "translated")
        date.text = python_dict['translation_date'].strftime('%m/%d/%Y')
        publicationStmt.insert(1, date)
    except KeyError:
        pass

    profileDesc = new_metadata.xpath("//profileDesc")[0]
    try:
        abstract = ET.Element("abstract")
        p_element = ET.Element("p")
        p_element.text = python_dict["abstract"]
        abstract.append(p_element)
        profileDesc.append(abstract)
    except KeyError:
        pass

    date = ET.Element("date")
    date.set("type", "published")
    try:
        date.text = python_dict['date'].strftime('%m/%d/%Y')
        publicationStmt.append(date)
    except KeyError:
        pass

    try:
        textClass = ET.Element("textClass")
        topics = python_dict["topics"]
        keywords = ET.Element("keywords")
        textClass.append(keywords)
        for topic in topics:
            term = ET.Element("term")
            term.set("{http://www.w3.org/XML/1998/namespace}lang", "en")
            term.text = topic
            keywords.append(term)
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
                    target_attr=("role", "original_author"),
                    parent_node=titleStmt,
                    sourceKey='authors')

    create_new_node(dictionnary=python_dict,
                    target_node="editor",
                    target_attr=("role", "reviewers"),
                    parent_node=titleStmt,
                    sourceKey='reviewers')

    create_new_node(dictionnary=python_dict,
                    target_node="author",
                    target_attr=("role", "translators"),
                    parent_node=titleStmt,
                    sourceKey='translator')

    create_new_node(dictionnary=python_dict,
                    target_node="editor",
                    target_attr=("role", "translation-reviewers"),
                    parent_node=titleStmt,
                    sourceKey='translation-reviewer')

    create_new_node(dictionnary=python_dict,
                    target_node="editor",
                    target_attr=("role", "editors"),
                    parent_node=titleStmt,
                    sourceKey='editors')

    metadata_as_xml = ET.tostring(new_metadata, pretty_print=True, encoding='utf8').decode()
    # We remove the metadata from the text file
    transformed = as_text.replace(metadata_as_yaml, "")
    ## Metadata management

    # There is a problem with footnotemarks that are placed before colon, they lead to a wrong note creation.
    # We add a space before the colon to avoid this.
    footnotemark_pattern = r"(\[\^\d+\]):"
    transformed = re.sub(footnotemark_pattern, r"\1 :", transformed)

    # Mathematical formulas in LaTeX markup.
    formulas_pattern = r"\$\$([^\$]*)\$\$"
    transformed = re.sub(formulas_pattern, r"<formula>\1</formula>", transformed)

    # Let's remove some unuseful data
    transformed = transformed.replace("%}", "%}\n\n")
    transformed = transformed.replace("{% include toc.html %}", "")
    transformed = transformed.replace("<hr/>", "")
    transformed = transformed.replace("<br/>", "")

    ## Next, some regexp-based rules to identify tricky elements (footnotes, etc)
    footnotes_pattern = re.compile(r"\[\^([^\[\]\^]*)\]:([^\n]*)\n", re.DOTALL)
    transformed = re.sub(footnotes_pattern, rf"<note id='\1'>\2</note>\n", transformed)

    footnotemarks_pattern = re.compile(r"\[\^([^\[\]\^]*)\]")
    transformed = re.sub(footnotemarks_pattern, rf"<ref type='footnotemark' target='#\1'/>", transformed)

    # Some images are tagged inline, which leads to huge transformation problems.
    inline_images_pattern = re.compile(r"(\!\[[^\[\]]*\]\([^\(\)]*\)):?")
    transformed = re.sub(inline_images_pattern, r"\1\n\n", transformed)
    save_file(transformed, "/home/mgl/Documents/test_image.txt")

    # Inclusions
    inclusion_pattern = re.compile(r"\{% include .* filename=\"(.*)\" caption=\"(.*)\" %\}", re.MULTILINE)
    replacement = rf'<figure><desc>\2</desc><graphic url="\1"></graphic></figure>'
    transformed = re.sub(inclusion_pattern, replacement, transformed)

    # GFM extension of marko parses tables too.
    # Let's strip some markup marko doesnt process correctly, like the style element.
    style_regex = re.compile(r"<style[^>]*>.+?(?=<\/style>)<\/style>", re.DOTALL)
    transformed = re.sub(style_regex, "", transformed)

    # Let's manage the tables not recognized by marko 
    # (when the table line doesnt start and end with a pipe |):
    table_possible_pattern = r"(^[^\|][^<\/>]*\|[^<\/>]*[^\|]$)"
    lesson_as_list_of_lines = transformed.split("\n")
    replacement_list = []
    for line in lesson_as_list_of_lines:
        replacement_list.append(re.sub(table_possible_pattern, r"| \1 |", line))
    transformed = "\n".join(replacement_list)

    # Let's convert the document to HTML
    converted_doc = gfm.convert(transformed)
    converted_doc = converted_doc.replace("<hr />", "")
    converted_doc = converted_doc.replace("<br />", "")
    parser = ET.HTMLParser(recover=True)
    lesson_as_xml_tree = ET.fromstring(converted_doc, parser=parser)
    save_file(transformed, "/home/mgl/Documents/test_after_transformation.md")
    serialize_tree_to_file(lesson_as_xml_tree, "/home/mgl/Documents/test_after_transformation.xml")

    ## Then we need to correct the structure. The first level of division will be 1.
    all_headings = []
    for section_level in range(6):
        all_headings.extend(
            [element.tag.replace("h", "") for element in lesson_as_xml_tree.xpath(f"//h{section_level}")])
    different_headings = [int(val) for val in list(set(all_headings))]
    minimal_heading = min(different_headings)
    print(minimal_heading)

    print("Structure check")
    heading_check = True
    minimal_heading_check = True
    structural_jump_check = True
    all_heads = [int(element.tag.replace("h", "")) for element in lesson_as_xml_tree.xpath(
        f"//node()[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]")]
    if int(all_heads[0]) != 2:
        heading_check = False
    if int(all_heads[0]) != int(minimal_heading):
        minimal_heading_check = False
    if any([all_heads[n] - all_heads[n + 1] < - 1 for n in range(len(all_heads[:-1]))]):
        structural_jump_check = False

    # Write log
    if all(check is True for check in [minimal_heading_check, structural_jump_check, heading_check]):
        write_to_log(f"\n\nLesson {lesson_name}")
        write_to_log(f"All checks passed\n\n")
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
        print("Minimal heading is 1")
        for section_level in reversed(range(minimal_heading, 6)):
            all_nodes = lesson_as_xml_tree.xpath(f"descendant::h{section_level}")
            for heading in all_nodes:
                heading.tag = f"h{str(section_level + 1)}"
    elif minimal_heading != 2 and all(check is True for check in [minimal_heading_check, structural_jump_check]):
        print("Minimal heading not 2")
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
    for section_level in range(0, 7):
        level = section_level + 1
        if level == 1 or level == 2:
            parent_nodes = [lesson_as_xml_tree]
        else:
            # We use the tree updated in a previous run (h1 > div @n=1, then h2 > div @n=2, etc)  
            parent_nodes = lesson_as_xml_tree.xpath(f"//div[@type = '{level - 1}']")
        for parent_node in parent_nodes:
            first_node = parent_node.xpath(f"descendant::h{level}[1]")
            all_same_level_nodes = parent_node.xpath(f"descendant::h{level}[1]/following-sibling::node()")
            filtered_same_level_nodes = first_node + [element for element in all_same_level_nodes if
                                                      isinstance(element, ET._Element)]
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


    # The next phase is to modify the nodes to make them TEI conformant.
    root = lesson_as_xml_tree.xpath("/node()")[0]
    # Let's modify some tagnames, clean some other
    change_element_name(root, "strong", "hi", "rend", "bold")
    change_element_name(root, "div[@class='alert alert-warning']", "p", "style", "alert alert-warning")
    change_element_name(root, "p[ancestor::p[@style='alert alert-warning']]", "p", "style", "alert alert-warning")
    remove_parent_keep_self(root, "//div[parent::p[@style='alert alert-warning']]", "p[@style='alert alert-warning']")
    remove_parent_keep_self(root, "//p[@style='alert alert-warning'][p[@style='alert alert-warning']]", "p[@style"
                                                                                                        "='alert "
                                                                                                        "alert-warning']")
    pop_attribute(root, "p", "role")
    pop_attribute(root, "p", "class")
    print("Changing alert alert-info")
    change_element_name(root, "div[@class='alert alert-info']", "p", "style", "alert alert-info")
    pop_attribute(root, "p[@class='alert alert-info']", "class")
    pop_attribute(root, "p[@class='alert alert-block alert-warning']", "class")
    serialize_tree_to_file(root, "/home/mgl/Documents/test.xml")
    change_element_name(root, "div[@class='alert alert-block alert-warning']", "p", "style",
                        "alert alert-block alert-warning")
    change_element_name(root, "div[@class='alert alert-success']", "p", "style", "alert alert-success")
    change_element_name(root, "em", "emph")
    change_element_name(root, "pre[code]", "ab")
    change_element_name(root, "code", "code", attr_change={'class': 'lang', 'type': 'rend'})
    change_element_name(root, "a[@href]", "ref", attr_change={'href': 'target'})
    change_element_name(root, "ul", "list", "type", "unordered")
    change_element_name(root, "ol", "list", "type", "ordered")
    change_element_name(root, "sup", "hi", "rend", "textsuperscript")
    change_element_name(root, "sub", "hi", "rend", "textsubscript")
    change_element_name(root, "i", "emph")
    change_element_name(root, "blockquote", "quote")
    change_element_name(root, "li", "item")
    pop_element(root, "hr")
    pop_element(root, "br")
    change_element_name(root, "p[parent::figcaption]", "figcaption")
    print("Captions")
    remove_parent_keep_self(root, "//figcaption[figcaption]", "figcaption")

    ## Let's clean the tables
    pop_attribute(root, "table", "border")
    pop_element(root, "colgroup")
    pop_attribute(root, "div", "markdown")
    pop_attribute(root, "div[@class]", "class")
    change_element_name(root, "table", "table", attr_change={'class': 'type'})
    change_element_name(root, "th", "cell")
    change_element_name(root, "td", "cell")
    change_element_name(root, "cell[ancestor::thead]", "cell", "role", "label")
    change_element_name(root, "img", "graphic", attr_change={"src": "url"})
    wrap_element(root, "//graphic[not(ancestor::figure)]", "figure")
    change_element_name(root, "tr", "row")
    pop_attribute(root, "row", "style")
    pop_attribute(root, "row", "class")
    pop_attribute(root, "col", "width")
    remove_parent_keep_self(root, "//thead", "row")
    remove_parent_keep_self(root, "//tbody", "row")
    remove_parent_keep_self(root, "//div[child::table]", "table")
    pop_attribute(root, "cell", "align")
    pop_attribute(root, "cell", "markdown")
    pop_attribute(root, "cell", "rowspan")
    pop_attribute(root, "ref", "title")
    pop_attribute(root, "cell", "valign")
    pop_attribute(root, "row", "style")

    # Let's put the caption back into the tables
    all_captions_outside_table = root.xpath("//caption[following-sibling::node()[self::table]]")
    for caption in all_captions_outside_table:
        following_table = caption.xpath("following-sibling::table[1]")[0]
        following_table.insert(0, caption)
    print(all_captions_outside_table)
    change_element_name(root, "table/caption", "head")

    # This is another problem: the indication of starting point of a numbered list. Ignoring for now
    pop_attribute(root, "list", "start")
    pop_attribute(root, "ref", "download")
    pop_attribute(root, "emph", "class")
    pop_element(root, "a")
    change_element_name(root, "p[parent::p[@style='alert alert-info']]", "p", "rend", "alert")
    remove_parent_keep_self(root, "//p[@style='alert alert-info'][p]", "p")
    pop_attribute(root, "p", "class")

    # Let's TEIfy it
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
    for index, block_code in enumerate(lesson_as_xml_tree.xpath("//ab/code", namespaces=ns_decl)):
        id = f"code_{lesson_name}_{index}"
        content = block_code.text
        block_code.text = ""
        block_code.set("xml:id", id)
        block_code.set("type", "block")
        block_code.set("corresp", f"{id}.txt")
        with open(f"../../data/to_tei/{dir_name}/{id}.txt", "w") as output_code:
            output_code.write(content)

    change_element_name(root, "code[not(@corresp)]", "code", "rend", "inline")
    change_element_name(root, "code[@corresp]", "code", attr_change={'type': 'rend'})

    # Creation of desc elements
    for graphic in root.xpath("//graphic[@title or @alt]"):
        title = graphic.xpath("@title")
        alt = graphic.xpath("@alt")

        desc = ET.Element("desc")
        figDesc = ET.Element("figDesc")
        try:
            title[0]
            desc.text = title[0]
            graphic.append(desc)
        except IndexError:
            pass

        try:
            alt[0]
            figDesc.text = alt[0]
            graphic.addprevious(figDesc)
        except IndexError:
            pass

    pop_attribute(root, "graphic", "alt")
    pop_attribute(root, "graphic", "title")

    # Cleaning refs with no target
    for ref_without_target in root.xpath("//ref[@target='']"):
        url = ref_without_target.text
        ref_without_target.set("target", url)

    print("refs")
    remove_parent_keep_self(root, "//ref[figDesc]", "figDesc")
    change_element_name(root, "figcaption", "desc")
    pop_attribute(root, "//figure[@style='']", "style")
    remove_parent_keep_self(root, "//ab[parent::p]", "*")
    change_element_name(root, "b", "emph")

    # Let's change the notes xml:id
    for note in root.xpath("//note"):
        xml_id = note.xpath("@id")[0]
        note.set("{http://www.w3.org/XML/1998/namespace}id", f"{language}_note_{xml_id}")
    pop_attribute(root, "note", "id")

    for note in root.xpath("//ref[@type='footnotemark']"):
        xml_id = note.xpath("@target")[0].replace("#", "")
        note.set("target", f"#{language}_note_{xml_id}")

    # Let's create a glossary
    change_element_name(root, "dl", "div", "type", "glossary")
    for glossary in root.xpath("//div[@type = 'glossary']"):
        dl_or_dt = glossary.xpath("descendant::node()[self::dt or self::dd]")
        entry = ET.Element("entry")
        for index in range(len(dl_or_dt) - 1):
            if index != 0 and index % 2 == 0:
                entry = ET.Element("entry")
            entry.append(dl_or_dt[index])
            entry.append(dl_or_dt[index + 1])
            glossary.append(entry)
    change_element_name(root, "dt", "form")
    change_element_name(root, "dd", "sense")

    # Let's move the solitary table in the previous div
    move_inside_previous_element(root, "table", "div")
    with open(f"../../data/to_tei/{dir_name}/{lesson_name}.xml", "w") as output_file:
        # TODO: single asterisks are not rendered and break the HTML. After ET recovery, they are lost. I suppose the same
        # TODO: happens with other chars. It's annoying.
        # TODO: Another problem with regexp lesson: last urls disapear.
        # TODO: linebreaks in code are removed by lxml. 
        output_file.write(ET.tostring(root, pretty_print=True).decode('utf-8'))


def move_inside_previous_element(tree, node, previous_sibling):
    """
    This function moves the target element to the preceding division
    :param tree: 
    :return: 
    """
    tables_outside_div = True
    while tables_outside_div:
        alone_elements = tree.xpath(f"//{node}[preceding-sibling::node()[1][self::{previous_sibling}]]",
                                    namespaces=ns_decl)
        for element in alone_elements:
            print(element)
            try:
                previous_div = \
                    element.xpath(f"preceding-sibling::node()[1][self::{previous_sibling}]", namespaces=ns_decl)[0]
                previous_div.append(element)
                print("Moved")
            except IndexError:
                print("error")
                pass
        alone_elements = tree.xpath(f"//{node}[preceding-sibling::node()[1][self::{previous_sibling}]]",
                                    namespaces=ns_decl)
        if len(alone_elements) == 0:
            tables_outside_div = False


def serialize_tree_to_file(tree, path):
    with open(path, "w") as output_file:
        output_file.write(ET.tostring(tree, pretty_print=True).decode('utf-8'))
    print(f"firefox {path}")


def validate(file):
    relaxng_doc = ET.parse("tei_all.rng")
    relaxng = ET.RelaxNG(relaxng_doc)
    doc = ET.parse(file)
    return relaxng.validate(doc)

    with open(f"../../data/to_tei/{dir_name}/{lesson_name}.xml", "w") as output_file:
        # TODO: single asterisks are not rendered and break the HTML. After ET recovery, they are lost. I suppose the same
        # TODO: happens with other chars. It's annoying.
        # TODO: Another problem with regexp lesson: last urls disapear.
        # TODO: linebreaks in code are removed by lxml. 
        output_file.write(ET.tostring(lesson_as_xml_tree, pretty_print=True).decode('utf-8'))


def link_lessons(lesson):
    """
    This function parses all the trees and links the original lessons and translations. It adds the information 
    to the teiHeader
    :return: None
    """
    glob_expression = f"../../data/to_tei/*/{lesson}.xml"
    glob_expression = glob.glob(glob_expression)
    glob_expression = [item for item in glob_expression if "introduccion-a-tei-1" not in item]
    glob_expression = [item for item in glob_expression if "introducao-codificacao-textos-tei-1" not in item]
    print("Linking lessons")
    tei_ns = "http://www.tei-c.org/ns/1.0"
    ns_decl = {"tei": tei_ns}
    # All_lessons is a dict with all the correspondance. It is used to link the lessons in each tei file, 
    # and to create a global TEI file

    all_lessons = dict()
    for lesson in glob_expression:
        print(lesson)
        as_tree = ET.parse(lesson)
        id = as_tree.xpath("@xml:id", namespaces=ns_decl)[0]
        print(id)
        if len(as_tree.xpath("//tei:sourceDesc/descendant::tei:ref[@type='original_file']",
                             namespaces=ns_decl)) == 0:
            all_lessons[id] = []

    for lesson in glob_expression:
        as_tree = ET.parse(lesson)
        id = as_tree.xpath("@xml:id", namespaces=ns_decl)[0]
        if len(as_tree.xpath("//tei:sourceDesc/descendant::tei:ref[@type='original_file']",
                             namespaces=ns_decl)) != 0:
            corresp = \
                as_tree.xpath("//tei:sourceDesc/descendant::tei:ref[@type='original_file']/@target",
                              namespaces=ns_decl)[0]
            corresp = corresp.replace("#", "")
            try:
                all_lessons[corresp].append(id)
            except KeyError:
                all_lessons[corresp] = [id]

    for lesson in glob_expression:
        as_tree = ET.parse(lesson)
        id = as_tree.xpath("@xml:id", namespaces=ns_decl)[0]
        # Si il s'agit d'une leçon originale.
        source_desc_p = as_tree.xpath("//tei:sourceDesc/tei:p", namespaces=ns_decl)[0]
        if id in all_lessons and all_lessons[id] != []:
            refs = " ".join(f"#{element}" for element in all_lessons[id])
            source_desc_p.text = f"{source_desc_p.text} Available translations are the following:"
            ref_element = ET.Element("ref")
            ref_element.set("type", "translations")
            ref_element.set("target", refs)
            source_desc_p.append(ref_element)
        else:
            if any([id in translated for translated in all_lessons.values() if translated != [id]]):
                source_desc = as_tree.xpath("//tei:sourceDesc", namespaces=ns_decl)[0]
                new_p = ET.Element("p")
                correct_index = [index for index, translated in enumerate(all_lessons.values()) if id in translated][0]
                corresponding_lessons = " ".join(
                    [f"#{element}" for element in list(all_lessons.values())[correct_index] if element != id])
                new_ref = ET.Element("ref")
                new_ref.set("target", corresponding_lessons)
                new_p.text = "There are other translations: "
                new_p.append(new_ref)
                source_desc.append(new_p)

        # Let's serialize the tree.

        # valid = validate(lesson)
        valid = True
        if valid:
            ET.indent(as_tree, space="    ")
            print(lesson)
            print(valid)
            try:
                os.mkdir(f"../../data/to_tei/{lesson.split('/')[4]}")
            except FileExistsError:
                pass
            with open(lesson, "w") as output_file:
                output_file.write(ET.tostring(as_tree, pretty_print=True, encoding='utf8').decode('utf8'))

    return all_lessons


def create_main_tei_file(lessons: dict) -> None:
    """
    This function creates the main TEI document, linking to the other documents with xi:include elements
    :param lessons:  The lessons to parse
    :return:  None
    """
    Incomplete_TEI = """
    <TEI xmlns="http://www.tei-c.org/ns/1.0" xmlns:xi="http://www.w3.org/2001/XInclude">
      <teiHeader>
          <fileDesc>
             <titleStmt>
                <title>Title</title>
             </titleStmt>
             <publicationStmt>
                <p>Publication information</p>        
             </publicationStmt>
             <sourceDesc>
                <p>Information about the source</p>
             </sourceDesc>
          </fileDesc>
      </teiHeader>
    </TEI>
    """

    tei_tree = ET.fromstring(Incomplete_TEI)
    root = tei_tree
    for orig, translations in lessons.items():
        corresp_tree = ET.parse(f"../../data/to_tei/{orig}/{orig}.xml")
        new_tree = corresp_tree.getroot()
        all_tests = []
        test_expression = "//tei:head[preceding-sibling::node()[not(self::text())]] | //tei:h2 | //tei:h3 | //tei:h4 | " \
                          "//tei:h5 | //tei:h6 | //tei:h7"
        html_heads_test = new_tree.xpath(test_expression, namespaces=ns_decl)
        all_tests.extend(html_heads_test)
        new_TEI_node = ET.fromstring(Incomplete_TEI)
        if len(html_heads_test) == 0:
            include = ET.Element("{http://www.w3.org/2001/XInclude}include")
            include.set('href', f"{orig}/{orig}.xml")
            new_TEI_node.append(include)
        else:
            print("Error")
        for element in translations:
            corresp_tree = ET.parse(f"../../data/to_tei/{element}/{element}.xml")
            print(corresp_tree)
            html_heads_test_2 = corresp_tree.xpath(test_expression, namespaces=ns_decl)
            all_tests.extend(html_heads_test_2)
            if len(html_heads_test_2) == 0:
                print("Including file to corpus")
                include = ET.Element("{http://www.w3.org/2001/XInclude}include")
                include.set('href', f"{element}/{element}.xml")
                new_TEI_node.append(include)
            else:
                print("File not valid, excluding it from main TEI file.")
        # If there is at least one correct lesson, append the TEI subfile to the main corpus.
        print(all_tests)
        if len(all_tests) == 0:
            print("Appending tei Node")
            print(new_TEI_node)
            root.append(new_TEI_node)

    with open("../../data/to_tei/main.xml", "w") as output_file:
        output_file.write(ET.tostring(tei_tree, pretty_print=True, encoding='utf8').decode('utf8'))


if __name__ == '__main__':
    # Let's select the lessons in all languages
    target_lesson = "analise-sentimento-R-syuzhet"
    target_lesson = "intro-to-linked-data"
    target_lesson = "corpus-analysis-with-spacy"
    target_lesson = "interactive-visualization-with-plotly"
    target_lesson = "ocr-with-google-vision-and-tesseract"
    target_lesson = "introduccion-map-warper"
    target_lesson = "*"
    regexp = rf"/home/mgl/Bureau/Travail/PH/jekyll/(es|fr|en|pt)/l[^/]*/[^/]*\.md"
    lessons = [f for f in glob.glob(f"/home/mgl/Bureau/Travail/PH/jekyll/*/l*/{target_lesson}.md") if
               re.search(regexp, f)]
    # Those two lessons break the script because of tei elements they have.
    lessons = [lesson for lesson in lessons if
               lesson != "/home/mgl/Bureau/Travail/PH/jekyll/es/lecciones/introduccion-a-tei-1.md"]
    lessons = [lesson for lesson in lessons if lesson != "/home/mgl/Bureau/Travail/PH/jekyll/pt/licoes/introducao" \
                                                         "-codificacao-textos-tei-1.md"]

    # Removing log file
    try:
        os.remove("logs/log.txt")
    except FileNotFoundError:
        pass
    for lesson in lessons:
        print(lesson)
        xmlify(lesson)

    lessons = link_lessons(target_lesson)
    create_main_tei_file(lessons)
