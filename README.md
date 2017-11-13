# XMLWalker

This tool walks through XML documents and stops at defined xpaths where you can execute your custom code and access the XML structure

## Interest
An interest marks a path where a function given as parameter should be executed
    
    Interest(<path>, <callback function>)
    
It can be registered to an FastXMLCallbackWalker

## FastXMLCallbackWalker

    def printme(**kwargs)
        print(kwargs["element"])

    from xml_walker.NodeInterest import Interest
    walker = FastXMLCallbackWalker()
    walker.register_interest(Interest("/a/b", printme))
    walker.walk_tree("obj.xml")

  
The callback function has the following kwargs:
    
    interest: This is the interest that triggered the function
    walker: The walker where the interest is registered
    element: The element where the interest matched
    
##XMLWriter

XMLWriter is able to split a XML document into several documents by given paths.
The paths are assigned to documents and written into the documents.

    writer = XMLWriter()
    writer.split("inputfile.xml", "outputfile", {"/*[0]/*[1]":{1,2}, "/*[0]/*[2]":{1,3}})
    
The above code will lead to three documents: "outputfile1.xml", "outputfile2.xml" "outputfile3.xml".
The first document "outputfile1.xml" contains  /\*[0]/\*[1] and /\*[0]/\*[2] of the source document, 
"outputfile2.xml"  contains /\*[0]/\*[1] and "outputfile3.xml" \*[0]/\*[2].