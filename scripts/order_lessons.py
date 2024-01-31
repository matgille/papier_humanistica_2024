import csv

out_list = []

with open("../donnees/aligned_ordered.csv", 'w') as output_file:
    output_file.write("Anglais,Espagnol,Français,Portugais\n")
    with open("../donnees/aligned_lessons.tsv", "r") as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t')
        for row in spamreader:
            row.sort()
            print(row)
            en = sorted([element if "/en/" in element else "" for element in row], reverse=True)[0]
            print(en)
            es = sorted([element if "/es/" in element else "" for element in row], reverse=True)[0]
            print(es)
            fr = sorted([element if "/fr/" in element else "" for element in row], reverse=True)[0]   
            pt = sorted([element if "/pt/" in element else "" for element in row], reverse=True)[0]       
            print(",".join([en, es, fr, pt]) + "\n")
            output_file.write(",".join([en, es, fr, pt]) + "\n")

