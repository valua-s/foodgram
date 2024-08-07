from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from backend.settings import REQUIRED_FIELD_MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField(
        'Электронная почта', unique=True
    )
    username = models.CharField(
        'Ник пользователя', max_length=REQUIRED_FIELD_MAX_LENGTH,
        unique=True)
    first_name = models.CharField(
        'Имя пользователя', max_length=REQUIRED_FIELD_MAX_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия пользователя', max_length=REQUIRED_FIELD_MAX_LENGTH,
    )
    password = models.CharField(
        'Пароль', max_length=REQUIRED_FIELD_MAX_LENGTH,
    )
    avatar = models.ImageField(
        'Аватар', upload_to='media/avatar', null=True,
    )
    role = models.CharField(
        'Роль', max_length=10, default='user'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "пользователи"
        ordering = ['date_joined']

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Tag(models.Model):
    name = models.CharField(
        'Название тега', max_length=32,
        unique=True
    )
    slug = models.SlugField(
        'Слаг Тега', max_length=32,
        unique=True
    )
    REQUIRED_FIELDS = ['name', 'slug']

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "теги"
        ordering = ['name']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        max_length=128,
        unique=True
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        'Название рецепта', max_length=REQUIRED_FIELD_MAX_LENGTH
    )
    text = models.TextField(
        'Описание рецепта'
    )
    cooking_time = models.IntegerField(
        'Время приготовления', validators=[MinValueValidator(1),]
    )
    image = models.ImageField(
        'Изображение рецепта', upload_to='media/recipe'
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientsInRecipe',
        verbose_name='Ингредиенты рецепта',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, through='RecipeTag',
        verbose_name='Теги рецепта',
        related_name='recipes'
    )
    author = models.ForeignKey(
        User, verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    is_favorited = models.BooleanField(
        'В избранном', default=False
    )
    is_in_shopping_cart = models.BooleanField(
        'В списке покупок', default=False
    )
    pub_date = models.DateTimeField(
        'Дата создания', auto_now_add=True
    )
    short_link = models.URLField(
        'Сокращенная ссылка'
    )
    REQUIRED_FIELDS = ['name', 'text',
                       'image', 'cooking_time', 'author', 'pub_date',
                       'short_link']

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = "рецепты"
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('tag', 'recipe'),
                name='unique_tag_recipe'
            )
        ]
        verbose_name = "тег к рецепту"
        verbose_name_plural = "теги к рецепту"

    def __str__(self):
        return f'{self.recipe} с тегом {self.tag}'


class IngredientsInRecipe(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='ingredientsinrecipes')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredientsinrecipes')
    amount = models.IntegerField('Количество ингрединета в рецепте')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_recipe_amount'
            )
        ]
        verbose_name = "ингредиент к рецепту"
        verbose_name_plural = "ингредиенты к рецепту"

    def __str__(self):
        return f'Ингредиент {self.ingredient} к рецепту {self.recipe}'


class ShortLinkRecipe(models.Model):
    short_link = models.CharField('Короткая ссылка',
                                  max_length=20, null=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    full_link = models.URLField('Полная ссылка',
                                max_length=100, default=None)

    class Meta:
        verbose_name = "короткую ссылку"
        verbose_name_plural = "короткие ссылки"

    def __str__(self):
        return f'Ссылка для рецепта {self.recipe}'


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='carts', null=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='carts', null=True)

    class Meta:
        verbose_name = "корзину"
        verbose_name_plural = "корзины"

    def __str__(self):
        return f'{self.user} добавил в корзину {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorites', null=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorites', null=True)

    class Meta:
        verbose_name = "избранное"
        verbose_name_plural = "избранное"

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'


class Subscriber(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='subscribtions', null=True,
                                   verbose_name='Подписавшийся')
    subscribed = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='subscribers', null=True,
                                   verbose_name='Подписка')
    is_subscribe = models.BooleanField(
        'Подписан', default=False
    )

    class Meta:
        verbose_name = "подписку"
        verbose_name_plural = "подписки"

    def __str__(self):
        return f'{self.subscriber} подписался на {self.subscribed}'
