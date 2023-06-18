from django import forms
from .models import OrderInformation
class OrderForm(forms.ModelForm):
    class Meta:
        model = OrderInformation
        fields = ['name', 'email', 'address', 'wilaya', 'numero']
        

from django import forms

class SearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=100)       