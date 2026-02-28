from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Product, Review, Category


# -----------------------
# CUSTOM USER REGISTRATION FORM
# -----------------------

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone',
            'user_type',
            'password1',
            'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border-slate-200 focus:border-emerald-500 focus:ring-emerald-500 text-sm',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-xl border-slate-200 focus:border-emerald-500 focus:ring-emerald-500 text-sm',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border-slate-200 focus:border-emerald-500 focus:ring-emerald-500 text-sm',
            }),
            'user_type': forms.Select(attrs={
                'class': 'w-full rounded-xl border-slate-200 focus:border-emerald-500 focus:ring-emerald-500 text-sm bg-white',
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'w-full rounded-xl border-slate-200 focus:border-emerald-500 focus:ring-emerald-500 text-sm',
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'w-full rounded-xl border-slate-200 focus:border-emerald-500 focus:ring-emerald-500 text-sm',
            }),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        user.phone = self.cleaned_data.get('phone')
        user.user_type = self.cleaned_data.get('user_type')
        if commit:
            user.save()
        return user


# -----------------------
# PRODUCT FORM (FARMER)
# -----------------------

class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all().order_by('name'),
        empty_label="Select Category",
        widget=forms.Select(attrs={
            'class': 'w-full rounded-xl border-slate-200 text-sm focus:border-emerald-500 focus:ring-emerald-500 bg-white',
        })
    )
    
    class Meta:
        model = Product
        fields = [
            'category',
            'name',
            'description',
            'price',
            'quantity_available',
            'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border-slate-200 text-sm focus:border-emerald-500 focus:ring-emerald-500',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-xl border-slate-200 text-sm focus:border-emerald-500 focus:ring-emerald-500',
                'rows': 3,
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full rounded-xl border-slate-200 text-sm focus:border-emerald-500 focus:ring-emerald-500',
                'step': '0.01',
            }),
            'quantity_available': forms.NumberInput(attrs={
                'class': 'w-full rounded-xl border-slate-200 text-sm focus:border-emerald-500 focus:ring-emerald-500',
                'min': '0',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'w-full text-sm',
            }),
        }


# -----------------------
# REVIEW FORM (BUYER)
# -----------------------

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'w-full rounded-xl border-slate-200 text-sm focus:border-emerald-500 focus:ring-emerald-500',
                'min': '1',
                'max': '5',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full rounded-xl border-slate-200 text-sm focus:border-emerald-500 focus:ring-emerald-500',
                'rows': 3,
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None:
            return rating
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating
