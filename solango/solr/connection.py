#
# Copyright 2008 Optaros, Inc.
#

from datetime import datetime, timedelta
import urllib2

from django.conf import settings
from solango.log import logger
from solango.solr import results
from solango.solr.query import Query

(DELETE, ADD) = (0,1)

class SearchWrapper(object):
    """
    This class is the entry point for all search-bound actions, including
    adding (indexing), deleting, and selecting (searching).  It is a singleton,
    and should always be accessed via get_instance.
    """
    (available, heartbeat) = (False, None)
    (update_url, select_url, ping_urls) = (None, None, None)
    
    def __init__(self):
        """
        Resolves configuration and instantiates a Log for this object.
        """
        self.update_url = settings.SEARCH_UPDATE_URL
        self.select_url = settings.SEARCH_SELECT_URL
        self.ping_urls = settings.SEARCH_PING_URLS
  
        self.heartbeat = datetime(1970, 01, 01)
    
    def is_available(self):
        """
        Returns True if the search system appears to be available and in good
        health, False otherwise.  A ping is periodically sent to the search
        server to query its availability.
        """
        (now, delta) = (datetime.now(), timedelta(0, 300))
        
        if now - self.heartbeat > delta:
            try:
                for url in self.ping_urls:
                    res = urllib2.urlopen(url).read()
            except StandardError:
                self.available = False
            else:
                self.available = True
            
        return self.available
    
    def get_document_xml(self, documents, mode):
        """
        Returns Solr Document XML representation of the specified objects, 
        transformed according to mode, as a Unicode (utf-8) string".
        """
        if not documents:
            raise ValueError
        
        if not isinstance(documents, (list, tuple)):
            documents = [documents]
        
        xml = unicode("", "utf-8")
        for d in documents:
            if mode:
                xml += d.add()
            else:
                xml += d.delete()
        return xml
    
    def add(self, documents):
        """
        Adds the specified list of objects to the search index.  Returns a
        two-element List of UpdateResults; the first element corresponds to
        the add operation, the second to the subsequent commit operation.
        """
        if not documents:
            raise ValueError        
        
        xml = self.get_document_xml(documents, ADD)
        
        if not len(xml):
            return
        
        if not self.is_available():
            logger.info("add: Search is unavailable.")
            return
        
        res = self.update("\n<add>\n" + xml + "</add>\n")
        return [results.UpdateResults(res), self.commit()]
    
    def delete(self, documents):
        """
        Deletes the specified list of objects from the search index.  Returns
        a two-element List of UpdateResults; the first element corresponds to
        the delete operation, the second to the subsequent commit operation.
        """
        if not documents:
            raise ValueError
 
        xml = self.get_document_xml(documents, DELETE)
        
        if not len(xml):
            return
        
        if not self.is_available():
            logger.info("delete: Search is unavailable.")
            return
        
        res = self.update("\n<delete>\n" + xml + "</delete>\n")
        return [results.UpdateResults(res), self.commit()]
    
    def commit(self):
        """
        Commits any pending changes to the search index.  Returns an
        UpdateResults instance.
        """
        res = self.update(unicode("\n<commit/>\n", "utf-8"))
        return results.UpdateResults(res)
    
    def optimize(self):
        """
        Optimizes the search index.  Returns an UpdateResults instance.
        """
        res = self.update(unicode("\n<optimize/>\n", "utf-8"))
        return results.UpdateResults(res)
            
    def issue_request(self, url, content=None):
        """
        Submits the specified Unicode content to the specified URL.  Returns
        the raw response content as a string, or None if an error occurs.
        """
        if content: 
            data = content.encode("utf-8", "replace")
        else:
            data = None
        
        (req, res) = (urllib2.Request(url, data), None)
        
        req.add_header("Content-type", "text/xml; charset=utf-8")
        
        try:
            res = urllib2.urlopen(req).read()
        except StandardError, e:
            print str(e)
            logger.error(e)
        return res
    
    def update(self, content):
        """
        Submits the specified Unicode content to Solr's update interface (POST).
        """
        if not content:
            raise ValueError
        
        return self.issue_request(self.update_url, content)
    
    def select(self, *args, **kwargs):
        """
        Submits the specified query to Solr's select interface (GET).
        
        if there are args it's a request.GET, kwargs are from the manager
        which looks like this:
            {'category' : 'news__national'
             'type' : None 
             'author' : None
             'year' : '2008'
             'sort' : 'score desc'}
        """
        
        if args and isinstance(args[0], Query):
            query= args[0]
        else:
            query = Query(*args, **kwargs)
        
        print query.url
        # Submits the response to solr
        response = self.issue_request(self.select_url + "?" + query.url)
    
        return results.SelectResults(response)