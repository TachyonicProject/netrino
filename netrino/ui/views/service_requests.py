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
from luxon import db
from luxon import router
from luxon import register
from luxon import render_template
from luxon.utils.bootstrap4 import form
from luxon.exceptions import FieldMissing

from netrino.helpers.yang import yang_to_html_form


g.nav_menu.add('/Services/Active',
               href='/services/requests',
               tag='customer',
               feather='package')

@register.resources()
class ServiceRequests():
    def __init__(self):
        router.add('GET',
                   '/services/requests',
                   self.list,
                   tag='customer')
        router.add('GET',
                   '/services/requests/available',
                   self.avail_services,
                   tag='customer')
        router.add('GET',
                   '/services/requests/{id}',
                   self.add_service_request,
                   tag='customer')
        router.add('GET',
                   '/services/requests/{id}/add',
                   self.add_service_request,
                   tag='customer')


    def list(self, req, resp):
        return render_template('netrino.ui/service_requests/list.html',
                               view='Active Services')

    def avail_services(self, req, resp):
        stemplates = req.context.api.execute('GET','v1/service-templates',
                                     endpoint='orchestration')
        return render_template('netrino.ui/service_requests/list_avail.html',
                               view='Create Service Request',
                               services=stemplates.json['payload'])

    def add_service_request(self, req, resp, id):
        if req.method == 'POST':
            pass
        else:
            api = req.context.api
            service_template = api.execute('GET','v1/service-template/%s' % id,
                                           endpoint='orchestration').json
            models = [m['yang_model'] for m in service_template['models']]
            user_select = []
            for model in service_template['models']:
                if model['user_select']:
                    user_select += model['user_select']

            form = user_select_form(user_select)
            return render_template('netrino.ui/service_requests/add.html',
                                   view="Request %s Service" %
                                        service_template['name'], id=id,
                                   form=form)


def user_select_form(l=[]):
    result = ''
    for us in l:
        result += '<div class="form-group">'
        result += '<label for="%s">%s</label>' % (us['name'], us['description'],)
        if us['type'] == "text":
            result += '<input type="text" class="form-control" '
            result += 'id="%s" name="%s"></div>' % (us['name'], us['name'],)
        elif us['type'] == 'select':
            result += '<select id="%s" name="%s" data-url="%s" ' \
                      'data-endpoint="%s" required></select>' \
                      '</div>' % (
                      us['name'], us['name'], us['url'], us['endpoint'])

    return result

