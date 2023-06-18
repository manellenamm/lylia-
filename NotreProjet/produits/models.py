from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
				
class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    email = models.CharField(max_length=200)
    
    class Meta:
        verbose_name_plural  = 'Clients'
        
    def __str__(self):
        return self.user.username
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.FloatField()
    image = models.ImageField(upload_to='media/MEDIA_ROOT/products/', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)  # new field for quantity
    CATEGORIE_CHOICES = [
        ('collier', 'Collier'),
        ('bague', 'Bague'),
        ('braclet', 'Braclet'),
        ('montre', 'Montre'),
        ('boucles', 'Boucles'),
        ('totbag_bag', 'Totbag_bag'),
        ('argent', 'Argent'),
        ('parrure','Parrure'),
    ]
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, default='OT')

    def __str__(self):
        return self.name

    def imageURL(self):
        if self.image:
            return self.image.url
        else:
            return ''

    class Meta:
        verbose_name_plural = "Produits"



class ProductOffre(Product):
    ancienprice=models.FloatField()

    class Meta:
        verbose_name_plural = "Offres"


#le panier de l'utilisateur est complete est a vrai lorsque il passe une commande
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)

    def __str__(self):
        if self.customer is not None:
            return str(self.customer.user.username)
        else:
            return "Commande sans client"

    @property
    def shipping(self):
        return True

    @property
    def cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.item_total for item in orderitems])
        return float(total)

    @property
    def cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total 

    class Meta:
        verbose_name_plural = "Panier"


#les informations de la personne qui a passer la commande
class OrderInformation(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=200, blank=True, null=True)
    wilaya = models.CharField(max_length=100, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    est_envoyé = models.BooleanField(default=False)
    est_annullé = models.BooleanField(default=False)

    def __str__(self):
        return str(self.customer) + ' - ' + self.created_at.strftime('%d-%m-%Y %H:%M')

    def cancel_order(self):
        if not self.est_envoyé:
            self.est_annullé = True
            self.save()
            # obtenir la liste de tous les produits associés à la commande annulée
            products = [item.product for item in self.items.all()]
            # ajuster les quantités de chaque produit dans la commande annulée
            for product in products:
                # trouver la quantité associée à chaque OrderItem pour ce produit
                order_items = self.items.filter(product=product)
                quantity_ordered = sum([item.quantity for item in order_items])
                # ajouter cette quantité à la quantité actuelle du produit
                product.quantity += quantity_ordered
                product.save()  # ajouter cet appel à save()

        else:
            raise ValueError("Impossible d'annuler une commande qui a déjà été envoyée.")

    class Meta:
        verbose_name_plural = "Commandes"

#les produits que la personne a commander
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    order_information = models.ForeignKey(OrderInformation, on_delete=models.CASCADE, related_name='items',null=True)
    quantity = models.IntegerField(default=0, null=False, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} ({self.id})"

    @property
    def item_total(self):
        return self.product.price * self.quantity
    class Meta:
        verbose_name_plural = "PanierItem"
        
    def get_product(self):
        return self.product



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'item_total']

class OrderInformationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'name', 'email', 'total', 'created_at', 'est_envoyé', 'est_annullé')
    list_filter = ('est_envoyé', 'est_annullé')
    search_fields = ('customer__username', 'customer__email', 'name', 'email')
    inlines = [OrderItemInline]
    def delete_orders(self, request, queryset):
        for order in queryset:
            order.delete()
            self.message_user(request, "Les commandes sélectionnées ont été supprimées.")
    delete_orders.short_description = "Supprimer les commandes"
    
    def cancel_orders(self, request, queryset):
        for order in queryset:
            order.cancel_order()
            self.message_user(request, "La commande {} a été annulée.".format(order.id))
        return
    cancel_orders.short_description = "Annuler la commande"

    actions = [cancel_orders,delete_orders]

    def mark_as_cancelled(self, request, queryset):
        queryset.update(est_annullé=True)
    mark_as_cancelled.short_description = "Marquer comme annulé"

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def est_annulé(self, obj):
        return obj.est_annullé
    est_annulé.boolean = True
    est_annulé.admin_order_field = 'est_annullé'   
admin.site.register(OrderInformation, OrderInformationAdmin)


class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'date_ordered', 'complete']
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)




    

class Categories(models.Model) :
    chemin_image=models.ImageField(upload_to='imagessssss/')
    legende = models.CharField(max_length=20)
    lien= models.URLField()
    def __str__(self):
        return self.legende
    

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True) 

from django import forms
class ProductSearchForm(forms.Form):
    query = forms.CharField(label='Search Products')    