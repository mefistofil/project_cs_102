from django.shortcuts import render,  render_to_response, redirect, get_object_or_404
from .models import OrderItem, Order
from .forms import OrderCreateForm
from cart.cart import Cart
from .tasks import OrderCreated
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.pdfgen import canvas
# import pisa
from io import BytesIO, StringIO


def OrderCreate(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if cart.cupon:
                order.cupon = cart.cupon
                order.discount = cart.cupon.discount
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'],
                                         quantity=item['quantity'])
            cart.clear()

            # Асинхронная отправка сообщения
            OrderCreated.delay(order.id)
            request.session['order_id'] = order.id
            return redirect(reverse('payment:process'))

    form = OrderCreateForm()
    return render(request, 'orders/order/create.html', {'cart': cart,
                                                        'form': form})



# staff_member_required - декоратор, который проверяет, если пользователь зарегистрирован и имеет доступ к
# интерфейсу администратора. Сама же функция AdminOrderDetail() принимает идентификатор заказа и рендерит 
# страницу с этим заказом.
@staff_member_required
def AdminOrderDetail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'admin/orders/order/detail.html', {'order': order})


@staff_member_required
def AdminOrderPDF(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order': order})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename=order_{}.pdf'.format(order.id)
    p = canvas.Canvas(response)
    # result = StringIO.StringIO()
    # pdf = pisa.pisaDocument((html.encode('utf-8')), show_error_as_pdf=True, encoding='UTF-8')
    p.drawString(200, 200, '{}'.format(html))
    # pdf_file = open("%s/%s.pdf" % ( settings.MEDIA_ROOT, html), 'w').write(html)
    p.showPage()
    p.save()
    return response

    
    


# def render_to_pdf(template_src, context_dict):
#     order = get_object_or_404(Order, id=order_id)
#     context = Context(context_dict)
#     html  = template.render(context)
#     result = StringIO.StringIO()
#     pdf = pisa.pisaDocument(StringIO.StringIO(html.encode('utf-8')), result, show_error_as_pdf=True, encoding='UTF-8')
#     if not pdf.err:
#         return result.getvalue()
#     return False


# import weasyprint


# @staff_member_required
# def AdminOrderPDF(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     html = render_to_string('orders/order/pdf.html', {'order': order})
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'filename=order_{}.pdf'.format(order.id)
#     weasyprint.HTML(string=html).write_pdf(response,
#                stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + 'css/bootstrap.min.css')])
#     return response