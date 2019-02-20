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

from luxon.exceptions import HTTPNotFound
from luxon.helpers.api import sql_list, obj, raw_list

from netrino.models.products import netrino_product
from netrino.models.products import netrino_custom_attr
from netrino.models.products import netrino_categories


@register.resources()
class Products:
    def __init__(self):
        router.add('GET', '/v1/product/{pid}', self.product,
                   tag='products:view')
        router.add('GET', '/v1/products', self.products,
                   tag='login')
        router.add('POST', '/v1/product', self.create,
                   tag='products:view')
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
               tag='login')

    def _get_categories(self, pid):
        sql = 'SELECT * FROM netrino_categories WHERE product_id=?'
        with db() as conn:
            return conn.execute(sql, (pid,)).fetchall()


    def product(self, req, resp, pid):
        view = req.query_params.get('view', False)
        if view:
            if view == 'categories':
                categories = self._get_categories(pid)
                return raw_list(req, categories)

        return obj(req, netrino_product, sql_id=pid)

    def products(self, req, resp):
        return sql_list(req, 'netrino_product', ('id',
                                                  'name',
                                                  'parent_id',
                                                  'price',
                                                  'monthly',
                                                  'description',
                                                  'creation_time')
                        )

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


        resp.set_header('Content-Type',result['image_type'])
        resp.content_type = result['image_type']
        resp.write(base64.b64decode(result['image']))

