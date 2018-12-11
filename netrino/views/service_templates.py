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

from luxon.helpers.api import raw_list
from luxon.utils import js
from luxon.exceptions import FieldMissing
from luxon.exceptions import SQLIntegrityError
from luxon.exceptions import FieldError
from luxon.exceptions import HTTPNotFound
from collections import OrderedDict

from netrino.models.service_templates import netrino_service_template
from netrino.models.service_templates import netrino_service_template_entry
from netrino.helpers.service_template import ALLOCATIONS

from luxon.helpers.api import sql_list


@register.resources()
class ServiceTemplate():
    def __init__(self):
        router.add('POST',
                   '/v1/service-template',
                   self.create, tag='services:admin')
        router.add('GET',
                   '/v1/service-template/{uid}',
                   self.view, tag='services:view')
        router.add('GET',
                   '/v1/service-templates',
                   self.list, tag='services:view')
        router.add(['PUT','PATCH'],
                   '/v1/service-template/{uid}',
                   self.update, tag='services:admin')
        router.add('DELETE',
                   '/v1/service-template/{uid}',
                   self.delete, tag='services:view')
        router.add('GET',
                   '/v1/service-template/{uid}/models',
                   self.models, 'services:view')
        router.add('GET',
                   '/v1/service-template/{uid}/model/{mid}',
                   self.view_model, 'services:view')
        router.add('POST',
                   '/v1/service-template/{uid}/model',
                   self.create_model, 'services:admin')
        router.add(['PUT','PATCH'],
                   '/v1/service-template/{uid}/model/{mid}',
                   self.update_model, 'services:admin')
        router.add('DELETE',
                   '/v1/service-template/{uid}/model/{mid}',
                   self.delete_model, 'services:admin')
        router.add('GET',
                   '/v1/service-template/{uid}/model/{mid}/allocations',
                   self.allocations, 'services:view')
        router.add('GET',
                   '/v1/service-template/{uid}/model/{mid}/allocations/'
                   '{atype}',
                   self.allocations, 'services:view')
        router.add('GET',
                   '/v1/allocation/{atype}/{aid}',
                   self.view_allocation, 'services:view')
        router.add(['PUT', 'PATCH'],
                   '/v1/allocation/{atype}/{aid}',
                   self.update_allocation, 'services:admin')
        router.add('DELETE',
                   '/v1/allocation/{atype}/{aid}',
                   self.delete_allocation, 'services:admin')


    def create(self, req, resp):
        """Creates a new Service Template.

        JSON Args:
             name (str): Name of the Service Template
             models (list): List of models for this Service Template
                            See netrino.models.netrino_service_template_entry
                            for available fields.

        Each Model may also have the following sections for Auto-allocation
        of specific leafs. Refer to the corresponding database model
        for details:
            'pool_allocations': netrino_servicetemplate_pool,
            'mappings': netrino_servicetemplate_mappings,
            'user_select':netrino_user_select,
            'task_output':netrino_task_output,
            'static_assignments': netrino_servicetemplate_static,
            'copy_entries': netrino_servicetemplate_copy
        """
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
        except (SQLIntegrityError, FieldError, FieldMissing) as err:
            service_template.delete()
            service_template.commit()
            raise err

        return self.view(req, resp, name)

    def list(self, req, resp):
        """Provides a terse list of Service Templates.
        """
        return sql_list(req, 'netrino_service_template',['id', 'name'])

    def view(self, req, resp, uid):
        """View a Service Template

        This view will include the details of the Models associated to
        this Service Template.

        Args:
            uid (str): UUID of the Service Template to view
        """
        result = OrderedDict()
        with db() as conn:
            cur = conn.execute("SELECT * FROM netrino_service_template "
                               "WHERE name=? OR id=?", (uid,uid,))
            stemplate = cur.fetchone()
            if not stemplate:
                raise HTTPNotFound
            result['id'] = stemplate['id']
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
                        am = ALLOCATIONS[a]()
                        am.sql_id(ae['id'])
                        result['models'][-1][a].append(am)

        return js.dumps(result)

    def update(self, req, resp, uid):
        """Updates a Service Template.

        Note that the Service template will be updated with all the included
        models. To update a specific model entry, include its UUID. Models
        without UUIDs are assumed to be new, and will be added.
        To remove or update a specific Model entry, use DELETE/PUT/PATCH on
        /v1/service-template/{id}/model/{model-id}
        Same goes for Allocations on
        /v1/allocation/{type}/{id}.

        Args:
            uid (str): UUID of the Service Template to update.

        JSON Args:
             name (str): Name of the Service Template
             models (list): List of models for this Service Template
                            See netrino.models.netrino_service_template_entry
        """
        with db() as conn:
            cur = conn.execute("SELECT * FROM netrino_service_template "
                               "WHERE name=? OR id=?", (uid,uid,))
            stemplate = cur.fetchone()
            if not stemplate:
                raise HTTPNotFound
        service_template = netrino_service_template()
        service_template.sql_id(stemplate['id'])
        service_template.update({'name':req.json['name']})
        service_template.commit()
        if 'models' in req.json:
            models = req.json['models']

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

        return self.view(req, resp, uid)

    def delete(self, req, resp, uid):
        """Deletes a Service Template

        Args:
             uid (str): UUID of Service Template to be deleted.
        """
        with db() as conn:
            conn.execute("DELETE FROM netrino_service_template "
                               "WHERE name=? OR id=?", (uid,uid,))
            conn.commit()

    def models(self, req, resp, uid):
        """Provides a terse list of Models associated with a Service Template

        Args:
             uid (str): UUID of the Service Template for which the models are
                        to be listed
        """
        with db() as conn:
            cur = conn.execute("SELECT * FROM netrino_service_template_entry "
                               "WHERE service_template=?", (uid,))
            return raw_list(req,cur.fetchall())

    def view_model(self, req, resp, uid, mid):
        """Returns a terse view of a specific Model Entry.

        Args:
             uid (str): UUID of the Service Request to which the Model belongs.
             mid (str): UUID of the Model Entry
        """
        entry = netrino_service_template_entry()
        entry.sql_id(mid)

        entry = entry.transaction
        # Adding element name so that Select forms can use this as
        # 'selected' option
        sql = 'SELECT netrino_element.name FROM netrino_element,' \
              'netrino_service_template_entry WHERE ' \
              'netrino_service_template_entry.id=? AND ' \
              'netrino_element.id=netrino_service_template_entry.element'
        with db() as conn:
            try:
                name = conn.execute(sql, mid).fetchone()['name']
                entry['element_name'] = name
            except TypeError:
                entry['element_name'] = None

        return entry

    def create_model(self, req, resp, uid):
        """Adds a Model entry to an existing Service request

        (The same can be achieved by updating a Serivce request with a model
        entry that does not contain a UUID)

        Args:
            uid (str): UUID of the Service Template to which this Model entry
                       will be associated.

        JSON Args:
             entry_no (int): Entry number in the Service Template.
             yang_model (str): Katalog location for the YANG model.
             interface (str): Interface to use with element.
                              (Default="netconf". Not required if element or
                              element_tag not present)
            element (str): Uuid of Element.
            element_tag (str): Tag associated with Element. Means user will
                               have option to choose element during service
                               creation.
        """
        entry = netrino_service_template_entry()
        req.json['service_template'] = uid
        entry.update(req.json)
        entry.commit()
        return self.view_model(req, resp, uid, entry['id'])

    def update_model(self, req, resp, uid, mid):
        """Updates a Model entry of an existing Service request.

            (The same can be achieved by updating a Serivce request by simply
            including the UUID of this model entry)

            Args:
                uid (str): UUID of the Service Template to which this Model
                           entry is associated.
                mid (str): UUID of the YANG model entry.

            JSON Args:
                 entry_no (int): Entry number in the Service Template.
                 yang_model (str): Katalog location for the YANG model.
                 interface (str): Interface to use with element.
                                  (Default="netconf". Not required if element or
                                  element_tag not present)
                element (str): Uuid of Element.
                element_tag (str): Tag associated with Element. Means user will
                                   have option to choose element during service
                                   creation.
        """
        entry = netrino_service_template_entry()
        entry.sql_id(mid)
        entry.update(req.json)
        entry.commit()
        return self.view_model(req, resp, uid, mid)

    def delete_model(self, req, resp, uid, mid):
        """Deletes a YANG model entry from a Service Template.

        Args:
            uid (str): UUID of the Service Template to which this Model
                       entry is associated.
            mid (str): UUID of the YANG model entry.
        """
        entry = netrino_service_template_entry()
        entry.sql_id(mid)
        entry.delete()
        entry.commit()

    def allocations(self, req, resp, uid, mid, atype=None):
        """Provides a list of all the auto-allocation settings for a YANG
           model entry of a Service Template.

        If 'atype' is not specified, all of the following categories are
        returned:
        'pool-allocations','mappings', 'user-select',
        'task-output', 'static-assignments'.

        Args:
            uid (str): UUID of the Service Template to which this Model
                       entry is associated.
            mid (str): UUID of the YANG model entry to be queried.
            atype: (str): (Optional) Show only this allocation type. See
                          netrino.helpers.service_template.ALLOCATIONS
        """
        result = {}
        sql = "SELECT * FROM %s WHERE servicetemplate_entry=?"
        with db() as conn:
            if not atype:
                for a in ALLOCATIONS:
                    cur = conn.execute(sql % ALLOCATIONS[a].__name__, (mid,))
                    result[a] = cur.fetchall()
            else:
                cur = conn.execute(sql % ALLOCATIONS[atype].__name__, (mid,))
                result = raw_list(req, cur.fetchall())

        return result

    def view_allocation(self, req, resp, atype, aid):
        """Returns the entry for a specific allocation setting.

        Args:
            atype (str): The Allocation type (one of 'pool-allocations',
                         'mappings', 'user-select', 'task-output' or
                         'static-assignments')
            aid (str): UUID of the specific allocation entry.
        """
        entry = ALLOCATIONS[atype.replace('-','_')]()
        entry.sql_id(aid)
        return entry

    def update_allocation(self, req, resp, atype, aid):
        """Updates an entry for an allocation setting.

        Args:
            atype (str): The Allocation type (one of 'pool-allocations',
                         'mappings', 'user-select', 'task-output' or
                         'static-assignments')
            aid (str): UUID of the specific allocation entry.
        """
        entry = ALLOCATIONS[atype]()
        entry.sql_id(aid)
        entry.update(req.json)
        entry.commit()
        return self.view_allocation(req, resp, atype, aid)

    def delete_allocation(self, req, resp, atype, aid):
        entry = ALLOCATIONS[atype]()
        entry.sql_id(aid)
        entry.delete()
        entry.commit()
