from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Trades

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
class NewTradeForm(forms.ModelForm):
    class Meta:
        model = Trades
        fields = [
        'pair','momentum_h4','momentum_h1','momentum_15m',
        'momentum_5m','momentum_1m','entry_place',
        'buy_or_sell','setup_quality','trade_type','confirmation',
        'mood','tp','tp_reason','risk_reward',]

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["momentum_h4"].required=False
        self.fields["momentum_h1"].required=False
        self.fields["momentum_15m"].required=False
        self.fields["momentum_5m"].required=False
        self.fields["momentum_1m"].required=False    


class TradeUpdateForm(forms.ModelForm):
    class Meta:
        model = Trades
        fields = [
        "target","reason","holding_time_hrs","holding_time_mns","narration"
        ]
    
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].required=False

    def clean(self):
        cleaned_data = super().clean()

        # Optional: enforce target validation
        target = cleaned_data.get("target")
        if target not in [0, 1, None]:
            raise forms.ValidationError("Target must be 0 or 1")

        return cleaned_data