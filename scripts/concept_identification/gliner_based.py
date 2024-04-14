import tqdm
from gliner import GLiNER
import glob
import sys
model = GLiNER.from_pretrained("urchade/gliner_base")

labels = ["technical term"]
# f"/home/mgl/Bureau/Travail/PH/jekyll/{lang}/*/*.md"
files = glob.glob(sys.argv[1])
concat_lessons = ""
entities = []
print(files)
for file in tqdm.tqdm(files):
    with open(file, "r") as indiv_file:
        lesson = indiv_file.read()
    try:
        identified_ents = model.predict_entities(lesson, labels, threshold=0.5)
    except  IndexError:
        continue
    for entity in identified_ents:
        entities.append(entity["text"])

    print(list(set(entities)))
    print(len(list(set(entities))))