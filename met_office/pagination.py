from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.query import QuerySet


class QuerySetPagination:

    def __validate(self):
        if isinstance(self.page, int) is False:
            raise Exception("int required")
        if isinstance(self.per_page, int) is False:
            raise Exception("int required")
        if isinstance(self.queryset, QuerySet) is False:
            raise Exception("queryset required")

    def __init__(self, queryset, per_page, page):
        self.queryset = queryset
        self.per_page = per_page
        self.page = page
        self.__validate()
        self.paginator = Paginator(self.queryset, self.per_page)
        self.total_objects = self.paginator.count
        self.has_next = None

    def get_page(self):
        try:
            page_obj = self.paginator.page(self.page)
        except PageNotAnInteger:
            page_obj = self.paginator.page(1)
        except EmptyPage:
            page_obj = self.paginator.page(self.paginator.num_pages)
        return page_obj

    def paginate_queryset(self):
        page = self.get_page()
        self.has_next = page.has_next()
        return page.object_list
