from rest_framework.pagination import PageNumberPagination


class SubRecipePagination(PageNumberPagination):
    page_size_query_param = 'recipes_limit'
    page_query_param = None


class ProjectPagination(PageNumberPagination):
    page_size_query_param = 'limit'
