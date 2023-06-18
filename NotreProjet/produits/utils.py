import json
from .models import *
from django.http import JsonResponse

def cookieCart(request):

    #Create empty cart for now for non-logged in user
    try:
        cart = json.loads(request.COOKIES['cart'])
    except:
        cart = {}
        print('CART:', cart)

    items = []
    order = {'cart_total':0, 'cart_items':0, 'shipping':False}
    cartItems = 0

    for i in cart:
        #We use try block to prevent items in cart that may have been removed from causing error
        try:
            quantity = cart[i]['quantity'] if cart[i]['quantity'] > 0 else 0 #items with negative quantity = lot of freebies  
            cartItems += quantity

            product = Product.objects.get(id=i)
            stock_quantity = product.quantity
            requested_quantity = quantity

            item_limit_msg = ""
            # Limit the quantity to the available stock if it exceeds the stock quantity
            if not request.user.is_authenticated and requested_quantity > stock_quantity:
                cart[i]['quantity'] = stock_quantity
                item_limit_msg = f"Quantity limited to {stock_quantity} due to stock availability."
                
            total = (product.price * quantity)

            order['cart_total'] += total
            order['cart_items'] += quantity

            item = {
                'id':product.id,
                'product':{'id':product.id,'name':product.name, 'price':product.price, 
                'imageURL':product.imageURL}, 
                'quantity':quantity,
                'get_total':total,
                'limit_msg': item_limit_msg,
            }
            items.append(item)
        except:
            pass
            
    return {'cartItems':cartItems ,'order':order, 'items':items}

def cartData(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()
        cartItems = order.cart_items

        # Vérifier les quantités en stock pour chaque produit dans le panier
        for item in items:
            product = item.product
            stock_quantity = product.quantity
            requested_quantity = item.quantity

            # Limiter la quantité à la quantité en stock si elle dépasse la quantité disponible
            max_quantity = min(stock_quantity, requested_quantity)
            if max_quantity != requested_quantity:
                item.quantity = max_quantity
                item.save()
    else:
        cookie_cart = json.loads(request.COOKIES.get('cart', '{}'))
        items = []
        order = {'cart_total':0, 'cart_items':0}
        cartItems = order['cart_items']

        for i in cookie_cart:
            try:
                product = Product.objects.get(id=i)
                quantity = cookie_cart[i]['quantity']
                if(quantity>product.quantity):
                    quantity=product.quantity
                total = (product.price * quantity)

                order['cart_total'] += total
                order['cart_items'] += quantity

                item = {
                    'product':{
                        'id':product.id,
                        'name':product.name,
                        'price':product.price,
                        'imageURL':product.imageURL,
                    },
                    'quantity':quantity,
                    'get_total':total,
                }
                items.append(item)

            except:
                pass

        cartItems = order['cart_items']

        # Enregistrer le contenu du panier mis à jour dans le cookie
        response = JsonResponse({'message': 'Item was added'}, status=200)
        response.set_cookie('cart', json.dumps(cookie_cart))

    return {'cartItems': cartItems, 'order': order, 'items': items}
