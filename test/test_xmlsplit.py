from collections import namedtuple
# set value (if needed)
from xml_walker import XMLWriter


#s = GenIF2Splitter()
#s.search_genif2()

s = XMLWriter.XMLWriter()
s.split("../relation_genif2.xml")
