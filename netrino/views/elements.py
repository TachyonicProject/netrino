# -*- coding: utf-8 -*-
# Copyright (c) 2018 Christiaan Frans Rademan, David Kruger.
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

from luxon import register
from luxon import router
from luxon import db
from luxon.utils import js
from luxon.utils.pkg import EntryPoints
from luxon.exceptions import NotFoundError
from luxon.exceptions import SQLOperationalError
from luxon.exceptions import SQLProgrammingError
from luxon.helpers.api import raw_list, sql_list, obj
from luxon.helpers.access import validate_access
from luxon.utils.cast import to_list

from netrino.models.elements import netrino_element
from netrino.models.elements import netrino_element_interface
from netrino.helpers.crypto import Crypto


def get_related(eid, table, where):
    if eid is None:
        return []

    sql = "SELECT * FROM %s WHERE %s=?" % (table, where,)

    with db() as conn:
        crsr = conn.execute(sql, eid)
        related = to_list(crsr.fetchall())

    return related

@register.resources()
class Elements(object):
    def __init__(self):
        router.add('GET', '/v1/elements',
                   self.list_elements,
                   tag='services')

        router.add('GET', '/v1/element/{eid}',
                   self.view_element,
                   tag='services')

        router.add('POST', '/v1/element',
                   self.add_element,
                   tag='services')

        router.add('POST', '/v1/element/{eid}',
                   self.add_element,
                   tag='services')

        router.add(['PUT', 'PATCH'], '/v1/element/{eid}',
                   self.update_element,
                   tag='services')

        router.add('DELETE', '/v1/element/{eid}',
                   self.delete_element,
                   tag='services')

        router.add('POST', '/v1/element/{eid}/{interface}',
                   self.add_interface,
                   tag='services')

        router.add(['PATCH', 'PUT'], '/v1/element/{eid}/{interface}',
                   self.update_interface,
                   tag='services')

        router.add('DELETE', '/v1/element/{eid}/{interface}',
                   self.delete_interface,
                   tag='services')

        router.add('GET', '/v1/element/{eid}/{interface}',
                   self.view_interface,
                   tag='services')

        router.add('POST', '/v1/element/{eid}/tag/{tag}',
                   self.add_tag,
                   tag='services')

        router.add('DELETE', '/v1/element/{eid}/tag/{tag}',
                   self.delete_tag,
                   tag='services')

    def list_elements(self, req, resp):
        sql = 'SELECT * FROM netrino_element WHERE domain '
        vals = []

        if req.context_domain:
            sql += '= ?'
            vals.append(req.context_domain)
        else:
            sql += 'is NULL'

        if req.context_tenant_id:
            sql += ' AND tenant_id=?'
            vals.append(req.context_tenant_id)
        else:
            sql += ' AND tenant_id IS NULL'

        with db() as conn:
            elements = conn.execute(sql, vals).fetchall()

        return raw_list(req, elements, context=False)

    def add_element(self, req, resp, eid=None):
        element = obj(req, netrino_element)
        if eid is not None:
            element['parent_id'] = eid
        element.commit()
        return element

    def _get_children(self, req, eid):
        element = netrino_element()
        element.sql_id(eid)
        validate_access(req, element)

        children = []

        for child in get_related(eid, 'netrino_element', 'parent_id'):
            child = {"id": child['id'],
                     "child_name": child['name'],
                     "domain": child['domain'],
                     "tenant_id": child['tenant_id']}
            children.append(child)

        return children

    def _get_interfaces(self, req, eid):
        element = netrino_element()
        element.sql_id(eid)
        validate_access(req, element)

        interfaces = []

        for interface in get_related(eid, 'netrino_element_interface',
                                     'element_id'):
            interface = {"id": interface['interface'],
                         "interface": interface['interface'],
                         "metadata": interface['metadata']}
            interfaces.append(interface)

        return interfaces

    def view_element(self, req, resp, eid):
        view = req.query_params.get('view', False)
        if view:
            if view == 'children':
                children = self._get_children(req, eid)
                return raw_list(req, children, context=False)
            if view == 'interfaces':
                interfaces = self._get_interfaces(req, eid)
                return raw_list(req, interfaces, context=False)

        element = obj(req, netrino_element, sql_id=eid)

        to_return = element.dict

        with db() as conn:
            children = conn.execute("SELECT id, name, enabled, creation_time"
                                      " FROM netrino_element"
                                      " WHERE parent_id = %s", eid).fetchall()
            interfaces = conn.execute("SELECT interface,metadata,creation_time"
                                      " FROM netrino_element_interface"
                                      " WHERE element_id = %s", eid).fetchall()
            tags = conn.execute("SELECT name"
                                      " FROM netrino_element_tag"
                                      " WHERE element_id = %s", eid).fetchall()
            try:
                parent = conn.execute("SELECT name FROM netrino_element "
                                      "WHERE id=%s",
                                      element['parent_id']).fetchone()
                to_return['parent'] = parent
            except (SQLOperationalError, SQLProgrammingError,):
                # when parent_id is None, sqlie raises Operational error,
                # whereas mysql raises Programming
                pass

        to_return['children'] = children
        to_return['interfaces'] = interfaces
        to_return['tags'] = tags

        if element['encrypt_metadata']:
            crypto = Crypto()
            for interfaces in to_return['interfaces']:
                interfaces['metadata'] = crypto.decrypt(interfaces['metadata'])

        for interfaces in to_return['interfaces']:
            interfaces['metadata'] = js.loads(interfaces['metadata'])

        return to_return

    def update_element(self, req, resp, eid):
        element = obj(req, netrino_element, sql_id=eid)
        element.commit()
        return self.view_element(req, resp, eid)

    def delete_element(self, req, resp, eid):
        element = obj(req, netrino_element, sql_id=eid)
        element.commit()
        return element

    def add_interface(self, req, resp, eid, interface):
        metadata_model = EntryPoints('netrino_elements')[interface]()
        metadata_model.update(req.json)
        # Check to see all required data was submittied
        metadata_model._pre_commit()
        metadata = metadata_model.json
        element = netrino_element()
        element.sql_id(eid)
        if element['encrypt_metadata']:
            crypto = Crypto()
            metadata = crypto.encrypt(metadata)
        model = netrino_element_interface()
        model['element_id'] = eid
        model['interface'] = interface
        model['metadata'] = metadata
        model.commit()
        return self.view_interface(req, resp, eid, interface)

    def view_interface(self, req, resp, eid, interface):
        with db() as conn:
            cursor = conn.execute('SELECT interface, metadata, creation_time' +
                                  ' FROM netrino_element_interface' +
                                  ' WHERE element_id = %s' +
                                  ' AND interface = %s', (eid, interface,))
            interface = cursor.fetchone()

            if interface is None:
                raise NotFoundError('Interface not found')

            element = conn.execute('SELECT encrypt_metadata FROM '
                                   'netrino_element WHERE id = %s',
                                   eid).fetchone()

            if element['encrypt_metadata']:
                crypto = Crypto()
                interface['metadata'] = crypto.decrypt(interface['metadata'])

            interface['metadata'] = js.loads(interface['metadata'])

            return interface

    def update_interface(self, req, resp, eid, interface):
        # In case not all fields was submitted,
        # first we grab what we had.
        current = self.view_interface(req, resp, eid, interface)
        crypto = Crypto()
        model = EntryPoints('netrino_elements')[interface]()
        model.update(current['metadata'])
        model.update(req.json)
        model_json = model.json
        with db() as conn:
            element = conn.execute('SELECT encrypt_metadata FROM '
                                   'netrino_element WHERE id = %s',
                                   eid).fetchone()

            if element['encrypt_metadata']:
                model_json = crypto.encrypt(model_json)

            conn.execute('UPDATE netrino_element_interface' +
                         ' SET metadata = %s' 
                         ' WHERE element_id = %s' +
                         ' AND interface = %s', (model_json,
                                                 eid, interface,))
            conn.commit()
        return self.view_interface(req, resp, eid, interface)

    def delete_interface(self, req, resp, eid, interface):
        with db() as conn:
            conn.execute('DELETE FROM netrino_element_interface' +
                         ' WHERE element_id = %s' +
                         ' AND interface = %s', (eid, interface,))
            conn.commit()

    def add_tag(self, req, resp, eid, tag):
        tag_entry_id = str(uuid4())
        with db() as conn:
            conn.execute('INSERT INTO netrino_element_tag' +
                         ' (id, name, element_id)' +
                         ' VALUES' +
                         ' (%s, %s, %s)', (tag_entry_id,tag, eid))
            conn.commit()
            return self.view_element(req, resp, eid)

    def delete_tag(self, req, resp, eid, tag):
        with db() as conn:
            conn.execute('DELETE FROM netrino_element_tag' +
                         ' WHERE element_id = %s' +
                         ' AND name = %s', (eid, tag,))
            conn.commit()
            return self.view_element(req, resp, eid)
