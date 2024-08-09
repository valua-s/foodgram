from django.contrib.auth.models import AbstractUser
from django.core.validators import (MaxValueValidator,
                                    MinValueValidator,
                                    RegexValidator)
from django.db import models
from django.utils.text import slugify

from .constants import REQUIRED_FIELD_MAX_LENGTH, TAG_MAX_LENGTH


class AutoRelatedNameMeta(type):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, models.ForeignKey):
                attr_value.related_name = f"{slugify(name)}s"
            elif isinstance(attr_value, models.ManyToManyField):
                attr_value.related_name = f"{slugify(name)}s"
        return new_class


class BaseModel(models.Model, metaclass=AutoRelatedNameMeta):
    class Meta:
        abstract = True


class User(AbstractUser):
    email = models.EmailField(
        'Электронная почта', unique=True
    )
    username = models.CharField(
        'Ник пользователя', max_length=REQUIRED_FIELD_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message="Используйте только одно слово",
                code="invalid_registration",
            ),
        ])
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
        'Название тега', max_length=TAG_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Слаг Тега', max_length=TAG_MAX_LENGTH,
        unique=True, validators=[
            RegexValidator(
                regex=r'^[-a-zA-Z0-9_]+$',
                message="Используйте символы английского алфавита и цифры",
                code="invalid_registration",
            ),
        ],
        db_index=True
    )

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
        unique=True,
        db_index=True
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"
        ordering = ['name']
        unique_together = ('name', 'measurement_unit',)

    def __str__(self):
        return self.name


class Recipe(BaseModel):
    name = models.CharField(
        'Название рецепта', max_length=REQUIRED_FIELD_MAX_LENGTH
    )
    text = models.TextField(
        'Описание рецепта'
    )
    cooking_time = models.IntegerField(
        'Время приготовления', validators=[MinValueValidator(1),
                                           MaxValueValidator(1440)]
    )
    image = models.ImageField(
        'Изображение рецепта', upload_to='media/recipe'
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientsInRecipe',
        verbose_name='Ингредиенты рецепта'
    )
    tags = models.ManyToManyField(
        Tag, through='RecipeTag',
        verbose_name='Теги рецепта'
    )
    author = models.ForeignKey(
        User, verbose_name='Автор рецепта',
        on_delete=models.CASCADE
    )
    pub_date = models.DateTimeField(
        'Дата создания', auto_now_add=True
    )
    short_link = models.URLField(
        'Сокращенная ссылка'
    )

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


class IngredientsInRecipe(BaseModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
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


class BaseUserRecipeModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             null=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               null=True)


class Cart(BaseModel, BaseUserRecipeModel):

    class Meta:
        verbose_name = "корзину"
        verbose_name_plural = "корзины"
        unique_together = ('user', 'recipe',)

    def __str__(self):
        return f'{self.user} добавил в корзину {self.recipe}'


class Favorite(BaseModel, BaseUserRecipeModel):

    class Meta:
        verbose_name = "избранное"
        verbose_name_plural = "избранное"
        unique_together = ('user', 'recipe',)

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'


class Subscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='subscriptions', null=True,
                                   verbose_name='Подписавшийся')
    subscribed = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='subscribers', null=True,
                                   verbose_name='Подписка')

    class Meta:
        verbose_name = "подписку"
        verbose_name_plural = "подписки"
        unique_together = ('subscriber', 'subscribed',)

    def __str__(self):
        return f'{self.subscriber} подписался на {self.subscribed}'
