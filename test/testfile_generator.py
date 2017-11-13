from lxml import etree


def gen_genif2(outfile="../out/genif2_generated.xml", from_id=1000000, to_id=1199999):
    root = etree.Element("data",
                         nsmap={
                             None: "http://www.media-saturn.com/msx",
                             "vc":"http://www.w3.org/2007/XMLSchema-versioning",
                             "xsi":"http://www.w3.org/2001/XMLSchema-instance"
                         }
            )
    #root.set("interesting", "somewhat")

    for i in range(from_id,to_id):
        item = etree.SubElement(root, "item")
        uniqueId = etree.SubElement(item, "uniqueID")
        uniqueId.text = "MY_ID_%s" % i
    et = etree.ElementTree(root)
    et.write(outfile, pretty_print=True)


def gen_stepxml(outfile="../out/stepxml_generated.xml", from_id=1000000, to_id=1199999):
    root = etree.Element(
        "STEP-ProductInformation",
        nsmap={
             None: "http://www.stibosystems.com/step",
            # "schemaLocation": "http://www.stibosystems.com/step PIM.xsd",
             "ContextID": "NL_nl_global",
             "ExportContext": "NL_nl_global",
             "WorkspaceID": "Main",
        }
    )
    products = etree.SubElement(root, "Products")
    for i in range(from_id, to_id):
        product = etree.SubElement(products, "Product")
        product.set("ID", "MY_ID_%s" % i)
    et = etree.ElementTree(root)
    et.write(outfile, pretty_print=True)


if __name__ == "__main__":
    gen_genif2()
    gen_stepxml()
