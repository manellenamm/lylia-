from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
from django.conf import settings
import datetime
from django.contrib.auth.decorators import login_required
from .utils import cookieCart, cartData
from .forms import OrderForm
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.core.signals import request_finished
from django.db.models.signals import post_save
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from contact.models import *

################ la page d'accueil:##############################

def Acceuil(request):
    products = ProductOffre.objects.all()
    for product in products:
        product.pk = product.id  # Ajouter l'attribut pk pour chaque produit

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    avis = AvisClient.objects.filter(afficher=True)
    mon_modele=Categories.objects.all()
    context = {
        'products': products, 
        'cartItems': cartItems, 
        'avis': avis , 
        'mon_modele':mon_modele
    }
    return render(request, 'Acceuil.html', context)

############### "la page du panier###########################
@login_required
def cart(request):
    # Récupérer les données du panier
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    # Récupérer le contenu du panier stocké dans le cookie
    cart = json.loads(request.COOKIES.get('cart', '{}'))
    # Parcourir chaque produit dans le panier cookie
    for productId, itemData in cart.items():
        product = Product.objects.get(id=productId)
        quantity_in_cart = itemData['quantity']
        quantity_available = product.quantity

        # Si l'utilisateur est connecté, ajouter l'article à l'objet Order existant
        if request.user.is_authenticated:
            orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
            total_quantity = orderItem.quantity + itemData['quantity']
            # Ajouter la quantité de l'article dans le panier de session à la quantité de l'article dans l'objet Order
            if total_quantity > quantity_available:
                # Si la quantité totale est supérieure à la quantité disponible en stock, ajuster la quantité dans le panier.
                quantity_to_add = quantity_available - orderItem.quantity
                orderItem.quantity = quantity_available
                orderItem.save()
            else:
                quantity_to_add = itemData['quantity']
                orderItem.quantity = total_quantity
                orderItem.save()
            # Ajouter la quantité de l'article dans le panier de session à la quantité de l'article dans l'objet Order
            existing_item = None
            for item in items:
                if item.product.id == product.id:
                    existing_item = item
                    break
            if existing_item:
                existing_item.quantity += quantity_to_add
                existing_item.save()
            else:
                new_item = OrderItem.objects.create(
                    product=product,
                    order=order,
                    quantity=quantity_to_add
                )
                items.append(new_item)
        # Si l'utilisateur n'est pas connecté, ajouter l'article dans le panier de session
        else:
            existing_item = None
            for item in items:
                if item.product.id == product.id:
                    existing_item = item
                    break
            if existing_item:
                existing_item.quantity += itemData['quantity']
                existing_item.save()
            else:
                new_item = OrderItem.objects.create(
                    product=product,
                    order=order,
                    quantity=itemData['quantity']
                )
                items.append(new_item)

    # Si l'utilisateur est connecté, enregistrer les modifications de l'objet Order dans la base de données
    if request.user.is_authenticated:
        order.save()
    # Sinon, mettre à jour le panier de session
    else:
        request.session['cart'] = cart

    # Effacer le contenu du panier dans le cookie
    response = render(request, 'cart.html', {'items': items, 'order': order, 'cartItems': cartItems})
    response.delete_cookie('cart')

    return response

#################### update product################################
def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer if request.user.is_authenticated else None
    product = get_object_or_404(Product, id=productId)
    
    # Vérifier la quantité en stock du produit
    if product.quantity <= 0:
        messages.error(request, 'Out of stock!!!')
        response_data = {'error': 'Out of stock'}
        return JsonResponse(response_data, status=400)

    # Si l'utilisateur est connecté, ajouter l'article dans le panier en limitant la quantité à la quantité maximale disponible en stock
    if customer:
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
        
        if action == 'add':
            if orderItem.quantity < product.quantity:
                orderItem.quantity += 1
            else:
                messages.error(request, 'Out Of Stock!!!')
                response_data = {'error': 'Out Of Stock'}
                return JsonResponse(response_data, status=400)
        elif action == 'remove':
            orderItem.quantity -= 1
        orderItem.save()

        if orderItem.quantity <= 0:
            orderItem.delete()

    # Si l'utilisateur n'est pas connecté, ajouter l'article dans le cookie panier 
    else:
        cart = json.loads(request.COOKIES.get('cart', '{}'))
        cartItems = cart.get(str(product.id), None)

        if action == 'add':
            if cartItems:
                quantity_in_cart = cartItems['quantity']
                quantity_available = product.quantity
                if quantity_in_cart < quantity_available:
                    cartItems['quantity'] += 1
                else:
                    messages.error(request, 'Out Of Stock!!!')
                    response_data = {'error': 'Out Of Stock'}
                    return JsonResponse(response_data, status=400)
            else:
                cartItems = {'quantity': 1}
                cart[str(product.id)] = cartItems

        elif action == 'remove':
            if cartItems and cartItems['quantity'] > 0:
                cartItems['quantity'] -= 1
                if cartItems['quantity'] == 0:
                    del cart[str(product.id)]

        response = JsonResponse({'message': 'Item was added'}, status=200)
        response.set_cookie('cart', json.dumps(cart))
        return response

    response_data = {'message': 'Item was added'}
    return JsonResponse(response_data, status=200)

################## la page de  commande ##########################
@login_required
def checkout(request):
    # Récupérer les informations du panier enregistrées dans la session utilisateur
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    if request.method == 'POST':
        form = OrderForm(request.POST)

        if form.is_valid():
            # Créer une nouvelle instance du modèle OrderInformation pour stocker les informations de la commande
            order_information = form.save(commit=False)
            order_information.customer = request.user
            order_information.total = order.cart_total
            order_information.save()

            # Récupérer les informations sur les produits à partir de la session
            product_list = []
            order = Order.objects.filter(
                customer=request.user.customer, complete=False).first()
            if order:
                order_items = order.orderitem_set.all()
                for item in order_items:
                    product_list.append(
                        {'product': item.product, 'quantity': item.quantity})
                print(product_list)
                # Mettre à jour la quantité des produits dans la base de données
                for item in product_list:
                    product = item['product']
                    quantity_ordered = item['quantity']
                    product.quantity -= quantity_ordered
                    product.save()
                    if product.quantity <= 0:
                        product.delete()

                for item in product_list:
                    order_item = OrderItem.objects.create(
                        product=item['product'],
                        quantity=item['quantity'],
                    )
                    order_information.items.add(order_item)

                # Mettre à jour la commande et supprimer le panier de la session(pour les wilayas )
                order.complete = True
                order.save()
                if order.complete:
                    # rediriger vers la page de confirmation de commande
                    return redirect(reverse('order_confirmation', args=[order_information.id]))
                
        else:
                print("ERROR")
    else:
        form = OrderForm()

    context = {'form': form, 'items': items,
               'order': order, 'cartItems': cartItems, }
    return render(request, 'checkout.html', context)

#####################la confirmation de la commande~###################
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def order_confirmation(request, order_info_id):
    order_info = OrderInformation.objects.get(id=order_info_id)
    context = {'order_info': order_info}
    html_message = render_to_string('commande.html', context)
    plain_message = strip_tags(html_message)
    from_email = 's_fergui@estin.dz' # l'adresse e-mail à partir de laquelle vous souhaitez envoyer l'e-mail
    to_email = order_info.email
    subject = 'Confirmation de commande'
    send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)
    return render(request, 'commande.html', context)

def bagues(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    bague = Product.objects.filter(categorie='bague')
    context = {'bague': bague,'cartItems': cartItems }
    return render(request, 'bagues.html', context)


def boucles(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    boucle = Product.objects.filter(categorie='boucles')
    context = {'boucle': boucle, 'cartItems': cartItems  }
    return render(request, 'boucles.html', context)


def montres(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    montre = Product.objects.filter(categorie='montre')
    context = {'montre': montre, 'cartItems': cartItems  }
    return render(request, 'montres.html', context)


def Bracelets(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    bracelet = Product.objects.filter(categorie='braclet')
    context = {'bracelet': bracelet,  'cartItems': cartItems }
    return render(request, 'bracelets.html', context)


def Colliers(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    Collier = Product.objects.filter(categorie='collier')
    context = {'Collier': Collier, 'cartItems': cartItems  }
    return render(request, 'colliers.html', context)




 

def Argent(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    argent = Product.objects.filter(categorie='argent')
    context = {'argent': argent,  'cartItems': cartItems }
    return render(request, 'argent.html', context)

def Parrure(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    parrure = Product.objects.filter(categorie='parrure')
    context = {'parrure': parrure,  'cartItems': cartItems }
    return render(request, 'parrure.html', context)


from django.shortcuts import redirect, get_object_or_404


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if created:
        messages.success(request, "Le produit a été ajouté à votre liste de souhaits.")
    else:
        messages.warning(request, "Ce produit est déjà dans votre liste de souhaits.")
    
    # Récupérer l'URL précédente de la requête
    prev_url = request.META.get('HTTP_REFERER')
    
    # Rediriger vers l'URL précédente
    return redirect(prev_url)
from django.shortcuts import redirect, get_object_or_404
from .models import Product, Wishlist

@login_required
def wishlist(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    wishlist_items = Wishlist.objects.filter(user=request.user)
    context = {'wishlist_items': wishlist_items,'cartItems': cartItems }
    return render(request, 'wishlist.html', context)


def remove_from_wishlist(request, item_id):
    item = get_object_or_404(Wishlist, id=item_id)
    item.delete()
    return redirect('wishlist')



from django.db.models import Q
from .forms import SearchForm
def search(request):
    query = request.GET.get('query')
    results = []
    if query:
        results = Product.objects.filter(name__icontains=query)
    context = {
        'query': query,
        'results': results,
        'form': SearchForm(),
    }
    return render(request, 'search.html', context)

from django.shortcuts import render

def error_404(request, exception):
    return render(request, '404.html', status=404)



