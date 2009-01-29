#
# Copyright 2008 Optaros, Inc.
#

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from solango import connection
from solango import utils
from solango.paginator import SearchPaginator

def select(request, q=''):
    """
    Issues a select request to the search server and renders any results.
    The query term is derived from the incoming URL, while additional
    parameters for pagination, faceting, filtering, sorting, etc come
    from the query string.
    """
    if not connection.is_available():
        return HttpResponseRedirect(reverse('solango_search_error'))
    
    params = {}
    facets = []
    paginator = None
    sort_links = []
    
    if q:
        params['q'] = q
    
    if request.GET:
        params.update(dict(request.GET.items()))
    
    if params:
        paginator = SearchPaginator(params, request)
        facets = utils.get_facets_links( request, paginator.results)
        sort_links = utils.get_sort_links(request)
        
    return render_to_response("solango/search.html", {'paginator': paginator ,
                                                      'facets' : facets,
                                                      'q' : q,
                                                      'sort_links' : sort_links } , RequestContext(request))