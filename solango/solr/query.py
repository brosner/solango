#
# Copyright 2008 Optaros, Inc.
#

"""
Helper class to build queries.

Provides niceties that make building queries easier on the end users.

from solango.solr.query import Query

>>> query = Query({'q' : 'django'})
>>> query.url
'q=the+washington+times'
>>> query.sort = ['date desc', 'relavance desc']
>>> query.facet.fields = ['model', 'date']
>>> query.facet.limit = 100
>>> query.facet.sort = True
>>> query.highlight = 

"""
from solango.solr import utils
from solango.solr.utils import CleverDict
from django.conf import settings
import urllib


class Facet(CleverDict):
    """
    Python class representation of solr's facet capibilites
    
    Date faceting has not been implemented
    
    by default solr assumes
        self.sort = False
        self.offset = 0
        self.limit = 100
        self.mincount = 0
        self.missing = None 
    """
    def __init__(self, *args, **kwargs):
        #if initial data exists then we parse it out and put it in the right fields
        # expects a list of tuples. Facets shouldn't be built directly, only of queries
        # Standard Fields
        self.field = []
        self.queries = []
        CleverDict.__init__(self, *args, **kwargs)

    @property    
    def url(self):
        params = self.as_list()
        return urllib.urlencode(params)

class Highlight(CleverDict):
    """
    Handles the following fields nicely.
        # hl
        # hl.fl
        # hl.snippets
        # hl.fragsize 
    """
    
    def __init__(self, *args, **kwargs):
        #if initial data exists then we parse it out and put it in the right fields
        # expects a list of tuples. Facets shouldn't be built directly, only of queries
        self.simple = CleverDict(instance='simple')
        self.regex = CleverDict(instance='regex')
        self.fl = []
        CleverDict.__init__(self, *args, **kwargs)
    
    @property
    def url(self):
        params = self.as_list()
        return urllib.urlencode(params)

class Query(dict):
    """
    Query Object.
        
    Every request to solr builds a query first. It allows use to pass in 
    default params as well clean the data before we sent it over
    
    The args look something like this when they come in.
        (('category', 'news__national'),
         ('type' , None ),
        ('author',None),
        ('year', '2008'),
        ('sort','score desc'))
    
    Solr Defaults a few values, but here's what has been implemented so far
    and their default values.
        sort: score desc
        start: 0
        rows: 10
        fq (Filter Query): None
        fl (Filter List?): *
        
    Here's how to use it:
    >>> from solango.solr.query import Query
    >>> q = Query('lorem')
    >>> q.url
    'q=lorem'
    
    >>> q = Query([('q', 'lorem'), ('fl', 'model'), ('model', 'example__event')])
    >>> q.url
    'q=lorem+AND+model%3Aexample__event&fl=model'
    
    >>> q = Query({'q' : 'lorem', 'fl' : 'model', 'model': 'test' })
    >>> q.url
    'q=lorem+AND+model%3Aexample__event&fl=model'
    >>> q.facet.facet = True
    >>> q.facet.fields.append('model')
    >>> q.url
    'q=lorem+AND+model%3Atest&fl=model&facet=true&facet.field=model'
    >>> import solango
    >>> solango.connection.select(q)
    <solango.backends.solr.results.SelectResults instance at 0x8795fac>
    """
    
    def __init__(self, *args, **kwargs):
        self.q = []
        self.sort = []
        self.fq = []
        self.fl = []
        self.start = 0
        self.rows = 10
        self.clean(*args, **kwargs)

    #So we can do url.url
    def __getattr__(self, name):
        return self[name]
    #So we can do url.url = '/'
    def __setattr__(self, name, value):
        self[name] = value
    
    def items(self):
        temp_list = []
        for key, value in  super(Query, self).items():
            if isinstance(value, CleverDict):
                temp_list.extend(value.items())
            elif isinstance(value, list):
                temp_list.append((key,value))
            else:
                temp_list.append(('%s' % key, utils._from_python(value)))
        return temp_list

        
    def as_list(self):
        return [(key, value) for key, value in self.items()]

    def clean(self, *args, **kwargs):
        """
        Expects a list of tuples like:
        [('q', 'model'), ('sort', 'date desc'), ('facet.field', 'model')]
        """
        params = []
        if args:
            params = list(args[0].items())
        params.extend(kwargs.items()) 
        
        if not params:
            return None
        
        facet_params = settings.SEARCH_FACET_PARAMS
        hl_params = settings.SEARCH_HL_PARAMS
        for key, value in params:
            if key.startswith('facet'):
                facet_params.append((key, value),)
            elif key.startswith('hl'):
                hl_params.append((key, value),)
            else:
                try:
                    v = self[key]
                    if isinstance(v, list):
                        self[key].append(value)
                    else:
                        self[key] = value
                except KeyError:
                    self.q.append('%s:%s' % (key, value))
        
        self.facet = Facet(facet_params, instance='facet')
        self.hl = Highlight(hl_params, instance='hl')

    @property
    def url(self):
        params = []
        q = False
        for key, value in self.items():
            if not value:
                continue
            if key == 'q':
                params.append( ('q', ' AND '.join(self.q)), )
                q = True
            elif key == 'sort':
                params.append( ('sort', ' '.join(value)), )
            elif isinstance(value, list):
                params.append( (key, ', '.join([x for x in value])), )
            else:
                params.append( (key, value), )

        if not q:
            return ''
                
        query = urllib.urlencode(params)
        
        if self.facet:
            query += '&facet=true'
        if self.hl:
            query += '&hl=true'

        return query
    
