from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .forms import RegisterForm, LoginForm, OrderForm
from .payments import get_default_gateway


# ======================== Утилиты ========================

def _get_or_create_cart(request):
    """Получить или создать корзину для текущего пользователя/сессии."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, created = Cart.objects.get_or_create(
        session_key=session_key, user__isnull=True
    )
    return cart


def _merge_cart_on_login(request, user):
    """При логине — объединить анонимную корзину с корзиной пользователя."""
    session_key = request.session.session_key
    if not session_key:
        return
    try:
        anon_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
    except Cart.DoesNotExist:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)
    for item in anon_cart.items.all():
        existing = user_cart.items.filter(product=item.product).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
        else:
            item.cart = user_cart
            item.save()
    anon_cart.delete()


# ======================== Каталог ========================

def index(request):
    """Главная страница — каталог товаров."""
    categories = Category.objects.all()
    products = Product.objects.filter(in_stock=True)

    # Фильтр по категории
    category_slug = request.GET.get('category')
    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=current_category)

    # Поиск
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Сортировка
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')

    context = {
        'categories': categories,
        'products': products,
        'current_category': current_category,
        'query': query,
        'sort': sort,
    }
    return render(request, 'store/index.html', context)


def product_detail(request, slug):
    """Страница товара."""
    product = get_object_or_404(Product, slug=slug)
    related = Product.objects.filter(
        category=product.category, in_stock=True
    ).exclude(pk=product.pk)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
    })


# ======================== Корзина ========================

def cart_view(request):
    """Страница корзины."""
    cart = _get_or_create_cart(request)
    return render(request, 'store/cart.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    """Добавить товар в корзину (AJAX)."""
    product = get_object_or_404(Product, pk=product_id, in_stock=True)
    cart = _get_or_create_cart(request)

    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product,
        defaults={'quantity': 1}
    )
    if not created:
        item.quantity += 1
        item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.total_items,
            'message': f'«{product.name}» добавлен в корзину',
        })
    messages.success(request, f'«{product.name}» добавлен в корзину')
    return redirect('store:cart')


@require_POST
def cart_update(request, item_id):
    """Обновить количество товара в корзине."""
    item = get_object_or_404(CartItem, pk=item_id)
    cart = item.cart

    # Проверка принадлежности корзины
    if request.user.is_authenticated:
        if cart.user != request.user:
            return JsonResponse({'success': False}, status=403)
    else:
        if cart.session_key != request.session.session_key:
            return JsonResponse({'success': False}, status=403)

    action = request.POST.get('action', '')
    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
        else:
            item.delete()
    elif action == 'remove':
        item.delete()

    return redirect('store:cart')


# ======================== Заказ ========================

def checkout(request):
    """Оформление заказа."""
    cart = _get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, 'Корзина пуста')
        return redirect('store:cart')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.total_price = cart.total_price
            order.payment_method = form.cleaned_data['payment_method']
            order.payment_status = Order.PAYMENT_STATUS_PENDING
            order.save()

            # Перенести товары из корзины в заказ
            for cart_item in cart.items.select_related('product'):
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity,
                )
            # Очистить корзину
            cart.items.all().delete()

            # Обработка оплаты. Разделение способов намеренно сделано на
            # стороне view, а не модели: это позволяет в будущем вынести
            # онлайн-оплату в отдельный шаг (redirect → платёжная форма →
            # webhook) без изменений модели.
            if order.payment_method == Order.PAYMENT_METHOD_ONLINE:
                gateway = get_default_gateway()
                result = gateway.charge(
                    amount=order.total_price,
                    order_id=order.pk,
                    card_number=form.cleaned_data.get('card_number') or None,
                )
                order.transaction_id = result.transaction_id
                if result.success:
                    order.payment_status = Order.PAYMENT_STATUS_PAID
                    order.status = 'processing'
                    messages.success(
                        request,
                        f'Заказ #{order.pk} оплачен. {result.message}'
                    )
                else:
                    order.payment_status = Order.PAYMENT_STATUS_FAILED
                    messages.error(
                        request,
                        f'Оплата не прошла: {result.message} '
                        f'Заказ #{order.pk} сохранён со статусом «Ошибка оплаты».'
                    )
                order.save(update_fields=[
                    'payment_status', 'transaction_id', 'status'
                ])
            else:
                messages.success(
                    request,
                    f'Заказ #{order.pk} оформлен. '
                    'Оплата будет произведена при получении.'
                )

            return redirect('store:order_success', order_id=order.pk)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            }
        form = OrderForm(initial=initial)

    return render(request, 'store/checkout.html', {
        'form': form,
        'cart': cart,
    })


def order_success(request, order_id):
    """Страница успешного заказа."""
    order = get_object_or_404(Order, pk=order_id)
    # Заказ с привязкой к пользователю виден только владельцу.
    # Анонимный заказ (order.user is None) виден любому по прямой ссылке —
    # это нужно, чтобы показать страницу сразу после оформления.
    if order.user and order.user != request.user:
        from django.http import Http404
        raise Http404
    return render(request, 'store/order_success.html', {'order': order})


@login_required
def order_history(request):
    """История заказов пользователя."""
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/order_history.html', {'orders': orders})


# ======================== Авторизация ========================

def register_view(request):
    """Регистрация."""
    if request.user.is_authenticated:
        return redirect('store:index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            _merge_cart_on_login(request, user)
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('store:index')
    else:
        form = RegisterForm()
    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    """Вход."""
    if request.user.is_authenticated:
        return redirect('store:index')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            _merge_cart_on_login(request, user)
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            next_url = (request.POST.get('next')
                        or request.GET.get('next')
                        or 'store:index')
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'store/login.html', {'form': form})


def logout_view(request):
    """Выход."""
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('store:index')
