from collections import defaultdict

from anytree import RenderTree

from xml_walker.Logger import Logger
from xml_walker.NodeInterest import Interest
from xml_walker.XMLWalker import FastXMLCallbackWalker


class StepXMLsplitter:
    def __init__(self):
        self.IDs = set()
        self.SplitNodes = defaultdict(list)
        self.Refs = defaultdict(set)
        self.IDs2Exact = defaultdict(set)

    def check_for_references(self, **kwargs):
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
        ID = kwargs["element"].attrib["ID"]
        self.SplitNodes[kwargs['interest'].interest].append(ID)
        walker = kwargs["walker"]
        self.IDs2Exact[ID].add(walker.exact_path)
        if sum([len(self.SplitNodes[x]) for x in self.SplitNodes]) % 10000 == 0:
            Logger.info("%s SplitNodes" % sum([len(self.SplitNodes[x]) for x in self.SplitNodes]))

    def add_id(self, **kwargs):
        found_id = kwargs["element"].attrib["ID"]
        if not found_id in self.IDs:
            self.IDs.add(kwargs["element"].attrib["ID"])
            if len(self.IDs) % 10000 == 0:
                Logger.info("%s IDs" % len(self.IDs))

    def calc_connected_sets(self, refs, split_nodes):
        return [refs[x] | set([x]) if x in refs else [x] for y in split_nodes for x in split_nodes[y]]

    def search_stepxml(self, myfile):
        # root=None
        fx = FastXMLCallbackWalker()

        fx.register_interests(
            {Interest(
                interest="//{http://www.stibosystems.com/step}Asset/@ID",
                callback=self.add_split_node
            ), Interest(
                interest="//@ID",
                callback=self.add_id
            )}
        )
        # for _uuid in fx.relative_interests_trees:
        #    print(RenderTree(fx.relative_interests_trees[_uuid]))
        fx.walk_tree(myfile)
        Logger.debug("IDs: %s" % self.IDs)
        Logger.debug("split_nodes: %s" %self.SplitNodes)
        fx2 = FastXMLCallbackWalker()
        fx2.register_event_callback("start", self.check_for_references)
        fx2.walk_tree(myfile)

        Logger.debug("direct: %s" % self.Refs)

        idr = IndirectIDResovler(self.Refs, self.SplitNodes)
        idr.resolve_indirect()
        Logger.debug("indirect: %s" % idr.refs)

        connected_sets = self.calc_connected_sets(self.Refs, self.SplitNodes)
        Logger.debug("conected_sets: %s" % connected_sets)
        connected_sets2 = []
        for connected_set in connected_sets:
            my_set = set()
            for item in connected_set:
                for exactpath in self.IDs2Exact[item]:
                    my_set.add(exactpath)
            connected_sets2.append(my_set)
        return connected_sets2

class GenIF2Splitter:
    def __init__(self):
        self.relations = defaultdict(lambda: defaultdict(list))
        self.IDs = set()
        self.ExactPathIDs2SplitNodes = defaultdict(list)
        self.IDs2ExactPaths = defaultdict(set)
        self.SplitNodes = defaultdict(list)
        self.Refs = defaultdict(set)

    def add_target(self, **kwargs):
        target_id = kwargs["element"].text
        relation_node_exact_id = kwargs["walker"].exact_path.rsplit("/", 2)[0]
        print("addTarget %s to %s" % (target_id, relation_node_exact_id))

        self.relations[relation_node_exact_id]["target_id"].append(target_id)

    def add_source(self, **kwargs):
        source_id = kwargs["element"].text
        relation_node_exact_id = kwargs["walker"].exact_path.rsplit("/", 2)[0]
        print("addSource %s to %s" % (source_id, relation_node_exact_id))
        self.relations[relation_node_exact_id]["source_id"].append(source_id)

    def relation_to_ref(self, **kwargs):
        ep = kwargs["walker"].exact_path
        #print("handle relation %s" % ep)
        #print("relation %s" % self.relations[ep])
        for id in self.relations[ep]["source_id"]:
            self.Refs[id].update(self.relations[ep]["target_id"])
        del self.relations[ep]
        #print("relations length %s" % len(self.relations))

    def add_split_node(self, **kwargs):
        #self.SplitNodes[kwargs["interest"]].append(kwargs["walker"].exact_path)
        self.SplitNodes[kwargs["interest"]].append(kwargs["walker"].exact_path)
        if sum([len(self.SplitNodes[x]) for x in self.SplitNodes]) % 10000 == 0:
            Logger.info("%s SplitNodes" % sum([len(self.SplitNodes[x]) for x in self.SplitNodes]))

    def add_id(self, **kwargs):
        found_id = kwargs["element"].text
        exact_path_parent = kwargs["walker"].exact_path.rsplit("/", 1)[0]
        self.IDs2ExactPaths[found_id].add(exact_path_parent)
        if found_id not in self.IDs:
            self.IDs.add(found_id)
            if len(self.IDs) % 10000 == 0:
                print("%s IDs" % len(self.IDs))

    def add_split_node_id(self, **kwargs):
        found_id = kwargs["element"].text
        self.add_id(**kwargs)
        self.ExactPathIDs2SplitNodes[kwargs["walker"].exact_path.rsplit("/", 1)[0]].append(found_id)
        if found_id not in self.IDs:
            self.IDs.add(found_id)
            if len(self.IDs) % 10000 == 0:
                print("%s IDs" % len(self.IDs))

    def calc_splitnode_ids(self):
        for split_path in self.SplitNodes:
            split_nodes = []
            for split_node in self.SplitNodes[split_path]:
                split_nodes.append((split_node, self.ExactPathIDs2SplitNodes[split_node]))
            self.SplitNodes[split_path] = split_nodes
            print(split_nodes)

    # calculates all the ids that need to be in one file
    def calc_connected_sets(self, refs, split_nodes):
        res = {split_path: [set([exact for id_ in items[1] for ref in self.Refs[id_]|set([id_]) for exact in self.IDs2ExactPaths[ref]]) for items in split_nodes[split_path]] for split_path in split_nodes}
        return res

    def convert2exactpaths(self, listofids):
        return [exact for id in listofids for exact in self.IDs2ExactPaths[id]]

    def search_genif2(self, genif_file):
        # root=None
        fx = FastXMLCallbackWalker()

        fx.register_interests(
            {Interest(
                interest="/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}relation/{http://www.media-saturn.com/msx}source/{http://www.media-saturn.com/msx}uniqueID",
                callback=self.add_source
            ), Interest(
                interest="/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}relation/{http://www.media-saturn.com/msx}target/{http://www.media-saturn.com/msx}uniqueID",
                callback=self.add_target
            )
                , SplitPath(
                interest="/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item",
                callback=self.add_split_node,
                node_restriction=4
            ),
                SplitPath(
                    interest="/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}asset",
                    callback=self.add_split_node,
                    node_restriction=2
                ),
                Interest(
                    interest="/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item/{http://www.media-saturn.com/msx}uniqueID",
                    callback=self.add_split_node_id,
                ),
                Interest(
                    interest="/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}asset/{http://www.media-saturn.com/msx}uniqueID",
                    callback=self.add_split_node_id,
                )
                , Interest(
                interest="//{http://www.media-saturn.com/msx}relation",
                callback=self.relation_to_ref,
                event='end'
            )
                , Interest(
                interest="//{http://www.media-saturn.com/msx}uniqueID",
                callback=self.add_id
            )}
        )
        # print(RenderTree(fx.absolute_interest_tree.interest_tree))
        for _uuid in fx._relative_interests_trees:
            print(RenderTree(fx._relative_interests_trees[_uuid].interest_tree))
        fx.walk_tree(genif_file)
        Logger.debug("ids: %s" % self.IDs)
        Logger.debug("split_nodes: %s" % self.SplitNodes)
        # print("relations: %s" % fx.relations)

        Logger.debug("IDsSplitNodes %s" % self.ExactPathIDs2SplitNodes)
        Logger.debug("direct: %s" % self.Refs)
        self.calc_splitnode_ids()

        idr = IndirectIDResovler(self.Refs, self.SplitNodes)
        idr.resolve_indirect()
        Logger.debug("indirect: %s" % idr.refs)

        connected_sets = self.calc_connected_sets(self.Refs, self.SplitNodes)

        Logger.debug("connected_sets: %s" % connected_sets)

        nd=NodeDistributor(connected_sets)
        distribution_to_files = nd.distribute()

        Logger.debug("distribution to files: %s" % distribution_to_files)

        return distribution_to_files
        #fx2 = FastXMLCallbackWalker()
        #fx2.register_interests(
        #    [
        #        NodeDistributionInterest(interest, target_file="output_%s" % i, callback=
        #            lambda **kwargs: print("i am at node %s and want to write to file %s" % (
        #                XMLNode(kwargs["element"], [kwargs["interest"].target_file]).start_tag, kwargs["interest"].target_file)
        #                              )
        #        )
        #        for i, file_ in enumerate(distribution_to_files) for interests in file_ for interest in interests
        #    ]
        #)
        #fx2.walk_tree(genif_file)


class NodeDistributor:
    """
    connected_sets_by_split_path: dictionary with split paths as key and a list of connected sets that belong to the 
    split path as value
    """
    def __init__(self, connected_sets_by_split_path):
        self.connected_sets_by_split_path = connected_sets_by_split_path

    # distribute nodes that are selected by a split path into bags. Every bag has a node restriction which is the
    # maximum number of nodes allowed in a bag. The bag filling level is a number between 0 and 1 where 1 is a full bag
    def distribute(self):
        bags=[]
        # bag_filling_level = 1 --> node_restriction / nodes_to_add <= 1
        # node_restriction / nodes_to_add = 1
        bag_filling_level = 0
        bag=[]
        while len(self.connected_sets_by_split_path):
            for split_path in self.connected_sets_by_split_path.copy():
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
                    # items_to_add_to_bag =[",".join([str(split_path).rsplit("}",1)[1]]*int(take_number_items))]
                    # print("items in the bag %s" % [",".join([str(split_path).rsplit("}",1)[1]]*int(take_number_items))])
                    # remove items from set
                    self.connected_sets_by_split_path[split_path] = items_to_take_from[int(take_number_items):]
                    if len(self.connected_sets_by_split_path[split_path]) == 0:
                        del self.connected_sets_by_split_path[split_path]
                    bag.extend(items_to_add_to_bag)
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
        for split_node_id in self.split_nodes:
            self.resolve_recursive(split_node_id)
        return self.refs

    def resolve_recursive(self, source_id):
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
    def __init__(self, interest, callback, node_restriction=10):
        super(SplitPath, self).__init__(interest=interest, callback=callback, event="start")
        self.node_restriction = node_restriction

    def __str__(self):
        return "split_path<%s>" % self.interest
