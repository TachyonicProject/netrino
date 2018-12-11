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
from luxon.exceptions import FieldMissing



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
                   '/services/requests/add',
                   self.add_service_request,
                   tag='customer')

    def list(self, req, resp):
        return render_template('netrino.ui/service_requests/list.html',
                               view='Active Services')

    def add_service_request(self, req, resp):
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
                                   view='Create Service Request',
                                   form=html_form)


