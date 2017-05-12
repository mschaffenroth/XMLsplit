from collections import namedtuple
# set value (if needed)
from xml_walker.XMLWriter import XMLWriter

delayed_element = namedtuple("delayed_element", ["files", "element", "part"])

#s = GenIF2Splitter()
#s.search_genif2()

s = XMLWriter()
s.split("C:\\Users\\mschaffe\\PycharmProjects\\NewXMLsplit\\relation_genif2.xml")
