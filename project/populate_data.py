"""
Скрипт для заполнения базы данных тестовыми данными.
Запуск: python manage.py shell < populate_data.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beverage_store.settings')
django.setup()

from store.models import Category, Product
from django.contrib.auth.models import User

# Создать суперпользователя
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@drinkshop.kg', 'admin123')
    print('Суперпользователь создан: admin / admin123')

# Категории
categories_data = [
    {'name': 'Вода', 'slug': 'water', 'description': 'Минеральная и питьевая вода'},
    {'name': 'Соки', 'slug': 'juice', 'description': 'Натуральные и восстановленные соки'},
    {'name': 'Газировка', 'slug': 'soda', 'description': 'Газированные напитки'},
    {'name': 'Чай', 'slug': 'tea', 'description': 'Чай в бутылках и банках'},
    {'name': 'Кофе', 'slug': 'coffee', 'description': 'Кофейные напитки'},
    {'name': 'Энергетики', 'slug': 'energy', 'description': 'Энергетические напитки'},
    {'name': 'Молочные', 'slug': 'dairy', 'description': 'Молочные и кисломолочные напитки'},
]

for cat_data in categories_data:
    cat, created = Category.objects.get_or_create(
        slug=cat_data['slug'],
        defaults=cat_data
    )
    if created:
        print(f'Категория: {cat.name}')

# Товары
products_data = [
    # Вода
    {'category': 'water', 'name': 'Легенда Гор', 'slug': 'legenda-gor', 'price': 45, 'volume': '1.5 л',
     'description': 'Горная минеральная вода из источников Кыргызстана. Чистая, натуральная, с оптимальным балансом минералов.'},
    {'category': 'water', 'name': 'Aqua Bishkek', 'slug': 'aqua-bishkek', 'price': 30, 'volume': '0.5 л',
     'description': 'Питьевая вода высшей категории. Идеальна для ежедневного употребления.'},
    {'category': 'water', 'name': 'Тамчы', 'slug': 'tamchy', 'price': 55, 'volume': '1 л',
     'description': 'Природная минеральная вода из Иссык-Кульской области.'},

    # Соки
    {'category': 'juice', 'name': 'Rich Апельсин', 'slug': 'rich-orange', 'price': 120, 'volume': '1 л',
     'description': 'Восстановленный апельсиновый сок. Насыщенный вкус спелых апельсинов.'},
    {'category': 'juice', 'name': 'Добрый Яблоко', 'slug': 'dobry-apple', 'price': 95, 'volume': '1 л',
     'description': 'Яблочный сок из отборных яблок. Натуральный и освежающий.'},
    {'category': 'juice', 'name': 'J7 Мультифрукт', 'slug': 'j7-multi', 'price': 130, 'volume': '0.97 л',
     'description': 'Нектар из нескольких видов фруктов. Богатый витаминный состав.'},
    {'category': 'juice', 'name': 'Моя Семья Вишня', 'slug': 'moya-semya-cherry', 'price': 85, 'volume': '1 л',
     'description': 'Вишнёвый нектар с мягким вкусом.'},

    # Газировка
    {'category': 'soda', 'name': 'Coca-Cola', 'slug': 'coca-cola', 'price': 70, 'volume': '0.5 л',
     'description': 'Классический газированный напиток с неповторимым вкусом.'},
    {'category': 'soda', 'name': 'Fanta Апельсин', 'slug': 'fanta-orange', 'price': 65, 'volume': '0.5 л',
     'description': 'Газированный напиток с ярким апельсиновым вкусом.'},
    {'category': 'soda', 'name': 'Sprite', 'slug': 'sprite', 'price': 65, 'volume': '0.5 л',
     'description': 'Освежающий газированный напиток со вкусом лимона и лайма.'},
    {'category': 'soda', 'name': 'Шоро Максым', 'slug': 'shoro-maksym', 'price': 50, 'volume': '0.5 л',
     'description': 'Национальный кыргызский напиток из злаков. Традиционный рецепт.'},
    {'category': 'soda', 'name': 'Шоро Чалап', 'slug': 'shoro-chalap', 'price': 55, 'volume': '0.5 л',
     'description': 'Кисломолочный газированный напиток. Освежает в жару.'},

    # Чай
    {'category': 'tea', 'name': 'Fuze Tea Лимон', 'slug': 'fuze-tea-lemon', 'price': 75, 'volume': '0.5 л',
     'description': 'Холодный чай с натуральным лимонным вкусом.'},
    {'category': 'tea', 'name': 'Lipton Персик', 'slug': 'lipton-peach', 'price': 80, 'volume': '0.5 л',
     'description': 'Освежающий холодный чай со вкусом персика.'},
    {'category': 'tea', 'name': 'AriZona Green Tea', 'slug': 'arizona-green', 'price': 140, 'volume': '0.68 л',
     'description': 'Зелёный чай с мёдом и женьшенем. Американский бренд.'},

    # Кофе
    {'category': 'coffee', 'name': 'Nescafé Latte', 'slug': 'nescafe-latte', 'price': 90, 'volume': '0.24 л',
     'description': 'Молочный кофейный напиток. Нежный вкус латте.'},
    {'category': 'coffee', 'name': 'Burn Macchiato', 'slug': 'burn-macchiato', 'price': 110, 'volume': '0.25 л',
     'description': 'Кофейно-молочный напиток с энергетическим эффектом.'},

    # Энергетики
    {'category': 'energy', 'name': 'Red Bull', 'slug': 'red-bull', 'price': 150, 'volume': '0.25 л',
     'description': 'Энергетический напиток. Окрыляет! Содержит кофеин и таурин.'},
    {'category': 'energy', 'name': 'Monster Energy', 'slug': 'monster-energy', 'price': 160, 'volume': '0.5 л',
     'description': 'Мощный энергетический напиток с насыщенным вкусом.'},
    {'category': 'energy', 'name': 'Adrenaline Rush', 'slug': 'adrenaline-rush', 'price': 95, 'volume': '0.25 л',
     'description': 'Энергетический напиток для активного образа жизни.'},

    # Молочные
    {'category': 'dairy', 'name': 'Бишкек Сут Айран', 'slug': 'bishkek-sut-ayran', 'price': 40, 'volume': '0.5 л',
     'description': 'Традиционный кисломолочный напиток. Натуральный состав.'},
    {'category': 'dairy', 'name': 'Кумыс', 'slug': 'kumys', 'price': 80, 'volume': '0.5 л',
     'description': 'Кисломолочный напиток из кобыльего молока. Национальный продукт Кыргызстана.'},
    {'category': 'dairy', 'name': 'Актуаль Персик', 'slug': 'aktual-peach', 'price': 65, 'volume': '0.33 л',
     'description': 'Молочная сыворотка с соком персика. Лёгкий и освежающий напиток.'},
]

categories_map = {c.slug: c for c in Category.objects.all()}

for p_data in products_data:
    cat_slug = p_data.pop('category')
    cat = categories_map[cat_slug]
    product, created = Product.objects.get_or_create(
        slug=p_data['slug'],
        defaults={**p_data, 'category': cat, 'image': f"products/{p_data['slug']}.png"}
    )
    if created:
        print(f'  Товар: {product.name} — {product.price} сом')

print(f'\nГотово! Категорий: {Category.objects.count()}, Товаров: {Product.objects.count()}')
