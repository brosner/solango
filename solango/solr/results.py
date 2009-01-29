#
# Copyright 2008 Optaros, Inc.
#

from xml.dom import minidom
from solango.solr import xmlutils
from solango.solr.facet import Facet
from solango.log import logger
from django.conf import settings 
from solango import registry
import urllib

class Results:
    """
    Results instances parse Solr response XML into Python objects.  A Solr
    response contains a header section and, optionally, a result section.
    For update requests, the result section is generally omitted.
    
    <response>
      <lst name="responseHeader">
        <int name="status">0</int>
        <int name="QTime">12</int>
        <lst name="params">
          <str name="q">test</str>
          ...
        </lst>
        ...
      </lst>
      <result name="response" numfound="1" start="0">
        <doc>
          <str name="id">document_id</str>
          <str name="text">some test text</str>
          ...
        </doc>
      </result>
      <lst name="facet_counts">
        <lst name="facet_fields">
          <lst name="some field">
            <int name="some value">2</int>
            ...
          </lst>
        </lst>
      </lst>
      <lst name="highlighting">
        <lst name="document_id">
          <arr name="text">
            <str>some <em>test</em> text</str>
            ...
          </arr>
        </lst>
        ...
      </lst>
    </response>
    
    See http://wiki.apache.org/solr/XMLResponseFormat
    """
    
    (_doc, header, rows, start) = (None, None, 10, 0)
    
    def _parse_header(self):
        """
        Parses the results header into the header dictionary.
        """
        header = xmlutils.get_child_node(self._doc.firstChild, "lst", "responseHeader")
        
        if not header:
            raise ValueError, "Results contained no header."
        
        self.header = xmlutils.get_dictionary(header)
        #logger.debug("Parsed %d header fields." % len(self.header))
    
    def __init__(self, xml):
        """
        Parses the provided XML body and initialize the header dictionary.
        """
        if not xml:
            raise ValueError, "Invalid or missing XML"
        
        self._doc = minidom.parseString(xml)
        
        self._parse_header()
    
    @property
    def status(self):
        """
        Returns the Solr response status code for this Results instance.
        """
        return self.header["status"]
    
    @property
    def success(self):
        """
        Returns true if this Results object indicates status of 0.
        """
        return self.status == 0
    
    @property
    def time(self):
        """
        Returns the server request time, in millis, for this Results instance.
        """
        return self.header["QTime"]
    
    @property
    def url(self):
        return urllib.urlencode(self.header['params'])

class UpdateResults(Results):
    """
    Results for Solr update requests.
    """
    def __init__(self, xml):
        Results.__init__(self, xml)
        
        self._doc.unlink()
    
class SelectResults(Results):
    """
    Results for Solr select requests.
    """
    
    (count, documents, facets, highlighting) = (None, None, None, None)
    
    def __init__(self, xml):
        """
        Parses the provided XML body, including documents, facets, and
        highlighting information.  See Results.__init__(self, xml).
        """
        Results.__init__(self, xml)
        
        (self.documents, self.facets, self.highlighting) = ([], [], {})
        
        self._parse_results()
        
        self._parse_facets()
        
        self._parse_highlighting()
        
        self._doc.unlink()
        
    def _parse_header(self):
        Results._parse_header(self)
        self.rows = int(self.header['params']['rows'])
        self.start = int(self.header['params']['start'])
    
    def _get_result_node(self):
        """
        Returns the result Node from this Result's DOM tree.
        """
        return xmlutils.get_child_node(self._doc.firstChild, "result")
      
    def _parse_results(self):
        """
        Parse the results array into the documents list.  Each resulting
        document element is a dictionary. 
        """
        result = self._get_result_node()
        
        if not result:
            raise ValueError, "Results contained no result."
        
        self.count = int(xmlutils.get_attribute(result, "numFound"))
        
        for d in xmlutils.get_child_nodes(result, "doc"):
            data_dict = xmlutils.get_dictionary(d)
            document = registry[data_dict['model']](data_dict)
            self.documents.append(document)
        
    def _parse_facets(self):
        """
        Parses the facet counts into this Result's facets list.
        """
        result = self._get_result_node()
        facets =  xmlutils.get_sibling_node(result, "lst", "facet_counts")
        
        if not facets:
            return None
        
        fields = xmlutils.get_child_node(facets, "lst", "facet_fields")

        if not fields:
            return None

        for facet in xmlutils.get_child_nodes(fields, "lst"):
            self.facets.append(Facet(facet))
        
    def _parse_highlighting(self):
        """
        Parses the highlighting list into this Result's highlighting dictionary.
        Also iterate over this Result's documents, inserting highlighting
        elements to their owning documents.
        """
        highlighting = xmlutils.get_child_node(self._doc.firstChild, "lst", "highlighting")
        
        if not highlighting:
            return
        
        self.highlighting = xmlutils.get_dictionary(highlighting)
        for d in self.documents:
            #TODO: Ugly
            model_key = settings.SEARCH_SEPARATOR.join([d.fields['model'].value, d.pk_field.value])
            for key, value in self.highlighting[model_key].items():
                d.highlight += ' ' + ' '.join(value)
                d.fields[key].highlight = ' '.join(value)