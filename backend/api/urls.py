from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (APICartListCreate, APIShortLinkRecipe, CreateRecipeViewSet,
                    IngredientViewSet, ListSubscriptions, TagViewSet,
                    UserViewSet)

router_v_1 = DefaultRouter()
router_v_1.register('users', UserViewSet, basename='users')
router_v_1.register('tags', TagViewSet)
router_v_1.register('ingredients', IngredientViewSet)
router_v_1.register('recipes', CreateRecipeViewSet, basename='recipes')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('users/subscriptions/', ListSubscriptions.as_view()),
    path('recipes/download_shopping_cart/', APICartListCreate.as_view()),
    path('recipes/<int:pk>/get-link/', APIShortLinkRecipe.as_view()),
    path("", include(router_v_1.urls)),
]
