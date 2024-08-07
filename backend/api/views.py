from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView

from reviews.models import (Cart, Favorite, Ingredient, Recipe,
                            ShortLinkRecipe, Subscriber, Tag, User)

from .filters import (CustomSearchFilter, RecipeFilter,
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


class APISetPassword(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = PasswordSetSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('current_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'errors': 'Указан неверный пароль'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class APIUserMe(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user,
                                    context={'request': request})
        return Response(serializer.data)


class APIUserAvatar(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        serializer = UserAvatarSerializer(request.user, data=request.data,
                                          context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.user.is_authenticated is True:
            user = get_object_or_404(User, username=request.user.username)
            serializer = UserAvatarSerializer(user, data={'avatar': None},
                                              partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)


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
    filter_backends = (CustomSearchFilter,)
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


class APIShortLinkRecipe(APIView):
    def get(self, request, pk):
        host = get_current_site(request)
        data = {'recipe': pk,
                'full_link': f'http://{host}/api/recipes/{pk}'}
        serializer = ShortLinkRecipeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        short_link = serializer.data.get('short_link')
        return Response({'short-link': f'http://{host}/{short_link}'})


def redirect_link(request, short_link):
    link = get_object_or_404(ShortLinkRecipe,
                             short_link=short_link)
    return HttpResponseRedirect(link.full_link)


class APIBaseRecipe(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        dct = {'recipe': recipe,
               'user': request.user}
        serializer = self.serializer_name(data=dct,
                                          context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data.get('recipe'),
                            status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        try:
            obj = get_object_or_404(self.model, recipe=recipe,
                                    user=request.user)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({
                'obj': 'Вы не добавляли данный рецепт в список'},
                status=status.HTTP_400_BAD_REQUEST
            )


class APIAddCartRecipe(APIBaseRecipe):

    def __init__(self):
        self.model = Cart
        self.serializer_name = WriteCartRecipeSerializer


class APIAddFavoriteRecipe(APIBaseRecipe):

    def __init__(self):
        self.model = Favorite
        self.serializer_name = WriteFavoriteRecipeSerializer


class APIWriteSubscriber(APIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def post(self, request, pk):
        user = get_object_or_404(User, id=pk)
        serializer = SubscribeToUserSerializer(user,
                                               context={'request': request})
        if not serializer.data.get('errors'):
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data,
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = get_object_or_404(User, id=pk)
        try:
            obj = get_object_or_404(
                Subscriber,
                subscriber=request.user.id,
                subscribed=user.id)
        except Exception:
            return Response({
                'user': 'Вы не подписаны на данного пользователя'},
                status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(None,
                        status=status.HTTP_204_NO_CONTENT)


class ListSubscriptions(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscribeToUserSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        user = self.request.user
        set_of_subscribed = Subscriber.objects.filter(subscriber=user.id)
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
