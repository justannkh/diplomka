from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """Категория напитков (Вода, Соки, Газировка, Чай, Кофе и т.д.)"""
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('URL-имя', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)
    image = models.ImageField('Изображение', upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар (напиток)"""
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE,
        related_name='products', verbose_name='Категория'
    )
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL-имя', max_length=200, unique=True)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField('Цена (сом)', max_digits=10, decimal_places=2)
    volume = models.CharField('Объём', max_length=50, help_text='Например: 0.5 л, 1 л, 330 мл')
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)
    in_stock = models.BooleanField('В наличии', default=True)
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.volume})'


class Cart(models.Model):
    """Корзина покупателя"""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='cart', verbose_name='Пользователь',
        null=True, blank=True
    )
    session_key = models.CharField(
        'Ключ сессии', max_length=40,
        null=True, blank=True
    )
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        if self.user:
            return f'Корзина: {self.user.username}'
        return f'Корзина: сессия {self.session_key}'

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Элемент корзины"""
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE,
        related_name='items', verbose_name='Корзина'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField('Количество', default=1)

    class Meta:
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        unique_together = ('cart', 'product')

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    """Заказ покупателя.

    Помимо контактных данных и статуса доставки, модель хранит параметры
    оплаты: способ (`payment_method`), состояние ("pending/paid/failed")
    и идентификатор транзакции, присваиваемый платёжным шлюзом.
    В текущей реализации используется эмулятор шлюза — поле `transaction_id`
    заполняется UUID-значением, возвращаемым эмулятором. Такая организация
    модели соответствует принципу открытого/закрытого: смена реального шлюза
    потребует изменений только в сервисном слое, но не в структуре данных.
    """

    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]

    PAYMENT_METHOD_COD = 'cod'
    PAYMENT_METHOD_ONLINE = 'online'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_COD, 'Оплата при получении'),
        (PAYMENT_METHOD_ONLINE, 'Онлайн-оплата (тестовая)'),
    ]

    PAYMENT_STATUS_PENDING = 'pending'
    PAYMENT_STATUS_PAID = 'paid'
    PAYMENT_STATUS_FAILED = 'failed'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Ожидает оплаты'),
        (PAYMENT_STATUS_PAID, 'Оплачен'),
        (PAYMENT_STATUS_FAILED, 'Ошибка оплаты'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders', verbose_name='Пользователь'
    )
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    phone = models.CharField('Телефон', max_length=20)
    address = models.TextField('Адрес доставки')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    total_price = models.DecimalField('Итого', max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)
    comment = models.TextField('Комментарий', blank=True)

    # --- Блок оплаты ---
    payment_method = models.CharField(
        'Способ оплаты', max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_COD,
    )
    payment_status = models.CharField(
        'Статус оплаты', max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_PENDING,
    )
    transaction_id = models.CharField(
        'Идентификатор транзакции', max_length=64,
        blank=True, default=''
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.pk} — {self.get_status_display()}'

    @property
    def is_paid(self) -> bool:
        """Признак того, что заказ оплачен (актуален для онлайн-оплаты)."""
        return self.payment_status == self.PAYMENT_STATUS_PAID

    @property
    def requires_online_payment(self) -> bool:
        return self.payment_method == self.PAYMENT_METHOD_ONLINE


class OrderItem(models.Model):
    """Элемент заказа"""
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE,
        related_name='items', verbose_name='Заказ'
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL,
        null=True, verbose_name='Товар'
    )
    product_name = models.CharField('Название товара', max_length=200)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество', default=1)

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'

    @property
    def subtotal(self):
        return self.price * self.quantity
