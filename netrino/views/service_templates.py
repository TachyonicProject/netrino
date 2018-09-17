# -*- coding: utf-8 -*-
# Copyright (c) 2018 David Kruger.
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
from uuid import uuid4
from luxon import router
from luxon import register
from luxon import db

from luxon.utils import js
from luxon.exceptions import FieldMissing, SQLIntegrityError
from luxon.exceptions import HTTPNotFound
from collections import OrderedDict

from netrino.models.service_templates import netrino_service_template
from netrino.models.service_templates import netrino_service_template_entry
from netrino.models.service_templates import netrino_servicetemplate_mappings
from netrino.models.service_templates import netrino_servicetemplate_static
from netrino.models.service_templates import netrino_servicetemplate_pool
from netrino.models.service_templates import netrino_user_select
from netrino.models.service_templates import netrino_task_output

from psychokinetic.utils.api import sql_list

ALLOCATIONS = {'pool_allocations': netrino_servicetemplate_pool,
                       'mappings': netrino_servicetemplate_mappings,
                       'user_select':netrino_user_select,
                       'task_output':netrino_task_output,
                       'static_assignments': netrino_servicetemplate_static}

@register.resources()
class ServiceTemplate():
    def __init__(self):
        router.add('POST',
                   '/v1/service-template',
                   self.create, tag='services:admin')
        router.add('GET',
                   '/v1/service-template/{name}',
                   self.view, tag='services:view')
        router.add('GET',
                   '/v1/service-templates',
                   self.list, tag='services:view')
        router.add(['PUT','PATCH'],
                   '/v1/service-template/{name}',
                   self.update, tag='services:view')
        router.add('DELETE',
                   '/v1/service-template/{name}',
                   self.delete, tag='services:view')

    def create(self, req, resp):
        name = req.json['name']
        service_template = netrino_service_template()
        service_template.update({'name':name})
        models = req.json['models']
        service_template.commit()
        try:
            for model in models:
                nste = netrino_service_template_entry()
                allocate = {k:model.pop(k) for k in ALLOCATIONS if k in model}
                nste['service_template'] = service_template['id']
                nste.update(model)
                nste.commit()
                for a in allocate:
                    for e in allocate[a]:
                        alloc_model = ALLOCATIONS[a]()
                        alloc_model['servicetemplate_entry'] = nste['id']
                        alloc_model.update(e)
                        alloc_model.commit()
        except SQLIntegrityError as err:
            service_template.delete()
            service_template.commit()
            raise err

        return self.view(req, resp, name)

    def list(self, req, resp):
        return sql_list(req, 'netrino_service_template',['id', 'name'])

    def view(self, req, resp, name):
        result = OrderedDict()
        with db() as conn:
            cur = conn.execute("SELECT * FROM netrino_service_template "
                               "WHERE name=? OR id=?", (name,name,))
            stemplate = cur.fetchone()
            if not stemplate:
                raise HTTPNotFound
            result['name'] = stemplate['name']
            result['models'] = []
            msql = "SELECT * FROM netrino_service_template_entry WHERE " \
               "service_template=?"
            entries = conn.execute(msql,(stemplate['id'],)).fetchall()

            asql = "SELECT * FROM %s WHERE servicetemplate_entry=?"
            for e in entries:
                result['models'].append(e)
                for a in ALLOCATIONS:
                    result['models'][-1][a] = []
                for a in ALLOCATIONS:
                    cur = conn.execute(asql % ALLOCATIONS[a].__name__, e['id'])
                    allocate = cur.fetchall()
                    for ae in allocate:
                        result['models'][-1][a].append(ae)

        return js.dumps(result)

    def update(self, req, resp, name):
        with db() as conn:
            cur = conn.execute("SELECT * FROM netrino_service_template "
                               "WHERE name=? OR id=?", (name,name,))
            stemplate = cur.fetchone()
            if not stemplate:
                raise HTTPNotFound
        service_template = netrino_service_template()
        service_template.sql_id(stemplate['id'])
        service_template.update({'name':name})
        models = req.json['models']
        service_template.commit()
        try:
            for model in models:
                nste = netrino_service_template_entry()
                if 'id' in model:
                    nste.sql_id(model.pop('id'))
                allocate = {k:model.pop(k) for k in ALLOCATIONS if k in model}
                nste['service_template'] = service_template['id']
                nste.update(model)
                nste.commit()
                for a in allocate:
                    for e in allocate[a]:
                        alloc_model = ALLOCATIONS[a]()
                        if 'id' in e:
                            alloc_model.sql_id(e.pop('id'))
                        alloc_model['servicetemplate_entry'] = nste['id']
                        alloc_model.update(e)
                        alloc_model.commit()
        except SQLIntegrityError as err:
            service_template.delete()
            service_template.commit()
            raise err

        return self.view(req, resp, name)

    def delete(self, req, resp, name):
        with db() as conn:
            conn.execute("DELETE FROM netrino_service_template "
                               "WHERE name=? OR id=?", (name,name,))
            conn.commit()
