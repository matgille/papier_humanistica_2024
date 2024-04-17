import lxml.etree as ET
import tqdm
from bs4 import BeautifulSoup
import sys
import re


def prettify(file: str):
    bs = BeautifulSoup(open(file), 'xml')
    pretty_xml = bs.prettify()
    opening_pattern = re.compile(r"<(pc|w)>\s+")
    closing_pattern = re.compile(r"\s+<\/(pc|w)>")
    pretty_xml = re.sub(opening_pattern, r"<\1>", pretty_xml)
    pretty_xml = re.sub(closing_pattern, r"</\1>", pretty_xml)
    with open(file, "w") as output_clean:
        output_clean.write(pretty_xml)


if __name__ == '__main__':
    all_files = sys.argv[1:]
    for file in tqdm.tqdm(all_files):
        prettify(file)
