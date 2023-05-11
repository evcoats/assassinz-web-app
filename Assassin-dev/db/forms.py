from django import forms


class VideoForm(forms.Form):
    video = forms.FileField()
