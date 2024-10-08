import csv
import random
import string

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import F
from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS
from rest_framework.validators import UniqueValidator
from reviews.models import (Cart, Favorite, Ingredient, IngredientsInRecipe,
                            Recipe, ShortLinkRecipe, Subscription, Tag, User)

from .fields import Base64ImageField


class CreateUserSerializer(serializers.ModelSerializer):
    username = serializers.RegexField(
        regex=User.USER_REGEX,
        required=True, max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message='this username is already taken')])
    email = serializers.EmailField(
        required=True, max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message='this email is already taken')])
    password = serializers.CharField(write_only=True,
                                     style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')

    def create(self, validated_data):
        return User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            last_name=validated_data['last_name'],
            first_name=validated_data['first_name'],
            password=make_password(validated_data['password'])
        )


class PasswordSetSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={'input_type': 'password'},
                                         required=True)
    current_password = serializers.CharField(style={'input_type': 'password'},
                                             required=True)


class UserSerializer(CreateUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username',
                  'first_name', 'last_name', 'password',
                  'is_subscribed', 'avatar']
        read_only_fields = ('avatar',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.method in SAFE_METHODS and (
            request.user.is_authenticated
        ):
            return Subscription.objects.filter(subscriber=request.user,
                                               subscribed=obj).exists()
        return False


class UserAvatarSerializer(UserSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ['avatar', ]


class TagSerializer(serializers.ModelSerializer):
    slug = serializers.RegexField(
        regex=Tag.SLUG_REGEX,
        required=True, max_length=32,
        validators=[UniqueValidator(queryset=Tag.objects.all(),
                    message='Этот тег уже есть в базе')])

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class TagsForRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class IngredientsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=128,
        validators=[UniqueValidator(queryset=Ingredient.objects.all(),
                    message='Этот ингредиент уже есть в базе')])

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'is_favorited',
            'is_in_shopping_cart',
            'name', 'image', 'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('ingredientsinrecipes__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated) and (
            user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated) and (
            user.carts.filter(recipe=obj).exists()
        )


class WriteIngredientsInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', write_only=True)
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'amount')

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise ValidationError({
                'ingredients': 'Ингредиент не существует'
            })
        return value

    def validate_amount(self, value):
        if value < 1:
            raise ValidationError({
                'amount': 'Количество должно быть больше 0'
            })
        return value


class WriteRecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    ingredients = WriteIngredientsInRecipeSerializer(many=True)
    author = UserSerializer(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author',
            'ingredients',
            'name', 'image', 'text',
            'cooking_time',
        )

    def validate(self, data):
        if 'ingredients' not in data:
            raise ValidationError({
                'ingredients': 'У рецепта должен быть хотя бы 1 ингредиент'
            })
        if 'tags' not in data:
            raise ValidationError({
                'tags': 'У рецепта должен быть хотя бы 1 тег'
            })
        try:
            self.context.get('request').build_absolute_uri()
        except AttributeError:
            raise ValidationError()
        return super().validate(data)

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError(
                'У рецепта должен быть хотя бы 1 ингредиент'
            )
        set_of_ing = {}
        for item in value:
            id = item.get('ingredient')['id']
            amount = item.get('amount')
            set_of_ing[id] = id
            if amount <= 0:
                raise ValidationError({
                    'amount': 'Количество должно быть больше 0'
                })
        if len(value) != len(set_of_ing):
            raise ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться'
            })
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError(
                'У рецепта должен быть хотя бы 1 тег'
            )
        if len(value) != len(set(value)):
            raise ValidationError(
                'Теги не должны повторяться'
            )
        return value

    def create_ingredients_amount(self, ingredients, recipe):
        ingredients_in_recipe = (IngredientsInRecipe(
            ingredient=Ingredient.objects.get(id=ingredient.get(
                'ingredient')['id']),
            recipe=recipe,
            amount=ingredient['amount']
        ) for ingredient in ingredients)
        IngredientsInRecipe.objects.bulk_create(
            ingredients_in_recipe
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients_amount(
            ingredients=ingredients,
            recipe=recipe
        )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        if self.context.get('request').user != instance.author:
            raise PermissionDenied()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(tags)
        self.create_ingredients_amount(recipe=instance,
                                       ingredients=ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ReadRecipeSerializer(instance, context=context).data


class ShortLinkRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShortLinkRecipe
        fields = ('full_link', 'recipe', 'short_link')
        read_only = ('short_link',)
        write_only_fields = ('full_link', 'recipe')

    def short_link(self):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(6))

    def create(self, validated_data):
        try:
            return ShortLinkRecipe.objects.get(
                recipe_id=validated_data['recipe'].id,
                full_link=validated_data['full_link'])
        except ObjectDoesNotExist:
            return ShortLinkRecipe.objects.create(
                recipe=validated_data['recipe'],
                full_link=validated_data['full_link'],
                short_link=self.short_link())


class ReadCartRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image',
                  'cooking_time')
        read_only_fields = ('id', 'name', 'image',
                            'cooking_time')


class RecipeForCartSerializer(ReadRecipeSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class WriteBaseRecipeSerializer(serializers.ModelSerializer):
    recipe = RecipeForCartSerializer(read_only=True)

    def to_internal_value(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if not user:
            raise serializers.ValidationError({
                'user': 'Ошибка получения данных пользователя'
            })
        if not recipe:
            raise serializers.ValidationError({
                'recipe': 'Ошибка получения рецепта'
            })
        try:
            self.Meta.model.objects.get(recipe=recipe,
                                        user=user)
        except ObjectDoesNotExist:
            return {
                'user': user,
                'recipe': recipe
            }
        else:
            raise serializers.ValidationError({
                'errors': 'Данный рецепт уже в списке'
            })

    def create(self, validated_data):
        user = validated_data.get('user')
        recipe = validated_data.get('recipe')
        obj = self.Meta.model.objects.create(
            user=user,
            recipe=recipe
        )
        return obj


class WriteCartRecipeSerializer(WriteBaseRecipeSerializer):

    class Meta:
        model = Cart
        fields = ('recipe',)


class WriteFavoriteRecipeSerializer(WriteBaseRecipeSerializer):

    class Meta:
        model = Favorite
        fields = ('recipe',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('name',)


class SubscribeToUserSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('is_subscribed', 'email', 'username',
                  'first_name', 'last_name', 'recipes',
                  'recipes_count',
                  'avatar')
        read_only_fields = ('email', 'username',
                            'first_name', 'last_name',
                            'avatar')

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        serializer = ReadCartRecipeSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        pass


class CreateSubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('subscriber', 'subscribed')

    def validate(self, data):
        if data['subscriber'] == data['subscribed']:
            raise serializers.ValidationError(
                detail={'errors': "Вы не можете подписаться на себя"}
            )
        if Subscription.objects.filter(
            subscriber=data['subscriber'],
            subscribed=data['subscribed']
        ).exists():
            raise serializers.ValidationError(
                detail={'errors': "Вы уже подписаны на данного пользователя"}
            )
        return data

    def create(self, validated_data):
        return Subscription.objects.create(
            subscribed=validated_data['subscribed'],
            subscriber=validated_data['subscriber'])


class WriteSubscribeToUserSerializer(SubscribeToUserSerializer):

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        subscribed = obj
        subscriber = request.user
        dct = {'subscribed': subscribed.id,
               'subscriber': subscriber.id}
        serializer = CreateSubscribeSerializer(data=dct)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return True


class ReadSubscribeToUserSerializer(SubscribeToUserSerializer):

    def get_is_subscribed(self, obj):
        return True


class CreateListCartSerializer(serializers.Serializer):

    def get_list(self):
        data_of_cart_for_user = Cart.objects.filter(
            user=self.context.get('request').user)
        data_ing_rec = [IngredientsInRecipe.objects.filter(
            recipe=obj.recipe) for obj in data_of_cart_for_user]
        lst_am_ing = []
        for recipes in data_ing_rec:
            for obj in recipes:
                count = False
                serializer = IngredientSerializer(obj.ingredient)
                key = serializer.data['name']
                for d in lst_am_ing:
                    if d.get('ingredient') == key:
                        d['amount'] += obj.amount
                        count = True
                        break
                if not count:
                    lst_am_ing.append(
                        ({'amount': obj.amount,
                          'ingredient': serializer.data['name']}))
        return lst_am_ing

    def download_csv(self):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            'attachment; filename="product_list.csv"')
        writer = csv.writer(response)
        for product in self.get_list():
            writer.writerow([product.get('ingredient'), product.get('amount')])
        return response
