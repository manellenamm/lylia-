from collections.abc import Callable, Iterable, Mapping
import threading
from typing import Any
from django.urls import reverse
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from produits.models import Customer
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from produits.views import *
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from .token import *
from base64 import urlsafe_b64encode
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import *




    


################"login view###################
@login_required(login_url='login')
def home(request):
    return render(request, 'produits/templates/Acceuil.html')

################"login view###################
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST.get('password').strip()  
        user = authenticate(request, username=username, password=password)
        
        if user is not None and not user.is_superuser:
            Utilisateur = utilisateur.objects.get(user=user)
            if not Utilisateur.is_email_verified:
                message = "vous n'avez pas vérifier votre email, veuillez consultez votre email"
                return render(request, 'login.html', {'message': message} )
            else:
              login(request, user)
              # Récupérer les informations du panier dans les cookies
            cart = json.loads(request.COOKIES.get('cart', '{}'))
            customer = request.user.customer
            order, created = Order.objects.get_or_create(customer=customer, complete=False)
            for productId, itemData in cart.items():
                product = Product.objects.get(id=productId)
                orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
                orderItem.quantity += itemData['quantity']
                orderItem.save()
            # Effacer le contenu du panier dans le cookie
            response = redirect('Acceuil')
            response.delete_cookie('cart')
            return response 
        
        if not password:
            message = "Veuillez entrer votre mot de passe"
            return render(request, 'login.html', {'message': message})
        
        if user is None :
                  message = " Nom d'utilisateur ou mot de passe  incorrecte ! "
                  return render(request, 'login.html', {'message': message})

        if user.password is None :
                  message = "veuillez entrer votre mot de passe "
                  return render(request, 'login.html', {'message': message})
        
       
        
        if user.is_superuser :
                message = "vous etes l'administrateur de la page , veuillez vous connecter sur votre propre interface "
                return render(request, 'login.html', {'message': message})
        
    else:  
            
     return render(request, 'login.html')




      

from django.contrib.auth.views import PasswordResetView

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html' # nom du template contenant le formulaire de réinitialisation de mot de passe
    email_template_name = 'password_reset_email.html' # nom du template pour l'email de réinitialisation de mot de passe
    success_url = reverse_lazy('password_reset_done') # nom de l'url de la vue 'password_reset_done'


###################register view#######################
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password1 = request.POST.get('password1', None)
        password2 = request.POST.get('password2', None)
        email = request.POST.get('email', None)
        if email is None and password2 is None and password2 is None:
          message="vous n'avez pas vérifier votre email, veuillez  le consulter "
          return render (request,'login.html',{'message': message})
        else:
    
            if password1 != password2:
                message="Les mots de passe ne correspondent pas"
                return render(request, 'register.html', {'message': message})

            if User.objects.filter(username=username).exists():
                message="nom d'utilisateur est déja utilisé"
                return render(request, 'register.html', {'message': message})
            
            # Vérification de l'adresse e-mail
            if User.objects.filter(email=email).exists():
                message='Cet e-mail est déjà utilisé'
                return render(request, 'register.html', {'message': message})

            # Création de l'utilisateur
            user = User.objects.create_user(username=username, email=email, password=password1)
            user.save()
            # Création du customer associé
            customer = Customer.objects.create(user=user, email=email)
            customer.save()
            
            Utilisateur = utilisateur.objects.create(user=user, is_email_verified=False)
            send_activation_email(Utilisateur, request)
            message="vérifiez votre boîte de réception email afin d'activer votre compte"
            return render(request, 'login.html',{'message': message} )

    return render(request, 'register.html')




################logout###############
def logout_view(request):
    logout(request)
    return redirect('Acceuil')




def send_activation_email (Utilisateur, request):
   current_site= get_current_site(request)
   email_subject='Activez votre compte '
   email_body=render_to_string('emailconfirm.html', {'user':Utilisateur.user ,'domain': current_site, 'uid':urlsafe_base64_encode(force_bytes(Utilisateur.pk))
                                                 , 'token':generatorToken.make_token(Utilisateur)})
   

   email=EmailMessage( email_subject,email_body, 'aissoumanel009@gmail.com', to=[Utilisateur.user.email] )
   EmailThread(email).start()

   

def activate_user (request,uidb64,token):
    try :
        uid=force_text(urlsafe_base64_decode(uidb64))
        user=utilisateur.objects.get(pk=uid)
    except  Exception as e:
        user= None

 
    
    if user and generatorToken.check_token(user,token) :
            user.is_email_verified=True
            user.save()
            #message = "Votre compte a été activé. Vous pouvez maintenant vous connecter."
            return redirect(reverse('login'))  
            
   # "message = "Votre compte n'est pas encore activé."
    return redirect(reverse('login'))

    
class EmailThread (threading.Thread) : 
  def __init__(self, email):
      self.email=email
      threading.Thread.__init__(self)
  
  def run(self):
      self.email.send()