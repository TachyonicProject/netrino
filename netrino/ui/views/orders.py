# -*- coding: utf-8 -*-
# Copyright (c) 2018 Dave Kruger.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holders nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
from luxon import router
from luxon import register
from luxon import render_template
from luxon.utils.pkg import EntryPoints
from luxon.utils.bootstrap4 import form
from luxon.utils.timezone import now


from luxon.exceptions import FieldMissing

def first_payment_gateway(product, oid):
    _pay_gws = EntryPoints('netrino.payment.gateways')
    for p in _pay_gws:
        return _pay_gws[p](product, oid)

    return None

def process_notification(req, type, data):
    result = {}

    if req.method == 'POST':
        _pay_gws = EntryPoints('netrino.payment.gateways')
        _pg_name = [p for p in _pay_gws][0]

        payment_gw = _pay_gws[_pg_name]()

        method = getattr(payment_gw, type)

        result = method(req)

        data['price'] = result['product_price']

        order = req.context.api.execute('PUT',
                                        'v1/order/' + result['order_id'],
                                        endpoint='orchestration',
                                        data=data).json

        product = req.context.api.execute('GET',
                                          'v1/product/'
                                          + order['product_id'],
                                          endpoint='orchestration').json

        result['product_name'] = product['name']

    return result

@register.resources()
class Orders():
    def __init__(self):
        router.add('GET',
                   '/order/{pid}',
                   self.setup_order,
                   tag='customer')

        router.add(['GET', 'POST'],
                   '/order/{pid}/{oid}',
                   self.order_product,
                   tag='customer')

        router.add('GET',
                   '/order/{pid}/success',
                   self.activate_product,
                   tag='customer')

        router.add('GET',
                   '/orders',
                   self.orders,
                   tag='customer')

        router.add('POST',
                   '/order/success',
                   self.success)

        router.add(['GET','POST'],
                   '/order/decline',
                   self.decline)

        router.add(['GET', 'POST'],
                   '/order/notify',
                   self.notify)

        router.add(['GET', 'POST'],
                   '/order/redirect',
                   self.redirect)

    def setup_order(self, req, resp, pid):
        if not req.context_tenant_id:
            raise FieldMissing('Tenant', 'Current Tenant',
                               'Please select Tenant for this purchase')

        product = req.context.api.execute('GET',
                                          'v1/product/%s' % pid,
                                          endpoint='orchestration').json

        data = {'product_id': pid,
                'price': product['price']}

        order = req.context.api.execute('POST',
                                        'v1/order',
                                        endpoint='orchestration',
                                        data=data).json


        if len(product['services']):
            ep_name = product['services'][0]['entrypoint']
            _ep = EntryPoints('netrino.product.tasks')[ep_name]
            setup_form = form(_ep.prepare, {})
        else:
            return self.order_product(req, resp, pid, order['id'])


        return render_template('netrino.ui/orders/prepare_order.html',
                               view=product['name'],
                               product=product,
                               order_id=order['id'],
                               form=setup_form)

    def order_product(self, req, resp, pid, oid):
        product = req.context.api.execute('GET',
                                          'v1/product/' + pid,
                                          endpoint='orchestration').json


        if len(req.form_dict):
            data = {'metadata': req.form_dict}

            order = req.context.api.execute('PUT',
                                            'v1/order/' + oid,
                                            endpoint='orchestration',
                                            data=data).json

        # For now just using any payment option available.
        # In the future we'll grab the preferred payment option from
        # settings.ini, and make this the fallback

        payment_gw = first_payment_gateway(product, oid)

        return render_template('netrino.ui/orders/view_product.html',
                               view=product['name'],
                               product=product,
                               id=pid,
                               order_id=oid,
                               payment_gw=payment_gw)

    def activate_product(self, req, resp, pid):
        if not req.context_tenant_id:
            raise FieldMissing('Tenant', 'Current Tenant',
                               'Please select Tenant for this purchase')

        req.context.api.execute('POST',
                                'v1/activate/product/' + pid,
                                endpoint='orchestration')

        return self.orders(req, resp)

    def orders(self, req, resp):
        return render_template('netrino.ui/orders/my_orders.html',
                               view="Coming Soon")

    def success(self, req, resp):
        data = {'status': 'completed',
                'payment_date': now(),
                'metadata': {'gateway_data': req.form_dict}}

        result = process_notification(req, 'success', data)
        result['payment_date'] = data['payment_date']

        return render_template('netrino.ui/orders/success.html',
                               view="Order Received",
                               **result)


    def decline(self, req, resp):
        data = {'status': 'declined',
                'metadata': {'gateway_data': req.form_dict}}

        result = process_notification(req, 'decline', data)

        return render_template('netrino.ui/orders/decline.html',
                               view="Payment Failed", result=result)

    def notify(self, req, resp):
        data = {'status': 'completed',
                'payment_date': now(),
                'metadata': {'gateway_data': req.form_dict}}

        result = process_notification(req, 'notify', data)

        result['payment_date'] = data['payment_date']

        return render_template('netrino.ui/orders/notify.html',
                               view="Notification Received", result=result)

    def redirect(self, req, resp):
        purchase_date = now()

        metadata = {'gateway_data': req.form_dict,
                    'purchase_date': purchase_date}

        data = {'status': 'awaiting payment',
                'metadata': metadata}

        result = process_notification(req, 'redirect', data)

        result['purchase_date'] = purchase_date

        return render_template('netrino.ui/orders/redirect.html',
                               view="Order Received",
                               **result)
