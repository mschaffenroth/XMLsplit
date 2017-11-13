import glob
import os
import unittest
from collections import defaultdict
# set value (if needed)
from lxml import etree

from xml_splitter.xmlsplit import GenIF2Splitter
from xml_walker.XMLWriter import XMLWriter
from test.testfile_generator import gen_genif2


class TestGenIf(unittest.TestCase):
    def clean(self):
        if os.path.exists(self.split_file):
            os.remove(self.split_file)
        for file in glob.glob(self.out_file + "*.xml"):
            os.remove(file)

    def setUp(self):
        self.split_file = "../out/test_genif2_generated.xml"
        self.out_file = "../out/%s.out" % os.path.basename(self.split_file)
        self.clean()

    def tearDown(self):
        self.clean()

    def test_genif_small(self):

        nodes = 500
        start_id = 1000000
        item_restriction = 100
        gen_genif2(self.split_file, start_id, start_id + nodes)

        s = GenIF2Splitter()
        bags = s.search_genif2(self.split_file, [
                        ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item", item_restriction),
                        ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}asset", 200),
                    ]
        )
        self.assertEqual(len(bags), nodes/item_restriction)
        for item in bags:
            self.assertLessEqual(len(item), item_restriction)
        s.clear()
        # distribute bags to files
        paths_to_files = defaultdict(set)
        for i, bag in enumerate(bags):
            for bag_entry in bag:
                for set_entry in bag_entry:
                    paths_to_files[set_entry].add(i)

        xmlwriter = XMLWriter()
        xmlwriter.split(self.split_file, self.out_file, paths_to_files)
        self.assertEqual(len(glob.glob(self.out_file + "*.xml")), nodes/item_restriction)
        for file in glob.glob(self.out_file):
            tree = etree.parse(file)
            self.assertEqual(tree.xpath("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item"), item_restriction)

    def test_genif_medium(self):

        nodes = 500000
        start_id = 1000000
        item_restriction = 100
        gen_genif2(self.split_file, start_id, start_id + nodes)

        s = GenIF2Splitter()
        bags = s.search_genif2(self.split_file, [
                        ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item", item_restriction),
                        ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}asset", 200),
                    ]
        )
        self.assertEqual(len(bags), nodes/item_restriction)
        for item in bags:
            self.assertLessEqual(len(item), item_restriction)
        s.clear()
        # distribute bags to files
        paths_to_files = defaultdict(set)
        for i, bag in enumerate(bags):
            for bag_entry in bag:
                for set_entry in bag_entry:
                    paths_to_files[set_entry].add(i)

        xmlwriter = XMLWriter()
        xmlwriter.split(self.split_file, self.out_file, paths_to_files)
        self.assertEqual(len(glob.glob(self.out_file + "*.xml")), nodes/item_restriction)
        for file in glob.glob(self.out_file):
            tree = etree.parse(file)
            self.assertEqual(tree.xpath("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item"), item_restriction)

    @unittest.skip("too huge")
    def test_genif_huge(self):

        nodes = 50000000
        start_id = 1000000
        item_restriction = 10000
        gen_genif2(self.split_file, start_id, start_id + nodes)

        s = GenIF2Splitter()
        bags = s.search_genif2(
            self.split_file,
            [
                ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item", item_restriction),
                ("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}asset", 200),
            ]
        )
        self.assertEqual(len(bags), nodes/item_restriction)
        for item in bags:
            self.assertLessEqual(len(item), item_restriction)
        s.clear()
        # distribute bags to files
        paths_to_files = defaultdict(set)
        for i, bag in enumerate(bags):
            for bag_entry in bag:
                for set_entry in bag_entry:
                    paths_to_files[set_entry].add(i)

        xmlwriter = XMLWriter()
        xmlwriter.split(self.split_file, self.out_file, paths_to_files)
        self.assertEqual(len(glob.glob(self.out_file + "*.xml")), nodes/item_restriction)
        for file in glob.glob(self.out_file):
            tree = etree.parse(file)
            self.assertEqual(tree.xpath("/{http://www.media-saturn.com/msx}data/{http://www.media-saturn.com/msx}item"), item_restriction)


if __name__ == '__main__':
    unittest.main()