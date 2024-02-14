# Data

You'll find here two kind of data:
1) In `lessons` dir,  The whole dataset (all PH lessons in all language) converted to TEI-like XML (TODO: manage 
   `teiHeader`).
2) In `struct_aligned`, the 10-20 lessons that could be structurally aligned AND that were translated to french (to 
   start). 
   I had to modify the structure for some of them, and to change some heading levels in the original md files
   (in another branch). The lessons with translations that added or removed divisions were ignored.
   
In the last set of files, each division is identified with an ID that corresponds to its position in the tree:
`1.2`, `2.4.1`, etc. Each lesson should have the same ids, and normally an id should correspond to the same division and 
text in the different linguistic versions of a lesson.

This was the easy part. What sould we do with lessons that show some structural modification ? Get rid of structure and 
work on text data only ?

**TODO**: include lessons without french version. 