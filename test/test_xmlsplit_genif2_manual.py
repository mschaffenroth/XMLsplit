import os
from collections import defaultdict
# set value (if needed)
from test.testfile_generator import gen_genif2
from xml_splitter.xmlsplit import GenIF2Splitter
from xml_walker.XMLWriter import XMLWriter

split_file = "../relation_genif2.xml"
split_file = "../out/genif2_generated.xml"

nodes = 500000
start_id = 1000000
item_restriction = 100000
gen_genif2(split_file, start_id, start_id + nodes)

s = GenIF2Splitter()
bags = s.search_genif2(split_file, [
                ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item", item_restriction),
                ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}asset", 200),
            ]
)
s.clear()
# distribute bags to files
paths_to_files = defaultdict(set)
for i, bag in enumerate(bags):
    for bag_entry in bag:
        for set_entry in bag_entry:
            paths_to_files[set_entry].add(i)
xmlwriter = XMLWriter()
xmlwriter.split(split_file, "../out/%s.out" % os.path.basename(split_file), paths_to_files)

#s = XMLWriter.XMLWriter()
#s.split("../relation_genif2.xml", "../out/out", {"/*[0]/*[0]/*[0]/*[0]": {1}, "/*[0]/*[0]/*[0]/*[1]": {1,2}})
