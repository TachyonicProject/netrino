# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 Dave Kruger.
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
from luxon import router
from luxon import register
from luxon import render_template
from luxon.utils.bootstrap4 import form
from luxon.utils.pkg import EntryPoints
from luxon.exceptions import FieldMissing

from netrino.ui.models.products import netrino_product
from netrino.ui.models.products import netrino_custom_attr


def render_model(element_model, pid, mval, mtype, view, data={},
                 ro=False, **kwargs):
    if hasattr(element_model, '__bases__') and element_model.__bases__[
        0].__name__ == 'Model':
        html_form = form(element_model, data, readonly=ro)
    elif isinstance(element_model, str):
        html_form = render_template(element_model, **data)
    return render_template('netrino.ui/products/%s.html' % mtype,
                           view='%s %s %s' % (view, mval, mtype),
                           form=html_form,
                           id=pid,
                           model=mval,
                           **kwargs)


g.nav_menu.add('/Infrastructure/Orchestration/Product Catalog',
               href='/products',
               tag='products:admin',
               endpoint='orchestration',
                   feather='package')


@register.resources()
class Products():
    def __init__(self):
        router.add('GET',
                   '/products',
                   self.list,
                   tag='products:view')

        router.add('GET',
                   '/products/{pid}',
                   self.view,
                   tag='products:view')

        router.add('GET',
                   '/products/delete/{pid}',
                   self.delete,
                   tag='products:admin')

        router.add(('GET', 'POST',),
                   '/products/add',
                   self.add,
                   tag='products:admin')

        router.add(('GET', 'POST',),
                   '/products/edit/{pid}',
                   self.edit,
                   tag='products:admin')

        router.add('POST',
                   '/products/add-category/{pid}',
                   self.add_category,
                   tag='products:admin')

        router.add('GET',
                   '/products/rm-category/{cid}',
                   self.rm_category,
                   tag='products:admin')

        router.add('POST',
                   '/products/add-image/{pid}',
                   self.add_image,
                   tag='products:admin')

        router.add(('GET', 'POST',),
                   '/products/add-service/{pid}',
                   self.entrypoint,
                   tag='products:admin')

        router.add('POST',
                   '/products/services/{pid}/{ep}',
                   self.add_entrypoint,
                   tag='products:admin')

        router.add('POST',
                   '/products/services/edit/{pid}/{ep}',
                   self.update_entrypoint,
                   tag='products:admin')

        router.add('GET',
                   '/products/services/edit/{pid}/{ep}',
                   self.edit_entrypoint,
                   tag='products:admin')

        router.add('GET',
                   '/products/rm-service/{eid}',
                   self.delete_entrypoint,
                   tag='products:admin')

        router.add('GET',
                   '/products/services/{pid}/{ep}',
                   self.view_entrypoint,
                   tag='products:admin')

    def list(self, req, resp):
        return render_template('netrino.ui/products/list.html',
                               view='Products')

    def delete(self, req, resp, pid):
        req.context.api.execute('DELETE', '/v1/product/%s' % pid,
                                endpoint='orchestration')

    def view(self, req, resp, pid):
        product = req.context.api.execute('GET', '/v1/product/%s' % pid,
                                         endpoint='orchestration')
        html_form = form(netrino_product, product.json, readonly=True)
        return render_template('netrino.ui/products/view.html',
                               view='View Product',
                               form=html_form,
                               id=pid)

    def edit(self, req, resp, pid):
        if req.method == 'POST':
            req.context.api.execute('PUT', '/v1/product/%s' % pid,
                                    data=req.form_dict,
                                    endpoint='orchestration')
            return self.view(req, resp, pid)
        else:
            product = req.context.api.execute('GET', '/v1/product/%s' % pid,
                                             endpoint='orchestration')
            html_form = form(netrino_product, product.json)
            return render_template('netrino.ui/products/edit.html',
                                   view='Edit Product',
                                   form=html_form,
                                   id=pid)

    def add(self, req, resp):
        if req.method == 'POST':
            response = req.context.api.execute('POST', '/v1/product',
                                               data=req.form_dict,
                                               endpoint='orchestration')
            return self.view(req, resp, response.json['id'])
        else:
            html_form = form(netrino_product)
            return render_template('netrino.ui/products/add.html',
                                   view='Add Product',
                                   form=html_form)

    def add_category(self, req, resp, pid):
        category = req.form_dict['category']
        req.context.api.execute('POST',
                                '/v1/product/%s/category/%s' % (pid, category),
                                endpoint='orchestration', data={})

    def rm_category(self, req, resp, cid):
        req.context.api.execute('DELETE',
                                '/v1/products/category/%s' % cid,
                                endpoint='orchestration')

    def add_image(self, req, resp, pid):
        req.context.api.execute('POST',
                                '/v1/product/%s/image' % (pid, ),
                                endpoint='orchestration', data=req.form_dict)
        req.method = 'GET'
        return self.edit(req, resp, pid)

    def entrypoint(self, req, resp, pid):
        try:
            ep = req.form_dict['service']
        except KeyError:
            raise FieldMissing('Service', 'Product Service',
                               'Please select Service for Product')
        model = EntryPoints('netrino.product.tasks')[ep].form

        return render_model(model, pid, ep, 'service', view="Add")

    def add_entrypoint(self, req, resp, pid, ep):
        req.context.api.execute('POST',
                                '/v1/product/%s/task/%s' % (pid, ep,),
                                data=req.form_dict,
                                endpoint='orchestration')
        req.method = 'GET'

        return self.edit(req, resp, pid)

    def update_entrypoint(self, req, resp, pid, ep):
        req.context.api.execute('PUT', '/v1/product/%s/task/%s' % (pid, ep,),
                                data=req.form_dict)
        req.method = 'GET'
        return self.view_entrypoint(req, resp, pid, ep)

    def edit_entrypoint(self, req, resp, pid, ep):
        p_ep = req.context.api.execute('GET',
                                        '/v1/product/%s/%s' % (
                                            pid, ep,),
                                        data=req.form_dict)

        model = EntryPoints('netrino.product.tasks')[ep].form

        return render_model(model, pid, ep,
                            'service', view="Edit",
                            data=p_ep.json['metadata'])

    def view_entrypoint(self, req, resp, pid, ep):
        p_ep = req.context.api.execute('GET',
                                        '/v1/product/%s/%s' % (
                                           pid, ep,))

        model = EntryPoints('netrino.product.tasks')[ep].form

        return render_model(model, pid, ep,
                            'service', view="View",
                            data=p_ep.json['metadata'], ro=True)


    def delete_entrypoint(self, req, resp, eid):
        req.context.api.execute('DELETE',
                                '/v1/products/tasks/%s' % (eid,),
                                endpoint="orchestration")
