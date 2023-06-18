from django.shortcuts import render,redirect
from django.core.mail import send_mail
from django.conf import settings
from produits.models import *
from .models import *

def contact(request):
    if 'Send' in request.POST:
        email = request.POST['email']
        nom = request.POST['nom']
        user = Customer.objects.filter(email=email).exists()
        if not user:

            return render(request, "index.html")
        else:
            message = request.POST['message']
            email_subject = 'Nouveau message '
            send_mail('Nouveau message de contact', message, email,
                      recipient_list=['s_fergui@estin.dz'],
                      fail_silently=False, )
            message = ContactMessage(name=nom, email=email, message=message)
            message.save()
            return render(request, "off.html")
    return render(request, "contact.html")


def ajout (request):
    if 'envoyer' in request.POST:
        nom = request.POST['name']
        email = request.POST['email']
        note = request.POST['rating']
        commentaire = request.POST['commentaire']
        photo = request.FILES.get('photo')
        avis = AvisClient(photo=photo , nom=nom , commentaire=commentaire) 
        avis.save()
        return redirect ('Acceuil')
    return render(request, 'ex.html')