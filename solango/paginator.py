#
# Copyright 2008 Optaros, Inc.
#
from solango import connection
from solango import utils

class SearchPaginator(object):
    """
    Pagination. 
    
    Object that helps with search pagination. 
    
    Few Notes. To keep track of the request params the Paginator has a few extra 
    params than the normal Paginator. 
    
    * next_link
        * If paginator.has_next() than use paginator.next_link to keep state
    * previous_link
        * If paginator.has_previous() than use paginator.previous_link to keep state
    * results
        * An instance of SelectResults
    
    Template use:
        {% if paginator.has_previous %}
            <a href="{{ paginator.previous_link }}">&lt;&lt;</a> | 
        {% endif %}
        {% for link in paginator.links %}
            {% if link.href %}
                <a href="{{ link.href }}">{{ link.anchor }}</a> |
            {% else %}
                {{ link }} |
            {% endif %}
        {% endfor %}
        {% if paginator.has_next %}
            <a href="{{ paginator.next_link }}">&gt;&gt;</a>
        {% endif %}
    """
    
    def __init__(self, params, request):
        self.page = int(params.pop('page', 1))
        self.per_page = int(params.pop('per_page', 5))
        params['start'] = (self.page-1  ) * self.per_page
        params['rows'] = self.per_page
        self.results = connection.select(params)
        self.next_link = None
        self.previous_link = None
        self.links = []
        self._get_pagination_links(request)
    
    def _get_pagination_links(self, request):
        base = utils.get_base_url(request,["page",])
        
        links = []
        
        for i in self.page_range():
            
            if i == self.page:
                links.append(str(i))
                continue
            
            if i == 1:
                link = {"anchor": str(i), "href": base.rstrip('?')}
            else:
                link = {"anchor": str(i), "href": base + "page=" + str(i)}
            
            links.append(link)
            
        if self.has_next:
            self.next_link = base + "page=" + str(self.page+1)
            
        if self.has_previous:
            if self.page == 2:
                self.previous_link = base.rstrip('?')
            else:
                self.previous_link = base + "page=" + str(self.page-1)
        
        self.links = links

    
    def has_next(self):
        return self.results.start + self.results.rows < self.results.count
    
    def has_previous(self):
        return 0 < self.results.start
    
    def page_range(self):
        return range(1, (self.results.count / self.results.rows + 2))
    
    def has_other_pages(self):
        return self.has_previous() or self.has_next()
    
    def next_page_number(self):
        return self.page + 1
    
    def previous_page_number(self):
        return self.page - 1
    
    def page_count(self):
        return  (self.results.count % self.results.rows + 1)
    
    def facets(self):
        return self.results.facets
    
    def documents(self):
        return self.results.documents