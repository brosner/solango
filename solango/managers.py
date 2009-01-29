#
# Copyright 2008 Optaros, Inc.
#
"""
Allows models to do things like

Post.search.get()
Post.search.all()
Post.search.filter()

"""
from django.db import models
from solango import connection, get_model_key

class SearchManager(models.Manager):
    
    def query(self, *args, **kwargs):
        """
        Usage:
            If using get, all and filter we should give the opition to get documents and not
            other objects. This will cut down on DB queries. Instead give them a model 
            representation.
        
        """
        kwargs['model'] = get_model_key(self.model)
        results = connection.select(*args, **kwargs)
        ids = [doc.pk_field.value for doc in results.documents]
        return self.in_bulk(ids)