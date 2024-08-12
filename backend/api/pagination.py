from rest_framework.pagination import PageNumberPagination


class LimitOffsetPaginationRecipesParam(PageNumberPagination):
    page_size_query_param = 'recipes_limit'
