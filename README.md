# XMLWalker and XMLSplitter

This tool walks through XML documents and stops at defined xpaths where you can execute your custom code and access the XML structure.
One usage of the XMLWalker is the XMLSplitter component which is a memory efficient tool that allows to split huge XML files with low memory usage, 
whereas a DOM oriented approach (e.g. XSLT) uses around 10-20 times the size of the XML file in memory. Imagine a 10GB XML file, which cannot be 
handled in DOM fashion by most modern systems currently

## Interest
To mark parts of a XML document that are relevant for you we have interests.
An interest marks a path where a function given as parameter should be executed
    
    Interest(<path>, <callback function>)
    
It can be registered to an FastXMLCallbackWalker

## Paths
Paths are like xpaths, currently "/" is allowed to mark subnodes and "[]" to mark conditions on the nodes.


## FastXMLCallbackWalker

The following code is an example for the usage of the FastXMLCallbackWalker and the registration of a function that triggers on the xpath /a/b:

    def printme(**kwargs)
        print(kwargs["element"].tag)

    from xml_walker.NodeInterest import Interest
    walker = FastXMLCallbackWalker()
    walker.register_interest(Interest("/a/b", printme))
    walker.walk_tree("obj.xml")

The above code execute on the following file "obj.xml"
    
    <a>
        <b>
            hello
        </b>
        <b>
            world
        </b>
    </a>

would print "bb"
  
The callback function has the following kwargs (key-value arguments):
    
    interest: This is the interest that triggered the function
    walker: The walker where the interest is registered
    element: The element where the interest matched
    
## XMLWriter

XMLWriter is able to split a XML document into several documents by given paths.
The paths are assigned to documents and written into the documents.

    writer = XMLWriter()
    writer.split("inputfile.xml", "outputfile", {"/*[0]/*[1]":{1,2}, "/*[0]/*[2]":{1,3}})

The above code will lead to three documents: "outputfile1.xml", "outputfile2.xml" "outputfile3.xml".
The first document "outputfile1.xml" contains  /\*[0]/\*[1] and /\*[0]/\*[2] of the source document, 
"outputfile2.xml"  contains /\*[0]/\*[1] and "outputfile3.xml" \*[0]/\*[2].

The above code executed on the following file "inputfile.xml" would lead to
    
    <a>
        <b>
            hello
        </b>
        <b>
            world
        </b>
        <b>
            again
        </b>
        <b>
            and again
        </b>
    </a>

the following three output files:

outputfile1.xml
    
    <a>
        <b>
            world
        </b>
        <b>
            again
        </b>    
    </a>

outputfile2.xml

    <a>
        <b>
            world
        </b>
    </a>
   
outputfile3.xml

    <a>
        <b>
            again
        </b>
    </a> 
   
