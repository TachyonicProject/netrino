# -*- coding: utf-8 -*-
# Copyright (c) 2019 Christiaan Frans Rademan.
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

from netrino.ui.models.processes import netrino_process

g.nav_menu.add('/Infrastructure/Orchestration/Process Manager',
               href='/infrastructure/orchestration/process',
               tag='process:admin',
               endpoint='orchestration',
               feather='grid')


@register.resources()
class ProcessManager():
    def __init__(self):
        router.add('GET',
                   '/infrastructure/orchestration/process',
                   self.list,
                   tag='process:view')

        router.add('GET',
                   '/infrastructure/orchestration/process/{process_id}',
                   self.edit,
                   tag='process:admin')

        router.add('POST',
                   '/infrastructure/orchestration/process/edit/{process_id}',
                   self.edit,
                   tag='process:admin')

        router.add('GET',
                   '/infrastructure/orchestration/process/delete/{process_id}',
                   self.delete,
                   tag='process:admin')

        router.add(('GET', 'POST',),
                   '/infrastructure/orchestration/process/add',
                   self.add,
                   tag='process:admin')

        router.add(('GET', 'PUT',),
                   '/infrastructure/orchestration/process/{process_id}/{node}',
                   self.node,
                   tag='process:admin')

    def list(self, req, resp):
        return render_template('netrino.ui/process/list.html',
                               view='Process Manager')

    def delete(self, req, resp, process_id):
        req.context.api.execute('DELETE', '/v1/process/%s' % process_id,
                                endpoint='orchestration')
        return self.list(req, resp)

    def edit(self, req, resp, process_id):
        if req.method == 'POST':
            data = req.form_dict
            req.context.api.execute('PUT', '/v1/process/%s' % process_id,
                                    data=data,
                                    endpoint='orchestration')
            req.method = 'GET'
            return self.edit(req, resp, process_id)
        else:
            proc = req.context.api.execute('GET',
                                           '/v1/process/%s' % process_id,
                                           endpoint='orchestration')

            html_form = form(netrino_process, proc.json)

            return render_template('netrino.ui/process/edit.html',
                                   form=html_form,
                                   process_id=process_id,
                                   view="Process Editor")

    def node(self, req, resp, process_id, node):
        return render_template('netrino.ui/process/node.html',
                               process_id=process_id,
                               view="Node Editor")

    def add(self, req, resp):
        if req.method == 'POST':
            data = req.form_dict
            response = req.context.api.execute('POST', '/v1/process',
                                               data=data,
                                               endpoint='orchestration')

            return self.edit(req, resp, response.json['id'])
        else:
            html_form = form(netrino_process)

            return render_template('netrino.ui/process/add.html',
                                   view='New Process',
                                   form=html_form)
