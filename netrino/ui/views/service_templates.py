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
from luxon import js
from luxon.utils.bootstrap4 import form
from luxon.exceptions import FieldMissing
from collections import OrderedDict

from netrino.ui.models.service_templates import netrino_service_template
from netrino.ui.models.service_templates import netrino_service_template_entry
from netrino.ui.models.service_templates import netrino_servicetemplate_mappings
from netrino.ui.models.service_templates import netrino_servicetemplate_static
from netrino.ui.models.service_templates import netrino_servicetemplate_pool
from netrino.ui.models.service_templates import netrino_servicetemplate_copy
from netrino.ui.models.service_templates import netrino_user_select
from netrino.ui.models.service_templates import netrino_task_output

ALLOCATIONS = OrderedDict(
    {'static_assignments': netrino_servicetemplate_static,
    'pool_allocations': netrino_servicetemplate_pool,
    'mappings': netrino_servicetemplate_mappings,
    'user_select':netrino_user_select,
    'task_output': netrino_task_output,
    'copy_entries': netrino_servicetemplate_copy}
)

g.nav_menu.add('/Services/Templates',
               href='/services/templates',
               tag='admin',
               feather='package')


@register.resources()
class Users():
    def __init__(self):
        router.add('GET',
                   '/services/templates',
                   self.list,
                   tag='services:view')

        router.add('GET',
                   '/services/templates/{id}',
                   self.view,
                   tag='services:view')

        router.add(('GET', 'POST',),
                   '/services/templates/add',
                   self.add,
                   tag='services:admin')

        router.add(('GET', 'POST',),
                   '/services/templates/edit/{id}',
                   self.edit,
                   tag='services:admin')

        router.add('GET',
                   '/services/templates/delete/{id}',
                   self.delete,
                   tag='services:admin')

        router.add(('GET', 'POST',),
                   '/services/templates/{id}/model',
                   self.add_model,
                   tag='services:admin')

        router.add('GET',
                   '/services/templates/{id}/view_model/{model_id}',
                   self.view_model,
                   tag='services:admin')

        router.add(('GET', 'POST',),
                   '/services/templates/{id}/edit_model/{model_id}',
                   self.edit_model,
                   tag='services:admin')

        router.add('GET', '/services/templates/{id}/rm_model/{model_id}',
                   self.rm_model,
                   tag='services:admin')

        router.add('POST',
                   '/services/templates/{id}/allocate/{model_id}/{atype}',
                   self.add_allocation,
                   tag='services:admin')

        router.add('GET', '/services/templates/allocate/{atype}/{aid}',
                   self.rm_allocation,
                   tag='services:admin')

    def list(self, req, resp):
        return render_template('netrino.ui/service_templates/list.html',
                               view='Service Templates')

    def delete(self, req, resp, id):
        req.context.api.execute('DELETE', '/v1/service-template/%s' % id,
                                endpoint='orchestration')

    def view(self, req, resp, id):
        service = req.context.api.execute('GET',
                                          '/v1/service-template/%s' % id,
                                          endpoint='orchestration')
        html_form = form(netrino_service_template, service.json, readonly=True)
        return render_template('netrino.ui/service_templates/view.html',
                               form=html_form,
                               id=id,
                               view="View Service Template")

    def edit(self, req, resp, id):
        if req.method == 'POST':
            data = req.form_dict
            req.context.api.execute('PUT', '/v1/service-template/%s' % id,
                                    data=data,
                                    endpoint='orchestration')
            req.method = 'GET'
            return self.edit(req, resp, id)
        else:
            service = req.context.api.execute('GET',
                                              '/v1/service-template/%s' % id,
                                              endpoint='orchestration')
            html_form = form(netrino_service_template, service.json)
            return render_template('netrino.ui/service_templates/edit.html',
                                   form=html_form,
                                   id=id,
                                   view="Edit Service Template")

    def add(self, req, resp):
        if req.method == 'POST':
            data = req.form_dict
            data['models'] = []
            response = req.context.api.execute('POST', '/v1/service-template',
                                               data=data,
                                               endpoint='orchestration')
            return self.view(req, resp, response.json['id'])
        else:
            html_form = form(netrino_service_template)
            return render_template('netrino.ui/service_templates/add.html',
                                   view='Add Service Template',
                                   form=html_form)

    def add_model(self, req, resp, id):
        data = {}
        try:
            data['yang_model'] = req.form_dict['model']
            data['entry_no'] = req.form_dict['entry_no']
        except KeyError:
            raise FieldMissing('Model', 'Yang Model',
                               'Please select Yang Model and Entry_number')
        uri = '/v1/service-template/%s/model' % id
        response = req.context.api.execute('POST', uri, data=data,
                                           endpoint='orchestration')

    def view_model(self, req, resp, id, model_id):
        uri = '/v1/service-template/%s/model/%s' % (id, model_id,)
        service = req.context.api.execute('GET',
                                          uri,
                                          endpoint='orchestration')
        html_form = form(netrino_service_template_entry, service.json,
                         readonly=True)
        return render_template('netrino.ui/service_templates/model.html',
                               view='View Service Template Entry',
                               form=html_form,
                               id=id,
                               model=model_id)

    def edit_model(self, req, resp, id, model_id):
        if req.method == 'POST':
            data = req.form_dict
            req.context.api.execute('PUT',
                                    '/v1/service-template/%s/model/%s' % (
                                    id, model_id,),
                                    data=data,
                                    endpoint='orchestration')
            req.method = 'GET'
            return self.edit_model(req, resp, id, model_id)
        else:
            uri = '/v1/service-template/%s/model/%s' % (id, model_id,)
            service = req.context.api.execute('GET',
                                              uri,
                                              endpoint='orchestration')
            model_name = service.json['yang_model']
            html_form = form(netrino_service_template_entry, service.json)
            forms = {}
            for a in ALLOCATIONS:
                forms[a + '_form'] = form(ALLOCATIONS[a])
            return render_template('netrino.ui/service_templates/model.html',
                                   view='Edit Service Template Entry',
                                   form=html_form,
                                   id=id,
                                   model=model_id,
                                   model_name=model_name,
                                   interface=service.json['interface'],
                                   element_id=service.json['element'],
                                   element_name=service.json['element_name'],
                                   **forms)

    def rm_model(self, req, resp, id, model_id):
        uri = '/v1/service-template/%s/model/%s' % (id, model_id,)
        req.context.api.execute('DELETE', uri,
                                endpoint='orchestration')

    def add_allocation(self, req, resp, id, model_id, atype):
        data = req.form_dict
        data['servicetemplate_entry'] = model_id
        if 'mapper_data' in data:
            data['mapper_data'] = js.loads(data['mapper_data'])
        req.context.api.execute('POST', 'v1/allocation/' + atype,
                                data=data,
                                endpoint='orchestration')
        req.method = 'GET'
        return self.edit_model(req,resp, id, model_id)


    def rm_allocation(self, req, resp, atype, aid):
        req.context.api.execute('DELETE',
                                '/v1/allocation/%s/%s' % (atype, aid,),
                                endpoint='orchestration')

