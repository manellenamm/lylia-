
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from connection.views import *
from contact.views import contact
from produits.views import *
from django.contrib.auth import views as auth_views
from django.conf.urls import handler404
from django.views import defaults as default_views
from contact.views import *
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    path('contact/', contact, name='contact'),
    path('', Acceuil, name="Acceuil"),
    path('cart/', cart, name="cart"),
    path('checkout/', checkout, name="checkout"),
    path('update_item/', updateItem, name="update_item"),
    path('commande/confirmation/<int:order_info_id>/', order_confirmation, name='order_confirmation'),
    path('bagues/', bagues),
    path('boucles/', boucles),
    path('montres/', montres),
    path('bracelets/', Bracelets),
    path('colliers/',Colliers),
     path('reset_password/', CustomPasswordResetView.as_view(), name="password_reset"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="password_reset_sent.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_done.html"), name="password_reset_complete"),
    path('ajout/', ajout, name="ajout"),
    path('argent/',Argent),
    path('parrure/',Parrure),
    path('search/', search, name='search'),
    path('add_to_wishlist/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('remove_from_wishlist/<int:item_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/', wishlist, name='wishlist'),
    path('activate_user/<uidb64>/<token>',  activate_user , name="activate_user"),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler404 = 'produits.views.error_404'

