from .models import Cart


def cart_count(request):
    """Передаёт количество товаров в корзине во все шаблоны."""
    count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            if session_key:
                cart = Cart.objects.filter(session_key=session_key).first()
            else:
                cart = None
        if cart:
            count = cart.total_items
    except Exception:
        pass
    return {'cart_items_count': count}
