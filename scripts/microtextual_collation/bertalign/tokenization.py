import subprocess
from lxml import etree
import re
import sys
import bertalign.utils as utils
from itertools import groupby
from operator import itemgetter


class Tokenizer:
    def __init__(self, nodes_to_reinject: dict = {}, temoin_leader: str = "Sal_J",
                 regularisation: bool = True):
        self.temoin_leader = temoin_leader
        self.nodes_to_reinject = nodes_to_reinject
        self.tei_ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        self.namespace = 'http://www.tei-c.org/ns/1.0'
        self.tei = '{%s}' % self.namespace
        self.NSMAP0 = {None: self.namespace}
        self.regularisation = regularisation
        self.saxon = "saxon9he.jar"
        self.tokenized_tree = None

    def ajout_xml_id(self, temoin: str):
        """Ajout de xml:id à chaque token."""
        f = etree.parse(temoin)
        root = f.getroot()
        liste_elements_vides = root.xpath("//tei:*[not(child::node())][not(@xml:id)]", namespaces=self.tei_ns)
        for element in liste_elements_vides:
            element.set("{http://www.w3.org/XML/1998/namespace}id", utils.generateur_id())

        # On inclut les tei:pc pour faciliter le debuggage
        token_list = root.xpath("//node()[self::tei:w or self::tei:pc]", namespaces=self.tei_ns)
        for token in token_list:
            token.set("{http://www.w3.org/XML/1998/namespace}id", utils.generateur_id())


        with open(temoin, "w+") as sortie_xml:
            tree_as_string = etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True).decode(
                'utf8')
            sortie_xml.write(str(tree_as_string))
    
    def punctuation_tokenisation(self, tree):
        for division in tree.xpath("descendant::tei:div[@type='chapitre']/descendant::node()[self::tei:head or self::tei:p]", namespaces=self.tei_ns):
            tokens = division.xpath("descendant::node()[self::tei:pc or self::tei:w]", namespaces=self.tei_ns)
            punctuation_indices = [index for index, token in enumerate(tokens) if etree.QName(token).localname == 'pc']
    
            
            
            # On va regrouper les pontuations adjacentes pour ne retenir que la dernière
            # https://stackoverflow.com/a/2361991 + les commentaires pour la mise à jour du code
            
            grouped_punctuation = []
            for k, g in groupby(enumerate(punctuation_indices), lambda ix : ix[0] - ix[1]):
                grouped_punctuation.append(tuple(map(itemgetter(1), g)))
            
            spans = [group[-1] for group in grouped_punctuation]
            print(spans)
            print(len(tokens))
            grouped_spans = []
            print(f"Punctuation indices: {punctuation_indices}")
            print(' '.join([token.text for token in tokens]))
            try:
                grouped_spans.append((0, spans[0] - 1))
                grouped_spans.extend([(position + 1, spans[index + 1]) if index != 0 else (position, spans[index + 1]) for index, position in enumerate(spans[:-1])])
                if len(tokens) != spans[-1] + 1:
                    grouped_spans.append((spans[-1] + 1, len(tokens)))
                print(grouped_spans)
                
                for word_group in grouped_spans:
                    # On crée l'élément cl
                    element_to_insert = etree.Element(self.tei + 'cl', nsmap=self.NSMAP0)
                    following_word = tokens[word_group[0]]
                    following_word.addprevious(element_to_insert)
                    # Maintenant on va intégrer les tei:w dans cet élément cl.
                    for tok in tokens[word_group[0]: word_group[1] + 1]:
                        element_to_insert.append(tok)
            except IndexError:
                pass
            
            if grouped_spans == [(0, -1)] or grouped_spans == []:
                element_to_insert = etree.Element(self.tei + 's', nsmap=self.NSMAP0)
                try:
                    following_word = tokens[0]
                except:
                    print("Error. Division:")
                    print(' '.join([token.text for token in tokens]))
                    print(division.xpath("ancestor::tei:div/@n", namespaces=self.tei_ns))
                    exit(0)
                following_word.addprevious(element_to_insert)
                for tok in tokens:
                    element_to_insert.append(tok)
                
        return tree
        
    
    def syntactic_tokenization(self, tree, delimiters, use_punctuation):
        print(delimiters)
        for clause in tree.xpath("//tei:cl", namespaces = self.tei_ns):
            xml_tokens = clause.xpath("descendant::node()[self::tei:pc or self::tei:w]", namespaces=self.tei_ns)
            tokens = " ".join([token.text for token in xml_tokens])
            delimiter = re.compile(delimiters)
            search = re.search(delimiter, tokens)
            if search:
                matches = re.finditer(delimiter, tokens)
                spaces = re.compile("\s")
                spaces_positions = re.finditer(spaces, tokens)
                print(tokens)
                print([match for match in matches])
                print([match.span() for match in spaces_positions])
                matches = re.finditer(delimiter, tokens)
                spaces_positions = re.finditer(spaces, tokens)
                word_positions = [0]
                element_to_insert = etree.Element(self.tei + 'phr', nsmap=self.NSMAP0)
                following_word = xml_tokens[0]
                following_word.addprevious(element_to_insert)
                for match in matches:
                    string_position = match.span()[0]
                    space_position = [index for index, position in enumerate(spaces_positions) if position.span()[0] == string_position][0]
                    spaces_positions = re.finditer(spaces, tokens)
                    word_position = space_position
                    word_positions.append(word_position)

                    element_to_insert = etree.Element(self.tei + 'phr', nsmap=self.NSMAP0)
                    following_word = xml_tokens[word_position]
                    following_word.addprevious(element_to_insert)
                word_positions.append(len(xml_tokens))
                print(word_positions)
                phrases = clause.xpath("descendant::tei:phr", namespaces=self.tei_ns)
                positions = [(position + 1, word_positions[index + 1]) if index != 0 else (position, word_positions[index + 1]) for index, position in enumerate(word_positions[:-1])]
                print(positions)
                for index, position in enumerate(positions):
                    min_pos, max_pos = position
                    phrases[index].extend(xml_tokens[min_pos:max_pos + 1])
            else:
                # Dans le cas où on ne trouve pas de délimiteur
                if len(clause) != 0:
                    element_to_insert = etree.Element(self.tei + 'phr', nsmap=self.NSMAP0)
                    following_word = xml_tokens[0]
                    following_word.addprevious(element_to_insert)
                    for token in xml_tokens:
                        element_to_insert.append(token)
    
        self.tokenized_tree = tree
    
    def subsentences_tokenisation(self, path:str, delimiters):
        tree = etree.parse(path)
        segmented_tree = self.punctuation_tokenisation(tree)
        self.syntactic_tokenization(segmented_tree, delimiters=delimiters)
        with open(f"{path.replace('.xml', '.phrased.xml')}", "w") as output_file:
            output_file.write(etree.tostring(self.tokenized_tree, pretty_print=True).decode())
    
    def tokenisation(self, path: str, punctuation_regex):
        """
        Tokénise le corpus
        :path: le chemin vers les fichiers d'entré
        :correction_mode: le mode correction
        :regularisation: produire un fichier régularisé ? Défaut: oui
        """
        print("Tokenizing")
        tokenized_file = path.replace('.xml', '.tokenized.xml')
        regularized_file = path.replace('.xml', '.regularized.xml')
        print(path)
        subprocess.run(["java", "-jar", self.saxon, "-xi:on", path,
                        "bertalign/xsl/tokenization.xsl", f"output_path={tokenized_file}", f"punctuation_regex={punctuation_regex}"])
        try:
            self.ajout_xml_id(f"{tokenized_file}")
        except etree.XMLSyntaxError:
            print(f"Error: please check {tokenized_file}")
        if self.regularisation:
            output_path = f"output_path={regularized_file}"
            subprocess.run(["java", "-jar", self.saxon, "-xi:on", tokenized_file,
                            "bertalign/xsl/regularisation.xsl", output_path])
        print("Tokénisation et régularisation du corpus pour alignement ✓")
        


if __name__ == '__main__':
    tokeniser = Tokenizer(regularisation=True)
    tokeniser.tokenisation(path=sys.argv[1])
