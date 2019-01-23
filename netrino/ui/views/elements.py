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
from luxon.utils.pkg import EntryPoints
from luxon.exceptions import FieldMissing

from netrino.ui.models.elements import netrino_element

g.nav_menu.add('/Infrastructure/Elements',
               href='/infrastructure/elements',
               tag='services',
               feather='server')


def render_interface(eid, interface, view, data=None, ro=False):
    element_interface = EntryPoints('netrino_elements')[interface]
    html_form = form(element_interface, data, readonly=ro)
    return render_template('netrino.ui/elements/interface.html',
                           view='%s %s Interface' % (view, interface,),
                           form=html_form,
                           id=eid,
                           interface=interface)


@register.resources()
class Elements():
    def __init__(self):
        router.add('GET',
                   '/infrastructure/elements',
                   self.list,
                   tag='infrastructure:view')

        router.add('GET',
                   '/infrastructure/elements/{id}',
                   self.view,
                   tag='infrastructure:view')

        router.add('GET',
                   '/infrastructure/elements/delete/{id}',
                   self.delete,
                   tag='infrastructure:admin')

        router.add(('GET', 'POST',),
                   '/infrastructure/elements/add',
                   self.add,
                   tag='infrastructure:admin')

        router.add(('POST', 'GET',),
                   '/infrastructure/elements/edit/{id}',
                   self.edit,
                   tag='infrastructure:admin')

        router.add(('GET', 'POST',),
                   '/infrastructure/elements/{id}/interface',
                   self.interface,
                   tag='infrastructure:admin')

        router.add('POST',
                   '/infrastructure/interfaces/{eid}/{interface}',
                   self.add_interface,
                   tag='infrastructure:admin')

        router.add('POST',
                   '/infrastructure/interfaces/edit/{eid}/{interface}',
                   self.update_interface,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/interfaces/edit/{eid}/{interface}',
                   self.edit_interface,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/interfaces/delete/{eid}/{interface}',
                   self.delete_interface,
                   tag='infrastructure:admin')

        router.add('GET',
                   '/infrastructure/interfaces/{eid}/{interface}',
                   self.view_interface,
                   tag='infrastructure:admin')


    def list(self, req, resp):
        return render_template('netrino.ui/elements/list.html',
                               view='Elements')

    def delete(self, req, resp, id):
        req.context.api.execute('DELETE', '/v1/element/%s' % id,
                                endpoint='orchestration')

    def view(self, req, resp, id):
        element = req.context.api.execute('GET', '/v1/element/%s' % id,
                                         endpoint='orchestration')
        parent_name = None

        if 'parent' in element.json:
            parent_name = element.json['parent']['name']

        html_form = form(netrino_element, element.json, readonly=True)
        return render_template('netrino.ui/elements/view.html',
                               view='View Element',
                               form=html_form,
                               id=id,
                               parent=parent_name)

    def edit(self, req, resp, id):
        if req.method == 'POST':
            req.context.api.execute('PUT', '/v1/element/%s' % id,
                                    data=req.form_dict,
                                    endpoint='orchestration')
            return self.view(req, resp, id)
        else:
            element = req.context.api.execute('GET', '/v1/element/%s' % id,
                                             endpoint='orchestration')

            parent_name = None

            if 'parent' in element.json:
                parent_name = element.json['parent']['name']

            html_form = form(netrino_element, element.json)
            return render_template('netrino.ui/elements/edit.html',
                                   view='Edit Element',
                                   form=html_form,
                                   id=id,
                                   parent=parent_name,
                                   parent_id=element.json['parent_id'])

    def add(self, req, resp):
        if req.method == 'POST':
            response = req.context.api.execute('POST', '/v1/element',
                                               data=req.form_dict,
                                               endpoint='orchestration')
            return self.view(req, resp, response.json['id'])
        else:
            html_form = form(netrino_element)
            return render_template('netrino.ui/elements/add.html',
                                   view='Add Element',
                                   form=html_form)

    def interface(self, req, resp, id):
        try:
            interface = req.form_dict['interface']
        except KeyError:
            raise FieldMissing('Interface', 'Element Interface',
                               'Please select Interface for Element')
        return render_interface(id, interface, view="Add")
        element_interface = EntryPoints('netrino_elements')[interface]
        html_form = form(element_interface)

        return render_template('netrino.ui/elements/interface.html',
                               view='Add %s Interface' % interface,
                               form=html_form,
                               id=id,
                               interface=interface)

    def add_interface(self, req, resp, eid, interface):
        req.context.api.execute('POST', '/v1/element/%s/%s' % (eid, interface,),
                                data=req.form_dict,
                                endpoint='orchestration')
        req.method = 'GET'
        return self.edit(req, resp, eid)

    def update_interface(self, req, resp, eid, interface):
        req.context.api.execute('PUT', '/v1/element/%s/%s' % (eid, interface,),
                                data=req.form_dict,
                                endpoint='orchestration')
        req.method = 'GET'
        return self.view_interface(req, resp, eid, interface)

    def edit_interface(self, req, resp, eid, interface):
        e_int = req.context.api.execute('GET',
                                        '/v1/element/%s/%s' % (
                                        eid, interface,),
                                        data=req.form_dict,
                                        endpoint='orchestration')
        return render_interface(eid, interface, view="Edit",
                                data=e_int.json['metadata'])

    def view_interface(self, req, resp, eid, interface):
        e_int = req.context.api.execute('GET',
                                    '/v1/element/%s/%s' % (eid, interface,),
                                    data=req.form_dict,
                                    endpoint='orchestration')
        return render_interface(eid, interface, view="View",
                                data=e_int.json['metadata'], ro=True)
        element_interface = EntryPoints('netrino_elements')[interface]
        html_form = form(element_interface, e_int.json['metadata'],
                         readonly=True)
        return render_template('netrino.ui/elements/interface.html',
                               view='%s Interface' % interface,
                               form=html_form,
                               id=eid,
                               interface=interface)

    def delete_interface(self, req, resp, eid, interface):
        req.context.api.execute('DELETE', '/v1/element/%s/%s' % (eid, interface,),
                                data=req.form_dict,
                                endpoint='orchestration')
