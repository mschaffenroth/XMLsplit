def nice_start_tag(element):
    ret = [element.tag.replace("{%s}" % element.nsmap[ns], "%s:" % ns) if ns else element.tag.replace(
        "{%s}" % element.nsmap[ns], '') for ns in element.nsmap if element.nsmap[ns] in element.tag]
    nice_tag = "<%s%s>" % (ret[0] if ret else element.tag, " ".join(["%s=\"%s\"" %  (x,y) for x,y in element.attrib]) if element.attrib else "")
    return nice_tag

def nice_end_tag(element):
    #ret = [element.tag.replace("{%s}" % element.nsmap[ns], "%s:" % ns) if ns else element.tag.replace(
    #    "{%s}" % element.nsmap[ns], '') for ns in element.nsmap if element.nsmap[ns] in element.tag]
    ret = [element.tag.split("}")[-1]]
    nice_tag = "</%s>" % ret[0] if ret else element.tag
    return nice_tag


# provide all the informations to write the element into a file
class XMLNode:
    def __init__(self, element, wanted_in_files):
        self.wanted_in_files = wanted_in_files # mark when we want to write it into a file
        self.written_in_files = [] # mark when started to write in file (start tag)
        self.start_tag = nice_start_tag(element)
        self.end_tag = nice_end_tag(element)
        self.element = element

    def update(self, element):
        self.tail = element.tail


class AutoMergeInterestNode(XMLNode):
    # FExt
    def _pre_detach(self, parent):
        if not self in self.garbage:
            del parent.children_names[self.name]
        print("_pre_detach", parent)

        # def _post_detach(self, parent):
        # print("_post_detach", parent)

    garbage = set()

    def __init__(self, name, parent=None, interest=None, **kwargs):
        super(AutoMergeInterestNode, self).__init__(name, parent, **kwargs)
        # FExt
        self.children_names = {}
        self.interests = []
        if interest:
            self.interests.append(interest)
        self.attributes = {}

    def merge_node(self, node):
        children_to_move = {k: v for k, v in node.children_names.items() if k not in self.children_names}
        for child in children_to_move:
            children_to_move[child].parent = self
        children_to_merge = {k: v for k, v in node.children_names.items() if k in self.children_names}
        for child in children_to_merge:
            self.children_names[child].merge_node(children_to_merge[child])
        self.interests.extend(node.interests)

    @classmethod
    def clean_garbage(cls):
        for item in cls.garbage:
            item.parent = None

    def _pre_attach(self, parent):

        #        #old
        #        same_name = [x for x in parent.children if x.name == self.name]
        #
        #        if same_name:
        #            #old
        #            C = {c.name: c for c in self.children}
        #            E = {c.name: c for c in same_name[0].children}
        #            D = {k: v for k, v in C.items() if k not in E}
        #            for child in D:
        #                D[child].parent = same_name[0]
        #            self.garbage.append(self)


        # FExt
        same_name = parent.children_names[self.name] if self.name in parent.children_names else []
        if same_name:
            same_name.merge_node(self)
            self.garbage.add(self)
        else:
            if not self.name.startswith("@"):
                parent.children_names[self.name] = self
            else:
                parent.attributes[self.name] = self

                #
                # self.parent = None

                # print("_pre_attach", parent)

                # def _post_attach(self, parent):
                # print("_post_attach", parent)
