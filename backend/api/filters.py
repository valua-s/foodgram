import django_filters
from rest_framework.filters import SearchFilter
from reviews.models import Cart, Favorite, Recipe


class SearchFilterNameParam(SearchFilter):
    search_param = "name"


def get_filter_recipe_queryset(self):
    queryset = Recipe.objects.all()
    user = self.request.user
    is_favorited = self.request.GET.get('is_favorited')
    is_in_shopping_cart = self.request.GET.get('is_in_shopping_cart')
    if is_favorited and user.is_authenticated:
        objs = Favorite.objects.filter(user=user)
        recipe_ids = objs.values_list('recipe_id', flat=True)
        queryset = queryset.filter(id__in=recipe_ids)
    if is_in_shopping_cart and user.is_authenticated:
        objs = Cart.objects.filter(user=user)
        recipe_ids = objs.values_list('recipe_id', flat=True)
        queryset = queryset.filter(id__in=recipe_ids)
    tag_ids = self.request.query_params.getlist('tags')
    if tag_ids:
        queryset = queryset.filter(tags__slug__in=tag_ids).distinct()
    return queryset


class RecipeFilter(django_filters.FilterSet):

    class Meta:
        model = Recipe
        fields = ['author', ]
