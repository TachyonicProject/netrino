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
from luxon import g
from luxon import js
from luxon import router
from luxon import register
from luxon import render_template
from luxon.utils.pkg import EntryPoints
from luxon.utils.bootstrap4 import form
from luxon.utils.timezone import now

from luxon.exceptions import FieldMissing, JSONDecodeError, HTTPError

g.nav_menu.add('/Billing/My Orders',
               href='/orders',
               tag='customer',
               endpoint='orchestration',
               feather='package')

def get_payment_gateways(product):
    pmt_gws = []
    if 'custom_attributes' in product:
        for ca in product['custom_attributes']:
            if ca['name'] == 'payment_gateway':
                pmt_gws.append(ca['value'])

    return pmt_gws


def process_notification(req, type, data):
    result = {}

    if req.method in ('PUT', 'POST',):
        _pay_gws = EntryPoints('netrino.payment.gateways')
        _pg_name = g.app.config.get('orchestration','default_payment_gateway',
                                    fallback=None)
        _pg_name = g.current_request.query_params.get('payment_gw', _pg_name)
        if not _pg_name:
            raise HTTPError(title="Unknown Payment Gateway",
                            description="Please specify Payment Gateway or "
                                        "default Payment Gateway")

        payment_gw = _pay_gws[_pg_name]()

        method = getattr(payment_gw, type)

        result = method(req)

        data['price'] = result['product_price']
        data['metadata'] = {'gateway_data': result['gateway_data']}

        if 'status' in result:
            data['status'] = result['status']

        if 'payment_date' in result:
            data['payment_date'] = result['payment_date']

        order = g.api.execute('PUT',
                              'v1/order/' + result['order_id'],
                              endpoint='orchestration',
                              data=data).json

        try:
            product = req.context.api.execute('GET',
                                              'v1/product/'
                                              + order['product_id'],
                                              endpoint='orchestration').json

            result['product_name'] = product['name']
        except:
            pass

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

        router.add('GET',
                   '/orders/{oid}',
                   self.view_order,
                   tag='customer')

        router.add(('GET', 'POST',),
                   '/order/success',
                   self.success)

        router.add(['GET', 'POST'],
                   '/order/decline',
                   self.decline)

        router.add(['GET', 'POST', 'PUT'],
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
                'price': product['price'],
                'user_id': req.credentials.user_id}

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

        payment_gws = get_payment_gateways(product)

        return render_template('netrino.ui/orders/prepare_order.html',
                               view=product['name'],
                               product=product,
                               order_id=order['id'],
                               form=setup_form,
                               payment_gws=payment_gws)

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

        payment_gw = EntryPoints('netrino.payment.gateways')[
            req.form_dict['payment_gateway']](product, oid)

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
                               view="My Orders")

    def view_order(self, req, resp, oid):
        order = req.context.api.execute('GET',
                                        'v1/order/' + oid,
                                        endpoint='orchestration').json
        product = req.context.api.execute('GET',
                                          'v1/product/' + order['product_id'],
                                          endpoint='orchestration').json

        order_metadata = js.loads(order['metadata'])
        if 'payment_gateway' in order_metadata:
            pg_name = order_metadata['payment_gateway']
        else:
            pg_name = g.app.config.get('orchestration',
                                       'default_payment_gateway')

        payment_gw = EntryPoints('netrino.payment.gateways')[
            pg_name](product, oid)

        additional = None

        if hasattr(payment_gw, 'order_info'):
            additional = payment_gw.order_info(req, order)

        return render_template('netrino.ui/orders/view_order.html',
                               view="View Order",
                               order=order,
                               product=product,
                               additional=additional)

    def success(self, req, resp):
        if req.method != 'POST':
            return self.orders(req, resp)

        data = {'payment_date': now(),
                'metadata': {'gateway_data': req.form_dict}}

        result = process_notification(req, 'success', data)
        result['payment_date'] = data['payment_date']

        return render_template('netrino.ui/orders/success.html',
                               view="Order Received",
                               **result)

    def decline(self, req, resp, reason=None):
        if req.method != 'POST':
            return self.orders(req, resp)

        data = {'status': 'declined',
                'metadata': {'gateway_data': req.form_dict}}

        if reason:
            data['status'] += " - " + reason

        result = process_notification(req, 'decline', data)

        return render_template('netrino.ui/orders/decline.html',
                               view="Payment Failed", result=result)

    def notify(self, req, resp):
        if req.method not in ('PUT', 'POST',):
            return self.orders(req, resp)

        data = {}

        result = process_notification(req, 'notify', data)

        if 'payment_date' in data:
            result['payment_date'] = data['payment_date']

        return render_template('netrino.ui/orders/notify.html',
                               view="Notification Received", result=result)

    def redirect(self, req, resp):
        if req.method != 'POST':
            return self.orders(req, resp)

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
