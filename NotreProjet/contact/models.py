from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AvisClient(models.Model):
    nom = models.CharField(max_length=50)
    commentaire = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    afficher = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='photodeprofil/', default='22.png')

    def __str__(self):
        return self.nom

