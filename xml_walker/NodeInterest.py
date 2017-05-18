from xml_walker.XMLNode import AutoMergeInterestNode


class Interest:
    def __init__(self, interest, callback, event='start'):
        self.interest = interest
        self.callbacks = [callback]
        self.event = event


class NodeDistributionInterest(Interest):
    def __init__(self, interest, target_file, callback, event='start'):
        super(NodeDistributionInterest, self).__init__(interest, callback, event)
        self.target_file = target_file

class InterestPathTree:
    def __init__(self):
        self.current_tree_depth = 0
        self.interest_tree = AutoMergeInterestNode("InterestTreeRoot")
        self.current_node = self.interest_tree

    def check_node_attributes_for_callback_execution(self, event, element, kwargs):
        if self.current_node.attributes:
            found_attributes = [x for x in self.current_node.attributes if x[1:] in element.attrib]
            for attrib in found_attributes:
                interests = [x for x in self.current_node.attributes[attrib].interests if x.event == event]
                for interest in interests:
                    for callback in interest.callbacks:
                        kwargs_tmp = kwargs
                        kwargs_tmp["interest"] = interest
                        callback(**kwargs_tmp)

    def check_node_for_callback_execution(self, event, element, kwargs):
        interests = [x for x in self.current_node.interests if x.event == event]
        for interest in interests:
            for callback in interest.callbacks:
                kwargs_tmp = kwargs
                kwargs_tmp["interest"] = interest
                callback(**kwargs_tmp)

    def node_start(self, element, kwargs, document_depth, mode='absolute'):
        current_tree_depth_check = self.current_tree_depth
        if mode == 'relative' and not self.current_tree_depth:
            current_tree_depth_check = document_depth
        if current_tree_depth_check == document_depth:
            if self.current_tree_depth == 0:
                self.check_node_attributes_for_callback_execution(element=element, event="start", kwargs=kwargs)
                self.check_node_for_callback_execution(element=element, event="start", kwargs=kwargs)

            if self.current_node.children_names and element.tag in self.current_node.children_names:
                if mode == "relative" and not self.current_tree_depth:
                    self.current_tree_depth = document_depth
                self.current_tree_depth += 1
                self.current_node = self.current_node.children_names[element.tag]
                self.check_node_attributes_for_callback_execution(element=element, event="start", kwargs=kwargs)
                self.check_node_for_callback_execution(element=element, event="start", kwargs=kwargs)

    def node_end(self, element, document_depth, kwargs, mode='absolute'):
        current_tree_depth_check = self.current_tree_depth
        # if mode == 'relative' and not self.current_tree_depth:
        #    current_tree_depth_check = document_depth

        if current_tree_depth_check == document_depth:
            if self.current_node.name == element.tag:
                self.check_node_for_callback_execution(element=element, event="end", kwargs=kwargs)
                self.current_tree_depth -= 1
                self.current_node = self.current_node.parent
