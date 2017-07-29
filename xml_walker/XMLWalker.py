import uuid
from collections import defaultdict
from lxml import etree

from xml_walker.NodeInterest import Interest, InterestPathTree
from xml_walker.XMLNode import AutoMergeInterestNode


class FastXMLCallbackWalker:
    def __init__(self):
        from xml_walker.NodeInterest import InterestPathTree
        self._absolute_interest_tree = InterestPathTree()  # self.vr(None)
        self._relative_interests_trees = {}  # AutoMergeNode("RelativeInterestTreeRoot")
        self.current_absolute_node_chain_depth = 0
        self.event_callback_start = []
        self.event_callback_end = []
        self.user_space = {}
        self.exact_interests_dict = defaultdict(list)

        # exact path generator
        self.levels = defaultdict(lambda: -1)
        self._exact_xpath_str = ""

        self.register_event_callback("start", self.default_start_callbacks)

        self.register_event_callback("end", self.default_end_callbacks)

    @property
    def exact_path(self):
        return self._exact_xpath_str

    # def vr(self, node):
    #    return NamedForestNode('VirtualRoot', None, node)

    def build_chain(self, interest):
        import re
        res = interest.interest
        for match in re.findall("{.*?}[^/^$]*", interest.interest):
            res = res.replace(match, match.replace("/", "#"))
        node = None
        res = [x for x in res.split("/") if x]
        for e in res[:-1]:
            node = AutoMergeInterestNode(e.replace("#", "/"), parent=node)
        # only execute callbacks at leaf node
        node = AutoMergeInterestNode(res[-1].replace("#", "/"), parent=node, interest=interest)

        return node.root
        # res = interest.split("/")
        # chain = [x for x in res if x]
        # node = []
        # for chain_elem in reversed(chain):
        #    if callback:
        #        node = NamedForestNode(chain_elem, [callback], node)
        #        callback = None
        #    else:
        #        node = NamedForestNode(chain_elem, None, {node.name: node})
        # return self.vr({node.name: node})

    def _register_absolute_interest(self, interest):
        chain = self.build_chain(interest)
        chain.parent = self._absolute_interest_tree.interest_tree
        # self.interest_tree.merge_tree(chain)

    def _register_exact_interest(self, interest):
        self.exact_interests_dict[interest.interest].append(interest)

    def _register_relative_interest(self, interest):
        _uuid = uuid.uuid4()
        reset_interest = Interest('ResetInterest_%s' % _uuid, lambda **x: self.reset_relative_tree(_uuid, **x),
                                  event='end')
        chain = self.build_chain(interest)
        self._relative_interests_trees[_uuid] = InterestPathTree()
        chain.parent = self._relative_interests_trees[_uuid].interest_tree
        self._relative_interests_trees[_uuid].interest_tree.interests.append(reset_interest)
        return _uuid
        # self.interest_tree.merge_tree(chain)

    def register_interest(self, interest):
        if interest.interest.startswith("/*"):
            self._register_exact_interest(interest)
        else:
            if interest.interest.startswith("//"):
                _uuid = self._register_relative_interest(interest)
                self._relative_interests_trees[_uuid].interest_tree.clean_garbage()
            else:
                if interest.interest.startswith("/"):
                    self._register_absolute_interest(interest)
                    self._absolute_interest_tree.interest_tree.clean_garbage()
                else:
                    raise Exception("Cannot handle your Expression %s!" % interest)

    def register_interests(self, interests):
        for interest in interests:
            self.register_interest(interest)

    def register_event_callback(self, event, callback):
        if event == "start":
            self.event_callback_start.append(callback)
        if event == "end":
            self.event_callback_end.append(callback)

    def remove_event_callback(self, event, callback):
        if event == "start":
            self.event_callback_start.remove(callback)
        if event == "end":
            self.event_callback_end.remove(callback)

    def has_event_callback(self, event, callback):
        if event == "start":
            return callback in self.event_callback_start
        if event == "end":
            return callback in self.event_callback_end


    @staticmethod
    def reset_relative_tree(TREEID, **kwargs):
        Logger.debug("Reset relative tree %s" % TREEID)
        walker = kwargs["walker"]
        walker.relative_interests_trees[TREEID].current_node = walker.relative_interests_trees[TREEID].current_node.root
        walker.relative_interests_trees[TREEID].current_tree_depth = 0

    def check_exact_match(self, event, exact_xpath, kwargs):
        if exact_xpath in self.exact_interests_dict:
            interests = [x for x in self.exact_interests_dict[exact_xpath] if x.event == event]
            for interest in interests:
                for callback in interest.callbacks:
                    kwargs_tmp = kwargs
                    kwargs_tmp["interest"] = interest
                    callback(**kwargs_tmp)

    @staticmethod
    def default_start_callbacks(**kwargs):
        walker = kwargs["walker"]
        element = kwargs["element"]

        # exact node name calc start
        walker.levels[walker.current_absolute_node_chain_depth] += 1
        walker._exact_xpath_str += "/*[%s]" % (
            walker.levels[walker.current_absolute_node_chain_depth])

        walker._absolute_interest_tree.node_start(element=element, mode="absolute",
                                                  document_depth=walker.current_absolute_node_chain_depth, kwargs=kwargs)

        # check relative interests
        for _uuid in walker._relative_interests_trees:
            walker._relative_interests_trees[_uuid].node_start(element=element, mode="relative",
                                                              document_depth=walker.current_absolute_node_chain_depth,
                                                              kwargs=kwargs)
        # check exact interests
        walker.check_exact_match(event="start", exact_xpath=walker._exact_xpath_str, kwargs=kwargs)

        # update node depth
        walker.current_absolute_node_chain_depth += 1

    @staticmethod
    def default_end_callbacks(**kwargs):
        walker = kwargs["walker"]
        element = kwargs["element"]

        walker._absolute_interest_tree.node_end(element=element, mode="absolute",
                                                document_depth=walker.current_absolute_node_chain_depth, kwargs=kwargs)

        # check relative interests
        for _uuid in walker._relative_interests_trees:
            walker._relative_interests_trees[_uuid].node_end(element=element, mode="relative",
                                                            document_depth=walker.current_absolute_node_chain_depth,
                                                            kwargs=kwargs)
        # check exact interests
        walker.check_exact_match(event="end", exact_xpath=walker._exact_xpath_str, kwargs=kwargs)

        # exact node name calc end
        walker._exact_xpath_str = walker._exact_xpath_str.rsplit('/', 1)[0]

        # update node depth
        walker.current_absolute_node_chain_depth -= 1

    def walk_tree(self, file_path):
        for event, element in etree.iterparse(file_path, events=("start", "end")):
            if event == "start":
                for callback in self.event_callback_start:
                    callback(event=event, element=element, walker=self)
            if event == "end":
                for callback in self.event_callback_end:
                    callback(event=event, element=element, walker=self)
                element.clear()
