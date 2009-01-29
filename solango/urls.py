#
# Copyright 2008 Optaros, Inc.
#
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',               
    url(r'^$', 'solango.views.select', {}, 'solango_search'),
    url(r'^search-error/$', direct_to_template, {'template': 'solango/error.html'}, 'solango_search_error'),
    url(r'^(?P<q>.*)/$', 'solango.views.select', {}, 'solango_search_term'),
    
)