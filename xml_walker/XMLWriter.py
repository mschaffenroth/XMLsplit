from collections import namedtuple

from xml_walker.FileSupport import Files
from xml_walker.Logger import Logger
from xml_walker.XMLNode import XMLHelper
from xml_walker.XMLWalker import FastXMLCallbackWalker


class XMLWriter(FastXMLCallbackWalker):

    delayed_element = namedtuple("delayed_element", ["files", "element", "part"])

    def __init__(self):
        self.path_to_files = {}
        self.delay_element_parts = []
        from collections import defaultdict
        self.node_written = defaultdict(set)
        self.node_start_counter = 0
        self.node_stack = []
        self.files = Files()
        super(XMLWriter, self).__init__()
        if not self.has_event_callback('start', self._node_start):
            self.register_event_callback('start', self._node_start)
        if not self.has_event_callback('end', self._node_end):
            self.register_event_callback('end', self._node_end)

    def _node_start(self, walker, element, **kwargs):
        # write tags or content (writing is delayed so that we do not try to write anything that has not been parsed yet!)
        self.write_delayed_element_parts()
        exact_path = walker.exact_path
        parent_xpath = exact_path.rsplit("/", 1)[0]
        element = element
        Logger.debug("write_node_start: element %s" % element)

        self.node_stack.append(element)

        Logger.debug("write_node_start node_stack: %s" % self.node_stack)
        element_wanted_in_files = set()
        #for i in range(len(self.node_stack)):
        for i in range(self.exact_path.count('/')):
            if exact_path in self.path_to_files:
                element_wanted_in_files |= self.path_to_files[exact_path]
            exact_path = exact_path.rsplit("/", 1)[0]

        self.path_to_files[parent_xpath] = element_wanted_in_files
        if element_wanted_in_files:
            for elem in self.node_stack:
                element_to_files = element_wanted_in_files - \
                                   (self.node_written[elem] if elem in self.node_written else set())
                if element_to_files:
                    self.write_start_tag(element_to_files, elem)
                    self.write_text(element_to_files, elem)
                    self.node_written[elem] |= element_to_files

    def _node_end(self, **kwargs):
        self.write_delayed_element_parts()
        element = kwargs['element']
        exact_path = kwargs['walker'].exact_path
        Logger.debug("write_node_end: element %s" % element)

        if self.node_written[element]:
            self.write_end_tag(self.node_written[element], element)
            self.write_tail(self.node_written[element], element)

        self.node_stack.pop()
        if element in self.node_written:
            del self.node_written[element]
        if exact_path in self.path_to_files:
            del self.path_to_files[exact_path]

    def post_actions(self):
        self.write_delayed_element_parts()

    def split(self, source_file, target_file_pattern, paths_to_files):
        '''
        function that saves selected parts of a xml file into different files 
        :param source_file: original xml file
        :param target_file_pattern:  patter of the target files. The target files will be named as following: <target_file_pattern><filenumber>.xml
        :param paths_to_files: list of paths that select a part of the original document and the filenumbers where they will be saved 
        :return: list of paths to splitted files
        '''
        self.path_to_files = paths_to_files
        # assert that input is a list of file numbers
        for path in paths_to_files:
            assert isinstance(paths_to_files[path], set)
            for filenum in paths_to_files[path]:
                assert isinstance(filenum, int)

        # filenum to full file path
        for path in paths_to_files:
            paths_to_files[path] = set(["%s.%s.xml" % (target_file_pattern, x) for x in paths_to_files[path]])

        # self.register_write_nodes([x for x in self.path_to_files])
        self.walk_tree(file_path=source_file)
        self.post_actions()
        self.close()
        Logger.info("splitting %s completed" % source_file)
        return self.path_to_files

    def write_delayed_element_parts(self):
        """
        Write delayed element parts

        This function writes parts of an xml element (e.g. text, starttag, endtag) to an output document.
        To ensure that no element get written before being parsed the write process is delayed for one element.
        :return: None
        """
        for delay_element_part in self.delay_element_parts:
            if delay_element_part.part == "start_tag":
                for file in delay_element_part.files:
                    self.files[file].write(XMLHelper.nice_start_tag(delay_element_part.element))

            if delay_element_part.part == "end_tag":
                for file in delay_element_part.files:
                    self.files[file].write(XMLHelper.nice_end_tag(delay_element_part.element))

            if delay_element_part.part == "text":
                for file in delay_element_part.files:
                    if delay_element_part.element.text:
                        self.files[file].write(delay_element_part.element.text)

            if delay_element_part.part == "tail":
                for file in delay_element_part.files:
                    if delay_element_part.element.tail:
                        self.files[file].write(delay_element_part.element.tail)
        self.delay_element_parts = []

    def write_start_tag(self, files, element):
        """
        Write start tag

        :param files: Target files where this start tag should be written into
        :param element: LXML element that should be written
        :return: None
        """
        Logger.debug("write_start_tag %s" % element)
        self.delay_element_parts.append(self.delayed_element(files=files, element=element, part="start_tag"))

    def write_end_tag(self, files, element):
        """
        Write end tag

        :param files: Target files where this end tag should be written into
        :param element: LXML element that should be written
        :return: None
        """
        Logger.debug("write_end_tag %s" % element)
        self.delay_element_parts.append(self.delayed_element(files=files, element=element, part="end_tag"))

    def write_text(self, files, element):
        """
        Write text of element

        :param files: Target files where this text should be written into
        :param element: LXML element that should be written
        :return: None
        """
        self.delay_element_parts.append(self.delayed_element(files=files, element=element, part="text"))

    def write_tail(self, files, element):
        """
        Write tail of element

        :param files: Target files where the tail should be written into
        :param element: LXML element that should be written
        :return: None
        """
        self.delay_element_parts.append(self.delayed_element(files=files, element=element, part="tail"))

    def close(self):
        self.files.close()
