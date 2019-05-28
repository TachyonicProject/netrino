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
import base64
from luxon import register
from luxon import router
from luxon import db
from luxon import g
from luxon import js

from luxon.helpers.api import sql_list, obj, raw_list
from luxon.utils.pkg import EntryPoints
from luxon.utils import sql

from netrino.models.products import netrino_product
# from netrino.models.products import netrino_custom_attr
from netrino.models.products import netrino_categories
from netrino.models.products import netrino_product_entrypoint


@register.resources()
class Products:
    def __init__(self):
        router.add('GET', '/v1/product/{pid}', self.product,
                   tag='customer')
        router.add('GET', '/v1/products', self.products,
                   tag='customer')
        router.add('GET', '/v1/products/categories', self.categories,
                   tag='customer')
        router.add('POST', '/v1/product', self.create,
                   tag='products:admin')
        router.add(['PUT', 'PATCH'], '/v1/product/{pid}', self.update,
                   tag='products:admin')
        router.add('DELETE', '/v1/product/{pid}', self.delete,
                   tag='products:admin')
        router.add('POST', '/v1/product/{pid}/category/{category}',
                   self.add_category,
                   tag='products:admin')
        router.add('DELETE', '/v1/products/category/{cid}',
                   self.delete_category,
                   tag='products:admin')
        router.add('POST', '/v1/product/{pid}/image',
                   self.add_image,
                   tag='products:admin')
        router.add('GET', '/v1/product/{pid}/image',
                   self.image,
                   tag='customer')
        router.add('GET', '/v1/products/tasks',
                   self.entrypoints,
                   tag='products:admin')
        router.add('POST', '/v1/product/{pid}/task/{ep}',
                   self.add_ep,
                   tag='products:admin')
        router.add('DELETE', '/v1/products/tasks/{ep}',
                   self.delete_ep,
                   tag='products:admin')

    def _get_categories(self, pid):
        sql = 'SELECT * FROM netrino_categories WHERE product_id=?'
        with db() as conn:
            return conn.execute(sql, (pid,)).fetchall()

    def _get_services(self, pid):
        sql = 'SELECT netrino_product_entrypoint.* FROM ' \
              'netrino_product_entrypoint WHERE product_id=?'
        with db() as conn:
            return conn.execute(sql, (pid,)).fetchall()

    def product(self, req, resp, pid):
        product = obj(req, netrino_product, sql_id=pid).dict
        del product['image']

        categories = self._get_categories(pid)
        services = self._get_services(pid)
        product['categories'] = categories
        product['services'] = services

        view = req.query_params.get('view', False)

        if view:
            if view == 'categories':
                return raw_list(req, categories)
            elif view == 'services':
                return raw_list(req, services)

        return product

    def products(self, req, resp):
        select = sql.Select('netrino_product')
        f_product = sql.Field('netrino_product.id')
        f_name = sql.Field('netrino_product.name')
        f_parent_id = sql.Field('netrino_product.parent_id')
        f_price = sql.Field('netrino_product.price')
        f_monthly = sql.Field('netrino_product.monthly')
        f_description = sql.Field('netrino_product.description')
        f_creation_time = sql.Field('netrino_product.creation_time')

        filter = req.query_params.get('category', None)
        if filter:
            f_category_product = sql.Field('netrino_categories.product_id')
            f_category_name = sql.Field('netrino_categories.name')
            j_product = f_category_product == f_product
            select = sql.Select('netrino_categories')
            select.where = f_category_name == sql.Value(filter)
            select.inner_join('netrino_product', j_product)

        select.fields = (
            f_product, f_name, f_parent_id, f_price, f_monthly, f_description,
            f_creation_time)

        return sql_list(req,
                        select,
                        fields=('id',
                                'name',
                                'parent_id',
                                'price',
                                'monthly',
                                'description',
                                'creation_time',),
                        search={'id': str,
                                'name': str,
                                'parent_id': str,
                                'price': str,
                                'monthly': str,
                                'description': str,
                                'creation_time': str})

    def categories(self, req, resp):
        sql = 'SELECT DISTINCT(name) FROM netrino_categories'
        with db()as conn:
            categories = conn.execute(sql).fetchall()
        return raw_list(req, categories)

    def create(self, req, resp):
        product = obj(req, netrino_product)
        product.commit()
        return product

    def update(self, req, resp, pid):
        product = obj(req, netrino_product, sql_id=pid)
        product.commit()
        return product

    def delete(self, req, resp, pid):
        product = obj(req, netrino_product, sql_id=pid)
        product.commit()
        return product

    def add_category(self, req, resp, pid, category):
        category_entry = obj(req, netrino_categories)
        category_entry['name'] = category
        category_entry['product_id'] = pid
        category_entry.commit()
        return category_entry

    def delete_category(self, req, resp, cid):
        category_entry = obj(req, netrino_categories, sql_id=cid)
        category_entry.commit()

    def add_image(self, req, resp, pid):
        image_file = req.json['image_file']['base64']
        image_type = req.json['image_file']['type']
        sql = 'UPDATE netrino_product SET image=?,image_type=? WHERE id=?'
        with db() as conn:
            conn.execute(sql, (image_file, image_type, pid))
            conn.commit()
        return {}

    def image(self, req, resp, pid):
        sql = 'SELECT image,image_type FROM netrino_product WHERE id=?'
        with db() as conn:
            result = conn.execute(sql, pid).fetchone()

        if not result or not result['image_type'] or not result['image']:
            # Returning blank image so that products
            # with no images do not have "404 not found" image
            result = {'image_type': "image/gif",
                      'image': b"R0lGODlhAQABAIAAAAAAAP///"
                               b"yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"}

        resp.set_header('Content-Type', result['image_type'])
        resp.content_type = result['image_type']
        resp.write(base64.b64decode(result['image']))

    def add_ep(self, req, resp, pid, ep):
        region = g.app.config.get('identity', 'region',
                                  fallback=req.context_region)
        metadata_model = EntryPoints('netrino.product.tasks')[
            ep].model()
        metadata_model.update(req.json)
        # Check to see all required data was submittied
        metadata_model._pre_commit()
        metadata = metadata_model.dict
        metadata['region'] = region
        model = netrino_product_entrypoint()
        model['product_id'] = pid
        model['entrypoint'] = ep
        model['metadata'] = js.dumps(metadata)
        model.commit()
        return self.view_ep(req, resp, model['id'])

    def view_ep(self, req, resp, eid):
        ep = netrino_product_entrypoint()
        ep.sql_id(eid)

        return ep

    def delete_ep(self, req, resp, ep):
        nep = obj(req, netrino_product_entrypoint, sql_id=ep)
        nep.commit()

        return nep

    def entrypoints(self, req, resp):
        """Lists all tasks registered under the
                netrino.product.tasks entry point.
                """
        eps = []
        for e in EntryPoints('netrino.product.tasks'):
            eps.append({'id': e, 'name': e})
        return raw_list(req, eps)
