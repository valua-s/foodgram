from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from reviews.models import (Cart, Favorite, Ingredient, Recipe,
                            ShortLinkRecipe, Subscription, Tag, User)

from .filters import (RecipeFilter, SearchFilterNameParam,
                      get_filter_recipe_queryset)
from .serializers import (CreateListCartSerializer, CreateUserSerializer,
                          IngredientsSerializer, PasswordSetSerializer,
                          ReadRecipeSerializer, ReadSubscribeToUserSerializer,
                          ShortLinkRecipeSerializer, TagSerializer,
                          UserAvatarSerializer, UserSerializer,
                          WriteCartRecipeSerializer,
                          WriteFavoriteRecipeSerializer, WriteRecipeSerializer,
                          WriteSubscribeToUserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    pagination_class = LimitOffsetPagination
    http_method_names = ['get', 'list', 'post', 'put', 'delete']

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return UserSerializer
        return CreateUserSerializer

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = UserSerializer(request.user,
                                    context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        serializer = PasswordSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if user.check_password(serializer.data.get('current_password')):
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Указан неверный пароль'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'],
            permission_classes=(IsAuthenticated,),
            url_path='me/avatar')
    def avatar(self, request):
        serializer = UserAvatarSerializer(request.user, data=request.data,
                                          context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        serializer = UserAvatarSerializer(request.user, data={'avatar': None},
                                          partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        serializer = WriteSubscribeToUserSerializer(
            user, context={'request': request})
        if not serializer.data.get('errors'):
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.data,
                        status=status.HTTP_400_BAD_REQUEST)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        try:
            obj = get_object_or_404(
                Subscription,
                subscriber=request.user.id,
                subscribed=user.id)
        except Exception:
            return Response({'Вы не подписаны на данного пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        subscriptions = user.subscriptions.all()
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = ReadSubscribeToUserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ReadSubscribeToUserSerializer(subscriptions, many=True)
        return Response(serializer.data)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get', 'list']
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    http_method_names = ['get', 'list']
    permission_classes = (AllowAny,)
    filter_backends = (SearchFilterNameParam,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    pagination_class = LimitOffsetPagination
    http_method_names = ['get', 'list', 'post', 'patch', 'delete']
    permission_classes = (IsAuthenticatedOrReadOnly,)
    ordering = ['-pub_date']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return get_filter_recipe_queryset(self)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, pk):
        instance = self.get_object()
        if request.user != instance.author:
            return Response({
                'detail': 'У вас нет прав на данное действие'
            }, status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadRecipeSerializer
        return WriteRecipeSerializer

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method != 'POST':
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dct = {'recipe': recipe,
               'user': request.user}
        serializer = WriteCartRecipeSerializer(
            data=dct, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data.get('recipe'),
                        status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        try:
            obj = get_object_or_404(Cart, recipe=recipe,
                                    user=request.user)
        except Exception:
            return Response({'Вы добавляли элемент в корзину'},
                            status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method != 'POST':
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dct = {'recipe': recipe,
               'user': request.user}
        serializer = WriteFavoriteRecipeSerializer(
            data=dct, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data.get('recipe'),
                        status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        try:
            obj = get_object_or_404(Favorite, recipe=recipe,
                                    user=request.user)
        except Exception:
            return Response({'Вы добавляли элемент в избранное'},
                            status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'],
            permission_classes=(AllowAny,),
            url_path='get-link')
    def short_link(self, request, pk=None):
        host = get_current_site(request)
        data = {'recipe': pk,
                'full_link': f'http://{host}/recipes/{pk}'}
        serializer = ShortLinkRecipeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        short_link = serializer.data.get('short_link')
        return Response({'short-link': f'http://{host}/s/{short_link}/'})

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        serializer = CreateListCartSerializer(
            context={'request': request})
        response = serializer.download_csv()
        return response


def redirect_link(request, short_link):
    """Данный метод используется в backend.url.
    для переадресации коротких ссылок"""
    link = get_object_or_404(ShortLinkRecipe,
                             short_link=short_link)
    return redirect(link.full_link)
