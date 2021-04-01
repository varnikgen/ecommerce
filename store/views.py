import datetime
import json

from django.http import JsonResponse
from django.shortcuts import render

from store.models import Product, Order, OrderItem, ShippingAddress
from store.utils import cookieCart


def store(request):
    products = Product.objects.all()
    context = {'products': products, 'cartItems': cookieCart(request)['cartItems']}
    return render(request, 'store/store.html', context)


def cart(request):
    return render(request, 'store/cart.html', cookieCart(request))


def checkout(request):
    return render(request, 'store/checkout.html', cookieCart(request))


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('productId:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, completed=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, completed=False)
        total = float(data['form']['total'])
        order.transaction_id = transaction_id

        if total == order.get_cart_total:
            order.completed = True
        order.save()

        if order.shipping:
            ShippingAddress.objects.create(
                customer=customer,
                order=order,
                address=data['shipping']['address'],
                city=data['shipping']['city'],
                state=data['shipping']['state'],
                zipcode=data['shipping']['zipcode'],
            )

    else:
        print('Пользователь не авторизован')
    return JsonResponse('Payment complete!', safe=False)
