// ============================================
// DrinkShop — JavaScript (AJAX-корзина, тосты)
// ============================================

document.addEventListener('DOMContentLoaded', function() {

    // --- CSRF-токен для Django ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // --- Toast-уведомления ---
    function showToast(message) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add('toast--visible');
        setTimeout(function() {
            toast.classList.remove('toast--visible');
        }, 2500);
    }

    // --- Обновить бейдж корзины ---
    function updateCartBadge(count) {
        const badge = document.getElementById('cart-badge');
        if (badge) {
            badge.textContent = count;
        }
    }

    // --- AJAX: Добавить в корзину ---
    document.querySelectorAll('.add-to-cart').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.success) {
                    updateCartBadge(data.cart_count);
                    showToast(data.message);
                }
            })
            .catch(function(err) {
                console.error('Ошибка добавления в корзину:', err);
                showToast('Ошибка! Попробуйте ещё раз.');
            });
        });
    });

});
