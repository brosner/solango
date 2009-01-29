#
# Copyright 2008 Optaros, Inc.
#

from xml.dom import Node

"""
An extension to core.xmlutils, providing Solr-specific parsing facilities.  By
importing this module, core.xmlutils.* is available.
"""

def get_list(node):
    """
    Parses the specified Solr XML arr element into a list.
    """
    ret = []
    
    for c in node.childNodes:
        if c.nodeType == Node.ELEMENT_NODE:
            if c.localName == "str":
                ret.append(get_unicode(c))
            elif c.localName == "int":
                ret.append(get_int(c))
            elif c.localName == "date":
                ret.append(c)
            elif c.localName == "arr":
                ret.append(get_list(c))
            elif c.localName == "lst":
                ret.append(get_dictionary(c))
            elif c.localName == "doc":
                ret.append(get_dictionary(c))
    
    return ret       

def get_dictionary(node):
    """
    Parses the specified Solr XML lst element into a dictionary.
    """
    ret = {}
    
    for c in node.childNodes:
        if c.nodeType == Node.ELEMENT_NODE:
            
            name = c.attributes.item(0).value
            
            if c.localName == "str":
                ret[name] = get_unicode(c)
            elif c.localName == "int":
                ret[name] = get_int(c)
            elif c.localName == "date":
                ret[name] = get_unicode(c)
            elif c.localName == "arr":
                ret[name] = get_list(c)
            elif c.localName == "lst":
                ret[name] = get_dictionary(c)
            elif c.localName == "doc":
                ret[name] = get_dictionary(c)
    
    return ret

"""
Generic utilities for manipulating DOM objects.
"""

def get_unicode(node):
    """
    Parses the specified text Node into a unicode object.
    """
    ret = unicode("", "utf-8")
    
    for c in node.childNodes:
        if c.nodeType == Node.TEXT_NODE or c.nodeType == Node.CDATA_SECTION_NODE:
            ret += c.data
    
    return ret

def get_int(node):
    """
    Parses the specified text Node into an int.
    """
    return int(get_unicode(node))

def get_float(node):
    """
    Parses the specified text Node into an float.
    """
    return float(get_unicode(node))

def get_attribute(node, name):
    """
    Returns the value of the Node Attr with the specified name.
    """
    if not node.hasAttributes():
        return None
    
    at = node.attributes.getNamedItem(name)
    
    if not at:
        return None
    
    return at.value

def get_attributes_dictionary(node):
    """
    Returns a dictionary representation of the specified Node's attributes.
    """
    if not node.hasAttributes:
        return {}
    
    ret = {}
    
    for i in range(0, node.attributes.length):
        a = node.attributes.item(i)
        ret[a.localName] = a.value
    
    return ret

def get_child_node(parent, tag, name=None):
    """
    Returns the first child Node of the specified tag from parent.  Use
    this function instead of getElementsByTagName where possible.
    """
    if not len(parent.childNodes):
        return None
    
    for c in parent.childNodes:
        if c.nodeType == Node.ELEMENT_NODE and c.localName == tag:
            if name:
                if get_attribute(c, "name") == name:
                    return c
            else:
                return c
    
    return None

def get_child_nodes(parent, tag, name=None):
    """
    Returns all child Nodes of the specified tag from parent.  Use this 
    function instead of getElementsByTagName where possible.
    """
    if not len(parent.childNodes):
        return []
    
    ret = []
    
    for c in parent.childNodes:
        if c.nodeType == Node.ELEMENT_NODE and c.localName == tag:
            if name:
                if get_attribute(c, "name") == name:
                    ret.append(c)
            else:
                ret.append(c)
    
    return ret

def get_sibling_node(sibling, tag, name=None):
    """
    Returns the first sibling Node of the specified tag from sibling.  Use
    this function instead of getElementsByTagName where possible.
    """
    sib = sibling.nextSibling
    
    while(sib):
        
        if sib.nodeType == Node.ELEMENT_NODE and sib.localName == tag:
            if name:
                if get_attribute(sib, "name") == name:
                    return sib
            else:
                return sib
        
        sib = sib.nextSibling
        
    return None