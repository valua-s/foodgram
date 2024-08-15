from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from reviews.models import (Cart, Favorite, Ingredient, Recipe,
                            ShortLinkRecipe, Subscription, Tag, User)

from .filters import (RecipeFilter, SearchFilterNameParam,
                      get_filter_recipe_queryset)
from .serializers import (CreateListCartSerializer, CreateUserSerializer,
                          IngredientsSerializer, PasswordSetSerializer,
                          ReadRecipeSerializer, ShortLinkRecipeSerializer,
                          SubscribeToUserSerializer, TagSerializer,
                          UserAvatarSerializer, UserSerializer,
                          WriteCartRecipeSerializer,
                          WriteFavoriteRecipeSerializer, WriteRecipeSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
    pagination_class = LimitOffsetPagination
    http_method_names = ['get', 'list', 'post']

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
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        serializer = UserAvatarSerializer(request.user, data={'avatar': None},
                                          partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        if request.method == 'POST':
            serializer = SubscribeToUserSerializer(
                user, context={'request': request})
            if not serializer.data.get('errors'):
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            return Response(serializer.data,
                            status=status.HTTP_400_BAD_REQUEST)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        obj = get_object_or_404(
            Subscription,
            subscriber=request.user.id,
            subscribed=user.id)
        obj.delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)


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


class CreateRecipeViewSet(viewsets.ModelViewSet):
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

    def write_base_cart_favorite(request, pk=None,
                                 class_serializer=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            dct = {'recipe': recipe,
                   'user': request.user}
            serializer = class_serializer(
                data=dct, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data.get('recipe'),
                            status=status.HTTP_201_CREATED)

    def delete_base_cart_favorite(request, pk=None,
                                  model_name=None):
        recipe = get_object_or_404(Recipe, id=pk)
        obj = get_object_or_404(model_name, recipe=recipe,
                                user=request.user)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        return self.write_base_cart_favorite(
            pk=pk, request=request,
            class_serializer=WriteCartRecipeSerializer
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self.delete_base_cart_favorite(
            pk=pk, request=request,
            model_name=Cart
        )

    @action(detail=True, methods=['post'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        return self.write_base_cart_favorite(
            pk=pk, request=request,
            class_serializer=WriteFavoriteRecipeSerializer
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.delete_base_cart_favorite(
            pk=pk, request=request,
            model_name=Favorite
        )


class APIShortLinkRecipe(APIView):
    def get(self, request, pk):
        host = get_current_site(request)
        data = {'recipe': pk,
                'full_link': f'http://{host}/api/recipes/{pk}'}
        serializer = ShortLinkRecipeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        short_link = serializer.data.get('short_link')
        return Response({'short-link': f'http://{host}/s/{short_link}/'})


def redirect_link(request, short_link):
    link = get_object_or_404(ShortLinkRecipe,
                             short_link=short_link)
    return HttpResponseRedirect(link.full_link)


class ListSubscriptions(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscribeToUserSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        user = self.request.user
        set_of_subscribed = Subscription.objects.filter(subscriber=user.id)
        queryset = []
        for subd in set_of_subscribed:
            queryset.append(subd.subscribed)
        return queryset


class APICartListCreate(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = CreateListCartSerializer(
            context={'request': request})
        response = serializer.download_csv()
        return response
