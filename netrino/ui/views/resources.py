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
from luxon import router
from luxon import register
from luxon import render_template
from luxon.utils.bootstrap4 import form

from netrino.ui.models.service_templates import netrino_custom_resource

from netrino.helpers.yang import yang_to_html_form


g.nav_menu.add('/Resources/Custom',
               href='/resources/custom',
               tag='customer',
               feather='package')

@register.resources()
class CustomResources():
    def __init__(self):
        router.add('GET',
                   '/resources/custom',
                   self.list,
                   tag='services:view')

        router.add('GET',
                   '/resources/custom/{rid}', self.view,
                   tag='services:view')

        router.add('GET',
                   '/resources/custom/delete/{rid}',
                   self.delete,
                   tag='services:admin')

        router.add(('GET', 'POST',),
                   '/resources/custom/add',
                   self.add,
                   tag='services:admin')

        router.add(('GET', 'POST',),
                   '/resources/custom/edit/{rid}',
                   self.edit,
                   tag='services:admin')

    def list(self, req, resp):
        return render_template('netrino.ui/resources/list.html',
                               view='Custom Resources')

    def delete(self, req, resp, rid):
        req.context.api.execute('DELETE', '/v1/resources/custom/%s' % rid,
                                endpoint='orchestration')

    def view(self, req, resp, rid):
        domain = req.context.api.execute(
            'GET', '/v1/resources/custom/%s' % rid,
            endpoint='orchestration')
        html_form = form(netrino_custom_resource, domain.json, readonly=True)
        return render_template('netrino.ui/resources/view.html',
                               view='View Custom Resource',
                               form=html_form,
                               id=rid)

    def edit(self, req, resp, rid):
        if req.method == 'POST':
            req.context.api.execute('PUT', '/v1/resources/custom/%s' % rid,
                                    data=req.form_dict,
                                    endpoint='orchestration')
            return self.view(req, resp, rid)
        else:
            response = req.context.api.execute(
                'GET', '/v1/resources/custom/%s' % rid,
                                             endpoint='orchestration')
            html_form = form(netrino_custom_resource, response.json)
            return render_template('netrino.ui/resources/edit.html',
                                   view='Edit Custom Resource',
                                   form=html_form,
                                   id=rid)

    def add(self, req, resp):
        if req.method == 'POST':
            response = req.context.api.execute('POST', '/v1/resources/custom',
                                               data=req.form_dict,
                                               endpoint='orchestration')
            return self.view(req, resp, response.json['id'])
        else:
            html_form = form(netrino_custom_resource)
            return render_template('netrino.ui/resources/add.html',
                                   view='Add Custom Resource',
                                   form=html_form)
