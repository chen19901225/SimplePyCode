def toDOM(xml_src=None):
    from xml.dom import minidom
    if hasattr(xml_src,'documentElement'):
        return xml_src
    elif hasattr(xml_src,'read'):
        return minidom.parseString(xml_src.read())
    elif  isinstance(xml_src,basestring):
        xml=open(xml_src).read()
        return minidom.parseString(xml)
    else:
        raise ValueError,"Must be initialized with"+\
            "filename ,file-like obj or DOM obj"

if __name__=="__main__":
    print "Over"