from collections import defaultdict

from anytree import RenderTree

from xml_walker.Logger import Logger
from xml_walker.NodeInterest import Interest
from xml_walker.XMLWalker import FastXMLCallbackWalker


class StepXMLsplitter:
    """
    A XMLsplitter that splits the STEP-XML format by STIBO Systems

    Splitting works as following:

    1. Find IDs in the source file: add_id function and split nodes: add_split_node function
    2. Check for references on every node with check_for_references_function
    3. Take references and run Indirect ID resolver
    4. Calculate set of connected XML nodes
    5. Write out XML files for each set of connected nodes (outside this class)
    """
    def __init__(self, persist=False):
        self.IDs = set()
        self.SplitNodes = defaultdict(list)
        self.Refs = defaultdict(set)
        self.IDs2Exact = defaultdict(set)

    def clear(self):
        self.IDs = set()
        self.SplitNodes = defaultdict(list)
        self.Refs = defaultdict(set)
        self.IDs2Exact = defaultdict(set)

    def check_for_references(self, **kwargs):
        """
        FastXMLWalker callback function
        Checks all attributes of the current element whether it occurs in the list of IDs
        If an ID has been found the element and all parent elements are searched for an attribute named ID
        if such an element has been found a reference from the ID to the ID found in the attribute is created
        :param kwargs: FastXMLWalker kwargs
        :return: Mone
        """
        element = kwargs["element"]
        for attrib in [element.attrib[x] for x in element.attrib if x != "ID"]:
            if attrib in self.IDs:
                # find parent
                tmp_elem = element
                target_id = attrib
                source_id = None
                while True:
                    if "ID" in tmp_elem.attrib:
                        source_id = tmp_elem.attrib["ID"]
                        break
                    if tmp_elem.getparent() is None:
                        break
                    tmp_elem = tmp_elem.getparent()

                if not source_id == target_id:
                    self.Refs[source_id].add(target_id)
                    if len(self.Refs) % 10000 == 0:
                        Logger.info("%s Refs" % len(self.Refs))

    def add_split_node(self, **kwargs):
        """
        FastXMLWalker callback function
        Add a found split nodes: This callback should fire on a splitnode, it will then add the node to a list of splitnodes
        :param kwargs: FastXMLWalker kwargs
        :return: None
        """
        ID = kwargs["element"].attrib["ID"]
        self.SplitNodes[kwargs['interest']].append(ID)
        walker = kwargs["walker"]
        self.IDs2Exact[ID].add(walker.exact_path)
        if sum([len(self.SplitNodes[x]) for x in self.SplitNodes]) % 10000 == 0:
            Logger.info("%s SplitNodes identified" % sum([len(self.SplitNodes[x]) for x in self.SplitNodes]))

    def add_id(self, **kwargs):
        """
        FastXMLWalker callback function
        Should fire on a  node with an ID
        The found ID is added to the set of IDs
        :param kwargs: FastXMLWalker kwargs
        :return: None
        """
        found_id = kwargs["element"].attrib["ID"]
        if not found_id in self.IDs:
            self.IDs.add(found_id)
            if len(self.IDs) % 10000 == 0:
                Logger.info("%s IDs" % len(self.IDs))

    def calc_connected_sets(self, refs, split_nodes):
        """
        Returns the connected element sets (set of elements that should occur together in the same file)
        :param refs: list of references
        :param split_nodes: list of nodes at which could be split (IDs represented via a string)
        :return: None
        """
        return {y: [refs[x] | set([x]) if x in refs else [x] for x in split_nodes[y]] for y in split_nodes}
        #return [refs[x] | set([x]) if x in refs else [x] for y in split_nodes for x in split_nodes[y]]

    def search_stepxml(self, myfile, split_path_node_size_tuples=None):
        """
        Search for connected sets in a StepXML file
        :param myfile: Path to StepXML file
        :param split_path_node_size_tuples: list of paths to splitnode IDs (e.g.: ["//{http://www.stibosystems.com/step}Product/@ID"])
        :return: list of connected sets (list of IDs)
        """
        fx = FastXMLCallbackWalker()

        interests = {
            Interest(
                interest="//@ID",
                callback=self.add_id
            )
        }
        if not split_path_node_size_tuples:
            split_path_node_size_tuples = [("//{http://www.stibosystems.com/step}Product/@ID", 10)]
        for splitnode_path, node_restriction in split_path_node_size_tuples:
            interests.add(SplitPath(interest=splitnode_path, callback=self.add_split_node, node_restriction=node_restriction))

        fx.register_interests(
            interests
        )
        fx.walk_tree(myfile)
        Logger.debug("IDs: %s" % self.IDs)
        Logger.debug("split_nodes: %s" %self.SplitNodes)
        Logger.info("%S IDs found, %s SplitNodes found" % (len(self.IDs, len(self.SplitNodes))))
        fx2 = FastXMLCallbackWalker()
        fx2.register_event_callback("start", self.check_for_references)
        fx2.walk_tree(myfile)

        Logger.debug("direct: %s" % self.Refs)
        Logger.info("%s direct dependencies found" % (len(self.Refs)))

        idr = IndirectIDResovler(self.Refs, self.SplitNodes)
        idr.resolve_indirect()
        Logger.debug("indirect: %s" % idr.refs)
        Logger.info("%s indirect dependencies found" % (len(idr.refs)))

        connected_sets = self.calc_connected_sets(self.Refs, self.SplitNodes)
        Logger.debug("connected_sets: %s" % connected_sets)
        Logger.info("connected sets calculation completed")
        connected_sets2 = {}
        for path in connected_sets:
            connected_set2 = []
            for connected_set_path in connected_sets[path]:
                my_set = set()
                for item in connected_set_path:
                    for exactpath in self.IDs2Exact[item]:
                        my_set.add(exactpath)
                connected_set2.append(my_set)
            connected_sets2[path] = connected_set2
        nd = NodeDistributor(connected_sets2)
        distribution_to_files = nd.distribute()

        Logger.debug("distribution to files: %s" % distribution_to_files)
        Logger.info("distribution to files completed")

        return distribution_to_files
#        return connected_sets2

class GenIF2Splitter:
    """
    A XML splitter that splits generic interface 2.0 xml format

    1. find source and target for relations, split nodes, ids
    2. indirect ids are resolved
    3. connected sets are calculated
    4. node are distributed to files
    """
    def __init__(self):
        self.relations = defaultdict(lambda: defaultdict(list))
        self.IDs = set()
        self.ExactPathIDs2SplitNodes = defaultdict(list)
        self.IDs2ExactPaths = defaultdict(set)
        self.SplitNodes = defaultdict(list)
        self.Refs = defaultdict(set)

    def clear(self):
        self.relations = defaultdict(lambda: defaultdict(list))
        self.IDs = set()
        self.ExactPathIDs2SplitNodes = defaultdict(list)
        self.IDs2ExactPaths = defaultdict(set)
        self.SplitNodes = defaultdict(list)
        self.Refs = defaultdict(set)

    def add_target(self, **kwargs):
        """
        FastXMLWalker callback function
        Should be fired on an element that is a target to a reference
        Together with add source function it will create a reference from source to target
        :param kwargs: FastXMLWalker kwargs
        :return: None
        """
        target_id = kwargs["element"].text
        relation_node_exact_id = kwargs["walker"].exact_path.rsplit("/", 2)[0]
        Logger.debug("addTarget %s to %s" % (target_id, relation_node_exact_id))

        self.relations[relation_node_exact_id]["target_id"].append(target_id)

    def add_source(self, **kwargs):
        """
        FastXMLWalker callback function
        Should be fired on an element that is a source to a reference
        Together with add target function it will create a reference from source to target
        :param kwargs: FastXMLWalker kwargs
        :return: None
        """
        source_id = kwargs["element"].text
        relation_node_exact_id = kwargs["walker"].exact_path.rsplit("/", 2)[0]
        Logger.debug("addSource %s to %s" % (source_id, relation_node_exact_id))
        self.relations[relation_node_exact_id]["source_id"].append(source_id)

    def relation_to_ref(self, **kwargs):
        """
        FastXMLWalker callback function
        Should be fired on the end tag of a relation element
        In this function source and target are brought together and references in self.Refs are created
        :param kwargs: FastXMLWalker kwargs
        :return: None
        """
        ep = kwargs["walker"].exact_path
        for id in self.relations[ep]["source_id"]:
            self.Refs[id].update(self.relations[ep]["target_id"])
        del self.relations[ep]

    def add_split_node(self, **kwargs):
        """
        FastXMLWalker callback function
        Should be fired on split nodes
        To split nodes (self.SplitNodes[<interest>]) the exact path of this node (e.g: /*[0]/*[0](*[0]) is added
        :param kwargs: FastXMLWalker kwargs
        :return: None
        """
        #self.SplitNodes[kwargs["interest"]].append(kwargs["walker"].exact_path)
        self.SplitNodes[kwargs["interest"]].append(kwargs["walker"].exact_path)
        if sum([len(self.SplitNodes[x]) for x in self.SplitNodes]) % 10000 == 0:
            Logger.info("%s SplitNodes" % sum([len(self.SplitNodes[x]) for x in self.SplitNodes]))

    def add_id(self, **kwargs):
        """
        FastXMLWalker callback function
        Should be fired on nodes that contain an ID
        Saves the id to self.IDs
        :param kwargs: FastXMLWalker kwargs
        :return: None
        """
        found_id = kwargs["element"].text
        exact_path_parent = kwargs["walker"].exact_path.rsplit("/", 1)[0]
        self.IDs2ExactPaths[found_id].add(exact_path_parent)
        if found_id not in self.IDs:
            self.IDs.add(found_id)
            if len(self.IDs) % 10000 == 0:
                Logger.info("%s IDs" % len(self.IDs))

    def add_split_node_id(self, **kwargs):
        """
        FastXMLWalker callback function
        Should be fired on the id node of a split node
        :param kwargs: FastXMLWalker kwargs
        :return: None
        """
        found_id = kwargs["element"].text
        self.add_id(**kwargs)
        self.ExactPathIDs2SplitNodes[kwargs["walker"].exact_path.rsplit("/", 1)[0]].append(found_id)
        if found_id not in self.IDs:
            self.IDs.add(found_id)
            if len(self.IDs) % 10000 == 0:
                Logger.info("%s IDs identified" % len(self.IDs))

    def calc_splitnode_ids(self):
        """
        convert self.SplitNodes from list of split nodes to list of tuples (split node id, <exact paths>)
        :return: None
        """
        for split_path in self.SplitNodes:
            split_nodes = []
            for split_node in self.SplitNodes[split_path]:
                split_nodes.append((split_node, self.ExactPathIDs2SplitNodes[split_node]))
            self.SplitNodes[split_path] = split_nodes

    def calc_connected_sets(self, split_nodes):
        """
        Calculates all the ids that need to be in one file
        :param split_nodes:
        :return: dictionary with split path as key and a list of connected sets as value
        """
        res = {split_path: [set([exact for id_ in items[1] for ref in self.Refs[id_]|set([id_]) for exact in self.IDs2ExactPaths[ref]]) for items in split_nodes[split_path]] for split_path in split_nodes}
        return res

    def convert2exactpaths(self, listofids):
        """
        Converts IDs to exact paths
        :param listofids: List of IDs (string)
        :return: list of exact paths to the IDs
        """
        return [exact for id in listofids for exact in self.IDs2ExactPaths[id]]

    def search_genif2(self, genif_file, split_path_node_restriction_tuples):
        """
        Search connected sets in genif2 files
        :param genif_file: path to a genif2 file
        :return: list of sets of exact paths (each list entry should be written in a different file)
        """
        # root=None
        fx = FastXMLCallbackWalker()
        if not split_path_node_restriction_tuples:
            split_path_node_restriction_tuples = [
                ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item", 1),
                ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}asset", 2),
            ]
        interests = {Interest(
            interest="/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}relation/{http://www.media-saturn.com/msx}source/{http://www.media-saturn.com/msx}uniqueID",
            callback=self.add_source
        ), Interest(
            interest="/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}relation/{http://www.media-saturn.com/msx}target/{http://www.media-saturn.com/msx}uniqueID",
            callback=self.add_target
        ), Interest(
            interest="//{http://www.media-saturn.com/msx}relation",
            callback=self.relation_to_ref,
            event='end'
        ), Interest(
            interest="//{http://www.media-saturn.com/msx}uniqueID",
            callback=self.add_id
        )}
        for split_path_node_restriction_tuple in split_path_node_restriction_tuples:
            interests.add(
                SplitPath(
                    interest=split_path_node_restriction_tuple[0],
                    callback=self.add_split_node,
                    node_restriction=split_path_node_restriction_tuple[1]
                )
            )
            interests.add(
                Interest(
                    interest="%s/{http://www.media-saturn.com/msx}uniqueID" % split_path_node_restriction_tuple[0],
                    callback=self.add_split_node_id,
                )
            )
        fx.register_interests(
            interests
        )
        for _uuid in fx._relative_interests_trees:
            Logger.debug(RenderTree(fx._relative_interests_trees[_uuid].interest_tree))
        fx.walk_tree(genif_file)
        Logger.debug("ids: %s" % self.IDs)
        Logger.debug("split_nodes: %s" % self.SplitNodes)
        Logger.info("%s IDs, %s split nodes, %s direct references identified" % (len(self.IDs), sum([len(self.SplitNodes[x]) for x in self.SplitNodes]), len(self.Refs)))

        Logger.debug("IDsSplitNodes %s" % self.ExactPathIDs2SplitNodes)
        Logger.debug("direct: %s" % self.Refs)
        self.calc_splitnode_ids()

        idr = IndirectIDResovler(self.Refs, self.SplitNodes)
        idr.resolve_indirect()
        Logger.debug("indirect: %s" % idr.refs)
        Logger.info("indirect reference calculation completed")

        connected_sets = self.calc_connected_sets(self.SplitNodes)

        Logger.debug("connected_sets: %s" % connected_sets)
        Logger.info("connected set calculation completed")

        nd=NodeDistributor(connected_sets)
        distribution_to_files = nd.distribute()

        Logger.debug("distribution to files: %s" % distribution_to_files)
        Logger.info("distribution to files completed")

        return distribution_to_files

class NodeDistributor:
    """
    connected_sets_by_split_path: dictionary with split paths as key and a list of connected sets that belong to the 
    split path as value
    """
    def __init__(self, connected_sets_by_split_path):
        self.connected_sets_by_split_path = connected_sets_by_split_path

    def distribute(self):
        """
        Distribute nodes that are selected by a split path into bags. Every bag has a node restriction which is the
        maximum number of nodes allowed in a bag. The bag filling level is a number between 0 and 1 where 1 is a full bag
        :return: list of bags (bag contains set of node paths)
        """
        bags=[]
        # bag_filling_level = 1 --> node_restriction / nodes_to_add <= 1
        # node_restriction / nodes_to_add = 1
        bag_filling_level = 0
        bag=[]
        while len(self.connected_sets_by_split_path):
            split_path_to_delete = []
            for split_path in self.connected_sets_by_split_path:
                assert split_path.node_restriction > 0
                items_to_take_from = self.connected_sets_by_split_path[split_path]
                take_number_items = min((1-bag_filling_level) * split_path.node_restriction, len(items_to_take_from))
                if take_number_items:
                    assert take_number_items <= len(items_to_take_from)
                    assert items_to_take_from
                    assert take_number_items <= split_path.node_restriction
                    bag_filling_level += take_number_items/split_path.node_restriction
                    assert bag_filling_level <= 1
                    assert take_number_items
                    assert int(take_number_items)
                    items_to_add_to_bag = items_to_take_from[:int(take_number_items)]
                    self.connected_sets_by_split_path[split_path] = items_to_take_from[int(take_number_items):]
                    if not self.connected_sets_by_split_path[split_path]:
                        split_path_to_delete.append(split_path)
                    bag.extend(items_to_add_to_bag)
            for to_del in split_path_to_delete:
                del self.connected_sets_by_split_path[to_del]
            assert bag
            bags.append(bag)
            bag=[]
            bag_filling_level = 0
        return bags


class IndirectIDResovler:
    def __init__(self, refs, split_nodes):
        self.refs = refs
        self.split_nodes = split_nodes
        self.visited_ids = set()

    def resolve_indirect(self):
        """
        Resolve indirect dependencies, if there is a reference A -> B -> C a new reference A -> C is created
        :return:
        """
        for split_node_id in self.split_nodes:
            self.resolve_recursive(split_node_id)
        return self.refs

    def resolve_recursive(self, source_id):
        """
        Resolve recursive indirect deoendencies
        Go through all references and check if there is a ref A -> >B -> C and add new reference A -> C
        :param source_id:
        :return:
        """
        if source_id in self.refs:
            target_ids = self.refs[source_id]
            for target_id in target_ids:
                self.resolve_recursive(target_id)
            if source_id in self.refs:
                target_ids2 = self.refs[source_id].copy()
                for target_id in target_ids2:
                    if target_id in self.refs:
                        target_target_ids = self.refs[target_id].copy()
                        for target_target_id in target_target_ids:
                            if target_target_id and source_id:
                                self.refs[source_id].add(target_target_id)

            if source_id not in self.visited_ids:
                self.visited_ids.add(source_id)


class SplitPath(Interest):
    """
    This class represents a Interest to a split path, it has node restriction which is the max number of nodes in a file
    of this split path
    """
    def __init__(self, interest, callback, node_restriction=10):
        super(SplitPath, self).__init__(interest=interest, callback=callback, event="start")
        self.node_restriction = node_restriction

    def __str__(self):
        return "split_path<%s>" % self.interest
