from rest_framework.pagination import (PageNumberPagination,
                                       LimitOffsetPagination)


class LimitOffsetPaginationRecipesParam(PageNumberPagination):
    page_size_query_param = 'recipes_limit'


class PageLimitPagination(LimitOffsetPagination):
    limit_query_param = 'page'
    offset_query_param = 'limit'
