# -*- coding: utf-8 -*-
# Copyright (c) 2019 Dave Kruger.
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
from luxon import register
from luxon import router
from luxon import db
from luxon import js

from luxon.utils.pkg import EntryPoints
from luxon.helpers.api import raw_list, obj
from luxon.utils.unique import string_id

from luxon.exceptions import ValidationError
from luxon.exceptions import HTTPConflict

from netrino.models.orders import netrino_order


@register.resources()
class Orders:
    def __init__(self):
        router.add('GET', '/v1/orders', self.list,
                   tag='customer')
        router.add('GET', '/v1/order/{oid}', self.view,
                   tag='customer')
        router.add('POST', '/v1/order', self.create,
                   tag='customer')
        router.add(['PUT', 'PATCH'], '/v1/order/{oid}', self.update,
                   tag='customer')
        router.add('POST', '/v1/activate/product/{oid}', self.activate,
                   tag='services:admin')

    def _get_service(self, oid):
        sql_order = 'SELECT product_id FROM netrino_order WHERE id=?'
        sql_product = 'SELECT * FROM netrino_product WHERE id=?'
        sql = 'SELECT entrypoint,metadata FROM netrino_product_entrypoint ' \
              'WHERE product_id=?'
        with db() as conn:
            order = conn.execute(sql_order, oid).fetchone()
            pid = order['product_id']
            product = conn.execute(sql_product, pid).fetchone()
            result = conn.execute(sql, pid).fetchone()

        if result:
            try:
                metadata = js.loads(result['metadata'])
            except TypeError:
                metadata = {}

            return product, result['entrypoint'], metadata

        return product, None, None

    def _get_orders(self):
        sql = 'SELECT netrino_order.id as id,' \
              'netrino_product.name as product_name,' \
              'netrino_order.creation_time as creation_time,' \
              'netrino_order.tenant_id as tenant_id ' \
              'FROM netrino_order,netrino_product ' \
              'WHERE netrino_order.product_id=netrino_product.id'
        with db() as conn:
            return conn.execute(sql).fetchall()

    def list(self, req, resp):
        orders = self._get_orders()

        return raw_list(req, orders)

    def create(self, req, resp):

        order = obj(req, netrino_order)
        order.update({'short_id': string_id(25)})
        try:
            order.commit()
        except ValidationError:
            raise HTTPConflict(title="Duplicate Order",
                               description="Please retry this request")

        return order

    def update(self, req, resp, oid):
        """The following fields can be updated:
        status
        metadata
        payment_date
        """
        sql = 'UPDATE netrino_order SET '
        vals = []
        fields = []
        o_sql = 'SELECT * FROM netrino_order WHERE id=?'
        with db() as conn:
            if 'metadata' in req.json:
                emd = conn.execute(o_sql, oid).fetchone()['metadata']
                if emd:
                    md = js.loads(emd)
                else:
                    md = {}

                md.update(req.json['metadata'])
                fields.append('metadata=?')
                vals.append(js.dumps(md))

            if 'status' in req.json:
                fields.append('status=?')
                vals.append(req.json['status'])

            if 'payment_date' in req.json:
                fields.append('payment_date=?')
                vals.append(req.json['payment_date'])

            sql += ','.join(fields)
            sql += ' WHERE id=?'

            if vals:
                conn.execute(sql, vals + [oid])
                conn.commit()

            order = conn.execute(o_sql, oid).fetchone()

        return order

    def view(self, req, resp, oid):
        return obj(req, netrino_order, sql_id=oid)

    def activate(self, req, resp, oid):
        product, ep, metadata = self._get_service(oid)

        result = {'reason': 'Nothing to do, no "netrino.product.tasks" '
                            'entrypoint found'}
        if ep:
            ep = EntryPoints('netrino.product.tasks')[ep]
            ep_obj = ep(req, metadata, oid, product)
            result = ep_obj.deploy()

        return result
