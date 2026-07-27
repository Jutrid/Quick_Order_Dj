from django.shortcuts import render

# Create your views here.

def order_list(request):
    return render(request, 'order_list.html')

def clients_list(request):
    return render(request, 'clients_list.html')

def products_list(request):
    return render(request, 'products_list.html')