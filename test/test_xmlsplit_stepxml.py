import os
from collections import namedtuple, defaultdict
# set value (if needed)
from xml_splitter.xmlsplit import GenIF2Splitter, StepXMLsplitter
from xml_walker.XMLWriter import XMLWriter

split_file = "../small_example.xml"
s = StepXMLsplitter()
bags = s.search_stepxml(split_file)
# distribute bags to files
paths_to_files = defaultdict(set)
for i, bag in enumerate(bags):
    for bag_entry in bag:
        #for set_entry in bag_entry:
            paths_to_files[bag_entry].add(i)
xmlwriter = XMLWriter()
xmlwriter.split(split_file, "../out/%s.out" % os.path.basename(split_file), paths_to_files)

#s = XMLWriter.XMLWriter()
#s.split("../relation_genif2.xml", "../out/out", {"/*[0]/*[0]/*[0]/*[0]": {1}, "/*[0]/*[0]/*[0]/*[1]": {1,2}})
