from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from shop import views as shop_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Основні сторінки магазину
    path('', include('shop.urls')),

    # Користувацькі маршрути
    path('register/', shop_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='shop:home'), name='logout'),
    path('profile/', shop_views.profile, name='profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
