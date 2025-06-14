from django.http import HttpResponse

def home(request):
    return HttpResponse("<h1>Olá! meu nome é Gabriel Foloni</h1>")
