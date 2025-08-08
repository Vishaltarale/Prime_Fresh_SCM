from django.shortcuts import render

app_name = "Settings"
# Create your views here.
def settings(request):
    return render(request,'settings.html')