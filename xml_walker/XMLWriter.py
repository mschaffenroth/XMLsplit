class XMLWriter(FastXMLCallbackWalker):
    def __init__(self):
        self.xpath2files = {}
        self.delay_element_parts = []
        self.node_written = defaultdict(set)
        self.node_start_counter = 0
        self.node_stack = []
        self.files = Files()
        super(XMLWriter, self).__init__()

    def _write_node_start(self, **kwargs):
        self.write_delayed_element_parts()
        exact_path = kwargs['walker'].exact_path
        element = kwargs['element']

        if not self.node_stack:
            tmp_stack = []
            parent = element.getparent()
            while parent is not None:
                tmp_stack.append(parent)
                parent = parent.getparent()
            self.node_stack.extend(reversed(tmp_stack))
        self.node_stack.append(element)

        element_wanted_in_files = set()
        #for i in range(len(stack)):
        #    exact_path = exact_path.rsplit("/", 1)[0]
        #    if exact_path in self.xpath2files:
        #        element_wanted_in_files |= self.xpath2files[exact_path]
        parent_xpath = exact_path.rsplit("/", 1)[0]
        element_wanted_in_files = (self.xpath2files[exact_path] if exact_path in self.xpath2files else set()) | \
                                  (self.xpath2files[parent_xpath] if parent_xpath in self.xpath2files else set())
        self.xpath2files[parent_xpath] = element_wanted_in_files
        if element_wanted_in_files:
            for elem in self.node_stack:
                element_to_files = element_wanted_in_files - \
                                   (self.node_written[elem] if elem in self.node_written else set())
                if element_to_files:
                    self.write_start_tag(element_to_files, elem)
                    self.write_text(element_to_files, elem)
                    self.node_written[elem] |= element_to_files

    def _write_node_end(self, **kwargs):
        self.write_delayed_element_parts()
        element = kwargs['element']
        exact_path = kwargs['walker'].exact_path

        for elem in reversed(self.node_stack):
            elem_to_files = self.node_written[elem] if elem in self.node_written else set()
            if elem_to_files:
                self.write_end_tag(elem_to_files, elem)
                self.write_tail(elem_to_files, elem)

        self.node_stack.pop()
        del self.node_written[element]
        del self.xpath2files[exact_path]



    def write_node_start(self, **kwargs):
        self.node_start_counter += 1
        if self.node_start_counter == 1:
            assert not self.has_event_callback('start', self._write_node_start)
            assert not self.has_event_callback('end', self._write_node_end)
            self.register_event_callback('start', self._write_node_start)
            self.register_event_callback('end', self._write_node_end)
        if self.node_start_counter > 1:
            assert self.has_event_callback('start', self._write_node_start)
            assert self.has_event_callback('end', self._write_node_end)

    def write_node_end(self, **kwargs):
        self.node_start_counter -= 1
        if self.node_start_counter == 0:
            self._write_node_end(**kwargs)
            self.remove_event_callback('start', self._write_node_start)
            self.remove_event_callback('end', self._write_node_end)
            self.node_stack = []

    def register_write_nodes(self, xpaths):
        for xpath in xpaths:
            self.register_write_node(xpath)

    def register_write_node(self, xpath):
        self.register_interest(Interest(xpath, self.write_node_start, event='start'))
        self.register_interest(Interest(xpath, self.write_node_end, event='end'))

    def post_actions(self):
        self.write_delayed_element_parts()

    def split(self, file):
        #f = open(, "w")
        f = "1.xml"
        self.xpath2files["/*[0]/*[0]/*[0]/*[0]"] = set([f])
        self.xpath2files["/*[0]/*[0]/*[0]/*[1]"] = set([f])
        self.register_write_nodes([x for x in self.xpath2files])
        self.walk_tree(file_path=file)
        self.post_actions()

    def write_delayed_element_parts(self):
        for delay_element_part in self.delay_element_parts:
            if delay_element_part.part == "start_tag":
                for file in delay_element_part.files:
                    self.files[file].write(Helper.nice_start_tag(delay_element_part.element))

            if delay_element_part.part == "end_tag":
                for file in delay_element_part.files:
                    self.files[file].write(Helper.nice_end_tag(delay_element_part.element))

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
        self.delay_element_parts.append(delayed_element(files=files, element=element, part="start_tag"))

    def write_end_tag(self, files, element):
        self.delay_element_parts.append(delayed_element(files=files, element=element, part="end_tag"))

    def write_text(self, files, element):
        self.delay_element_parts.append(delayed_element(files=files, element=element, part="text"))

    def write_tail(self, files, element):
        self.delay_element_parts.append(delayed_element(files=files, element=element, part="tail"))
