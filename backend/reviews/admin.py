from django.contrib import admin

from .models import (Cart, Favorite, Ingredient, IngredientsInRecipe, Recipe,
                     RecipeTag, ShortLinkRecipe, Subscriber, Tag, User)


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'email',
        'username'
    )
    search_fields = ('email', 'last_name')


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'get_favorite_count'
    )
    search_fields = ('name', 'author')
    list_filter = ('tags',)

    def get_favorite_count(self, obj):
        return obj.favorites.count()
    get_favorite_count.short_description = 'Количество в избранном'


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)


admin.site.register(User, UserAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite)
admin.site.register(Subscriber)
admin.site.register(Cart)
admin.site.register(RecipeTag)
admin.site.register(IngredientsInRecipe)
admin.site.register(ShortLinkRecipe)
