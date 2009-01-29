#
# Copyright 2008 Optaros, Inc.
#

from datetime import datetime, date
from time import strptime

class CleverDict(dict):
    """
    Used for Facet, Query and Highlight
    """
    
    def __init__(self, *args, **kwargs):
        dict.__setattr__(self, '_name', kwargs.pop('instance', self.__class__.__name__.lower()))
        self.clean(*args)
        dict.__init__(self, **kwargs)

    #So we can do url.url
    def __getattr__(self, name):
        return self[name]
    #So we can do url.url = '/'
    def __setattr__(self, name, value):
        self[name] = value
    
    def __nonzero__(self):
        if self.items():
            return True
        return False
    
    def items(self):
        temp_list = []
        for key, value in  super(CleverDict, self).items():
            if isinstance(value, CleverDict):
                temp_list.extend([('%s.%s' % (self._name, k), _from_python(v)) for k, v in value.items() if v])
            elif isinstance(value, list):
                temp_list.extend([('%s.%s' % (self._name, key), _from_python(v)) for v in value])
            else:
                temp_list.append(('%s.%s' % (self._name, key), _from_python(value)))
        return temp_list

        
    def as_list(self):
        return [(key, value) for key, value in self.items()]

    def clean(self, *args):
        """
        Expects a list of tuples like:
        [('facet.field', 'model'), (facet.limit, 10)]
        """
        if not args or not isinstance(args[0], list):
            return None
        for key, value in  args[0]:
            if key.startswith(self._name):
                bits = key.split('.')
                if len(bits) is 1:
                    # something like ('facet', True)
                    continue
                try:
                    v = self[bits[1]]
                    if isinstance(v, list):
                        self[bits[1]].append(value)
                    elif isinstance(v, CleverDict):
                        self[bits[1]][bits[2]] = value
                    else:
                        self[bits[1]] = value
                except KeyError:
                    #Doesn't exist yet.
                    self[bits[1]] = value

def _from_python(value):
    """
    Converts python values to a form suitable for insertion into the xml
    we send to solr.
    
    Taken from pySolr
    """
    if isinstance(value, datetime):
        value = value.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    elif isinstance(value, date):
        value = value.strftime('%Y-%m-%dT00:00:00.000Z')
    elif isinstance(value, bool):
        if value:
            value = 'true'
        else:
            value = 'false'
    else:
        value = unicode(value)
    return value
