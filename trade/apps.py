from django.apps import AppConfig


#class TradeConfig(AppConfig):
#    name = 'trade'
#from django import forms
#from django.contrib.auth.models import User
#from django.contrib.auth.forms import UserCreationForm
#from .models import Courses,Course_lessons
#
##Creating a form here
#class signup_form(forms.ModelForm):
#    class Meta:
#        model = User
#        fields=['email']
#
#class signin_form(forms.ModelForm):
#    class Meta:
#        model = User
#        fields=['email','password']
#
#class addcourse_form(forms.ModelForm):
#    class Meta:
#        model = Courses
#        fields = ['title','price','description','more','image']
#class create_curriculum_form(forms.Form):
#    name = forms.CharField(max_length=50)
#
#class create_lesson_form(forms.ModelForm):
#    class Meta:
#        model = Course_lessons
#        fields = ['lesson_name','lesson_file','key_points']