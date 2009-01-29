#
# Copyright 2008 Optaros, Inc.
#

"""
A generic search system which allows configuration of
search document options on a per-model basis.

To use, do two things:

1. Create or import a subclass of ``SearchDocument`` defining the
    options you want.

2. Import ``searchdocument`` from this module and register one or more
    models, passing the models and the ``SearchDocument`` options
    class you want to use.


Example
-------

First, we define a simple model class which might represent entries in
a weblog::
    
    from django.db import models
    
    class Post(models.Model):
        title = models.CharField(maxlength=250)
        body = models.TextField()
        pub_date = models.DateField()
        enable_comments = models.BooleanField()

Then we create a `SearchDocument` subclass specifying some
moderation options::
    
import solango
    
class PostDocument(solango.SearchDocument):
    content = solango.fields.TextField(copy=True, field='body')
    
    #Overrides the default transform
    def transform_content(self, instance):
        return instance.body

And finally register it for searching:
    solango.register(Post, PostDocument)
"""

from django.utils.datastructures import SortedDict
from django.db.models.base import ModelBase, Model
from django.forms.models import model_to_dict
from django.template.loader import render_to_string

from solango import fields as search_fields

from copy import deepcopy

__all__ = ('SearchDocumentBase', 'SearchDocument')

class NoPrimaryKeyFieldException(Exception):
    pass

def get_model_declared_fields(bases, attrs, with_base_fields=True):
    """
    Taken from NewForms
    """
    Meta = attrs.get('Meta', None)
    model = getattr(Meta, 'model', None)
    fields = []
    if isinstance(model, ModelBase):
        for field in model._meta.fields:
            try:
                search_field = getattr(search_fields, field.__class__.__name__)
                fields.append((field.attname, search_field(dynamic=True)),)
            except Exception, e:
                print str(e)
                pass
    fields.extend([(field_name, attrs.pop(field_name)) for field_name, obj in attrs.items() if isinstance(obj, search_fields.Field)])
    fields.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))

    # If this class is subclassing another Form, add that Form's fields.
    # Note that we loop over the bases in *reverse*. This is necessary in
    # order to preserve the correct order of fields.
    if with_base_fields:
        for base in bases[::-1]:
            if hasattr(base, 'base_fields'):
                fields = base.base_fields.items() + fields
    else:
        for base in bases[::-1]:
            if hasattr(base, 'declared_fields'):
                fields = base.declared_fields.items() + fields
    
    for name, field in fields:
        field.name = name
    
    media = attrs.get('Media', None)
    template = getattr(media, 'template', None)
    if template:
        attrs['template'] = template
    
    return SortedDict(fields)


class DeclarativeFieldsMetaclass(type):
    """
    Taken from NewForms
    """
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = get_model_declared_fields(bases, attrs)
        new_class = super(DeclarativeFieldsMetaclass,
                     cls).__new__(cls, name, bases, attrs)
        return new_class

class BaseSearchDocument(object):
    def __init__(self, model_or_dict):
        """
        Takes a model or a dict.
        
        for a model it assumes that you are trying to create a document from the values
        
        for a dict it assumes that you recieved results from solr and you want to make a 
        python object representation of the model    
            
        """
        self.fields = deepcopy(self.base_fields)
        self.pk_field = None
        self._model = None
        self.data_dict = {}
        self.highlight = ""
        
        # If it's a model, set the _model and create a dictionary from the fields
        if isinstance(model_or_dict, Model):
            #make it into a dict.
            self._model = model_or_dict
            self.data_dict = model_to_dict(model_or_dict)
        elif isinstance(model_or_dict, dict):
            self.data_dict = model_or_dict
        else:
            raise ValueError('Argument must be a Model or a dictionary')
        
        # Iterate through fields and get value
        for field in self.fields.values():
            #Save value
            if isinstance(field, search_fields.PrimaryKeyField):
                self.pk_field = field
                break
        
        if not self.pk_field:
            raise NoPrimaryKeyFieldException('Search Document needs a Primary Key Field')
        
        if self._model:
            self.transform()
        else:
            self.clean()
        
    def transform(self):
        """
        Takes an model instance and transforms it into a Search Document
        """
        if not self._model:
            raise ValueError('No model to transform into a Search Document')
        
        for name, field in self.fields.items():
            value = None
            try:
                value = getattr(self, 'transform_%s' % name)(self._model)
                field.value = value
            except AttributeError:
                #no transform rely on the field
                field.transform(self._model)
    
    def clean(self):
        """
        Takes the data dictionary and creates python values from it.
        """
        if not self.data_dict:
            raise ValueError('No data to clean into a Search Document')
        
        for name, field in self.fields.items():
            value = None
            field.value = self.data_dict[field.get_name()]
            try:
                value = getattr(self, 'clean_%s' % name, None)()
                field.value = value
            except:
                #no transform rely on the field
                field.clean()
    
    def __unicode__(self):
        """
        Returns the Solr document XML representation of this Document.
        """
        return self.to_xml()
    
    def delete(self):
        return self.to_xml(True)
    
    def add(self):
        return self.to_xml()
    
    def to_xml(self, delete=False):
        #Delete looks like <id>1</id>
        if delete:
            return "<%s>%s</%s>" % (self.pk_field.name, self.pk_field.value, self.pk_field.name)

        doc = unicode("", "utf-8")
        
        for field in self.fields.values():
            doc += unicode(field)
        
        return "<doc>\n" + doc + "</doc>\n"

    def render_html(self):
        return render_to_string(self.template, {'document' : self})
    
class SearchDocument(BaseSearchDocument):
    id      = search_fields.PrimaryKeyField()
    model   = search_fields.ModelField()
    site_id = search_fields.SiteField()
    url     = search_fields.UrlField()
    text    = search_fields.SolrTextField(multi_valued=True)    
    
    class Media:
        template = 'solango/default_document.html'
        
    __metaclass__ = DeclarativeFieldsMetaclass
    