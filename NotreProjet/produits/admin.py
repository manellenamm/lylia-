from django.contrib import admin

from .models import *
admin.site.register(Customer)
admin.site.register(ProductOffre)
admin.site.register(Product)
admin.site.register(OrderItem)
admin.site.register(Categories)


def cancel_orders(modeladmin, request, queryset):
    for order in queryset:
        if not order.est_envoyé:
            order.cancel_order()
        else:
            modeladmin.message_user(request, "Impossible d'annuler une commande qui a déjà été envoyée.")
cancel_orders.short_description = "Annuler les commandes sélectionnées"

class OrderInformationAdmin(admin.ModelAdmin):
    actions = [cancel_orders]

