"""Фабрики тестовых данных.

Выделены отдельно, чтобы каждый TestCase не дублировал подготовку
категорий, продуктов и пользователей. Фабрики не зависят от Factory Boy —
используется минимальный набор функций, чтобы не тянуть лишнюю зависимость
в учебный проект.
"""

from decimal import Decimal

from django.contrib.auth.models import User

from store.models import Category, Product


def make_user(username: str = 'buyer', password: str = 'StrongPass123!') -> User:
    user = User.objects.create_user(
        username=username,
        password=password,
        email=f'{username}@example.com',
    )
    return user


def make_category(name: str = 'Вода', slug: str = 'water') -> Category:
    return Category.objects.create(name=name, slug=slug)


def make_product(
    category: Category,
    name: str = 'Минеральная вода 0.5 л',
    slug: str = 'mineral-water-05',
    price: str = '45.00',
    volume: str = '0.5 л',
    in_stock: bool = True,
) -> Product:
    return Product.objects.create(
        category=category,
        name=name,
        slug=slug,
        price=Decimal(price),
        volume=volume,
        in_stock=in_stock,
    )
