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
from psychokinetic.utils.api import sql_list, obj

from netrino.models.elements import netrino_element
from netrino.models.elements import netrino_element_interface


@register.resources()
class Elements(object):
    def __init__(self):
        router.add('GET', '/v1/elements',
                   self.list_elements,
                   tag='infrastructure:view')

        router.add('GET', '/v1/element/{eid}',
                   self.view_element,
                   tag='infrastructure:view')

        router.add('POST', '/v1/element',
                   self.add_element,
                   tag='infrastructure:admin')

        router.add('POST', '/v1/element/{eid}',
                   self.add_element,
                   tag='infrastructure:admin')

        router.add(['PUT', 'PATCH'], '/v1/element/{eid}',
                   self.update_element,
                   tag='infrastructure:admin')

        router.add('DELETE', '/v1/element/{eid}',
                   self.delete_element,
                   tag='infrastructure:admin')

        router.add('POST', '/v1/element/{eid}/{interface}',
                   self.add_interface,
                   tag='infrastructure:admin')

        router.add(['PATCH', 'PUT'], '/v1/element/{eid}/{interface}',
                   self.update_interface,
                   tag='infrastructure:admin')

        router.add('DELETE', '/v1/element/{eid}/{interface}',
                   self.delete_interface,
                   tag='infrastructure:admin')

        router.add('GET', '/v1/element/{eid}/{interface}',
                   self.view_interface,
                   tag='infrastructure:view')

    def list_elements(self, req, resp):
        return sql_list(req, 'netrino_element', ('id', 'parent_id', 'name',
                                                 'enabled', 'creation_time',),
                       parent_id=None)

    def add_element(self, req, resp, eid=None):
        element = obj(req, netrino_element)
        if eid is not None:
            element['parent_id'] = eid
        element.commit()
        return element

    def view_element(self, req, resp, eid):
        element = obj(req, netrino_element, sql_id=eid)
        children = sql_list(req, 'netrino_element', ('id', 'parent_id', 'name',
                                                     'enabled', 'creation_time',),
                            parent_id=eid, limit=0)
        interfaces = sql_list(req, 'netrino_element_interface', ('id',
                                                                 'interface',
                                                                 'metadata',),
                              element_id=eid, limit=0)
        to_return = element.dict
        to_return['children'] = children
        to_return['interfaces'] = interfaces

        for interfaces in to_return['interfaces']['payload']:
            interfaces['metadata'] = js.loads(interfaces['metadata'])

        return to_return

    def update_element(self, req, resp, eid):
        element = obj(req, netrino_element, sql_id=eid)
        element.commit()
        children = sql_list(req, 'netrino_element', ('id', 'parent_id', 'name',
                                                     'enabled', 'creation_time',),
                            parent_id=eid, limit=0)
        interfaces = sql_list(req, 'netrino_element_interface', ('id',
                                                                 'interface',
                                                                 'metadata',),
                              element_id=eid, limit=0)
        to_return = element.dict
        to_return['children'] = children
        to_return['interfaces'] = interfaces
        return to_return

    def delete_element(self, req, resp, id):
        element = obj(req, netrino_element, sql_id=id)
        element.commit()
        return element

    def add_interface(self, req, resp, eid, interface):
        model = EntryPoints('netrino_elements')[interface]()
        model.update(req.json)
        with db() as conn:
            uuid = str(uuid4())
            conn.execute('INSERT INTO netrino_element_interface' +
                         ' (id, element_id, interface, metadata)' +
                         ' VALUES' +
                         ' (%s, %s, %s, %s)',
                         (uuid, eid, interface, model.json))
            conn.commit()
            return self.view_interface(req, resp, eid, interface)

    def view_interface(self, req, resp, eid, interface):
        with db() as conn:
            cursor = conn.execute('SELECT * FROM netrino_element_interface' +
                                  ' WHERE element_id = %s' +
                                  ' AND interface = %s', (eid, interface,))
            interface = cursor.fetchone()

            if interface is None:
                raise NotFoundError('Interface not found')

            interface['metadata'] = js.loads(interface['metadata'])
            return interface

    def update_interface(self, req, resp, eid, interface):
        model = EntryPoints('netrino_elements')[interface]()
        model.update(req.json)
        with db() as conn:
            conn.execute('UPDATE netrino_element_interface' +
                         ' SET metadata = %s' 
                         ' WHERE element_id = %s' +
                         ' AND interface = %s', (model.json, eid, interface,))
            conn.commit()
        return self.view_interface(req, resp, eid, interface)

    def delete_interface(self, req, resp, eid, interface):
        with db() as conn:
            conn.execute('DELETE FROM netrino_element_interface' +
                         ' WHERE element_id = %s' +
                         ' AND interface = %s', (eid, interface,))
            conn.commit()


