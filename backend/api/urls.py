from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router_v_1 = DefaultRouter()
router_v_1.register('users', UserViewSet, basename='users')
router_v_1.register('tags', TagViewSet)
router_v_1.register('ingredients', IngredientViewSet)
router_v_1.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path("", include(router_v_1.urls)),
]
