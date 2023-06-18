from django.db import models 
from django.contrib.auth.models import User


class utilisateur (models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)  
  is_email_verified = models.BooleanField(default=False)

  def __str__(self) :
    return self.user.username