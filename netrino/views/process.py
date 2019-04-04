# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 Christiaan Frans Rademan.
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
from luxon import GetLogger
from luxon import router
from luxon import register
from luxon import db
from luxon.constants import APPLICATION_XML
from luxon.helpers.api import sql_list, obj
from luxon.exceptions import SQLIntegrityError, HTTPBadRequest

from netrino.utils.mxgraph import MxChangeDecoder, mxgraph
from netrino.models.processes import netrino_process

log = GetLogger(__name__)


@register.resources()
class Workflow():
    def __init__(self):
        router.add('GET', '/v1/process/{process_id}',
                   self.get_process,
                   tag='process:admin')
        router.add('GET', '/v1/processes',
                   self.get_processes,
                   tag='process:view')
        router.add('POST', '/v1/process',
                   self.post_process,
                   tag='process:admin')
        router.add(['PUT', 'PATCH'], '/v1/process/{process_id}',
                   self.put_process,
                   tag='process:admin')
        router.add('DELETE', '/v1/process/{process_id}',
                   self.delete_process,
                   tag='process:admin')

        router.add('GET',
                   '/v1/workflow/{process_id}',
                   self.get_workflow,
                   tag='process:admin')
        router.add('PUT',
                   '/v1/workflow/{process_id}',
                   self.update_workflow,
                   tag='process:admin')

    def get_process(self, req, resp, process_id):
        return obj(req, netrino_process, sql_id=process_id)

    def get_processes(self, req, resp):
        return sql_list(req,
                        'netrino_process',
                        fields=('id',
                                'name',),
                        search={'id': str,
                                'name': str})

    def post_process(self, req, resp):
        process = obj(req, netrino_process)
        process.commit()
        with db() as conn:
            node_id = "1/%s" % process['id']
            sql = "INSERT INTO netrino_workflow"
            sql += " (id, process_id, node, node_id, node_type, updated_time)"
            sql += " VALUES"
            sql += " (uuid(), %s, 1, %s, 'root', now())"
            conn.execute(sql, (process['id'], node_id,))
            conn.commit()

        return process

    def put_process(self, req, resp, process_id):
        user = obj(req, netrino_process, sql_id=process_id)
        user.commit()
        return user

    def delete_process(self, req, resp, process_id):
        user = obj(req, netrino_process, sql_id=process_id)
        user.commit()

    def get_workflow(self, req, resp, process_id):
        resp.content_type = APPLICATION_XML
        with db() as conn:
            conn.execute('DELETE FROM netrino_workflow' +
                         ' WHERE process_id = %s' +
                         ' AND (node_removed = 1' +
                         ' OR node_type is NULL)', process_id)
            conn.commit()
            graph = conn.execute('SELECT * FROM netrino_workflow' +
                                 ' WHERE process_id = %s' +
                                 ' AND node_removed = 0',
                                 process_id).fetchall()
            conn.commit()
            return mxgraph(graph)

    def update_workflow(self, req, resp, process_id):
        resp.content_type = APPLICATION_XML
        decoder = MxChangeDecoder(req.read(), process_id)
        changes = decoder.parse()
        with db() as conn:
            try:
                for change in changes:
                    values = [process_id]
                    sql = "INSERT INTO netrino_workflow ("
                    sql += "id"
                    sql += ", process_id"
                    sql += ", updated_time"
                    for attr in change:
                        sql += ", %s" % attr
                        values.append(change[attr])
                    sql += ") VALUES ("
                    sql += "uuid(), %s, now()"
                    for attr in change:
                        sql += ", %s"
                    sql += ") ON DUPLICATE KEY UPDATE"
                    sql += " process_id = %s,"
                    sql += " updated_time = now()"
                    for attr in change:
                        sql += ", %s = %s" % (attr, '%s',)
                    conn.execute(sql, values+values)
                conn.commit()
            except SQLIntegrityError:
                resp.content_type = 'APPLICATION_JSON'
                raise HTTPBadRequest('Graph modified and not in sync')
        return None
