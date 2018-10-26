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

from luxon import register
from luxon import router
from luxon import db
from luxon.utils.pkg import EntryPoints
from luxon.exceptions import NotFoundError

from netrino.helpers.service_template import populate_req_json


@register.resources()
class SerivceRequests(object):
    def __init__(self):
        router.add('POST', '/v1/service-request', self.create, tag='customer')
        router.add('GET', '/v1/service-request/{srid}',
                   self.get, tag='customer')

    def create(self, req, resp):
        srid = str(uuid4())
        req.json['id'] = srid
        populate_req_json()
        return req.json
        # Todo: Run through the entries and execute them.
        # stemplate = req.json['service_template']
        # esql = 'SELECT * FROM netrino_service_template_entry ' \
        #       'WHERE service_template=? ORDER BY entry_no'
        # with db() as conn:
        #     entries = conn.execute(esql, stemplate).fetchall()
        # netrino_interface = EntryPoints('netrino_interfaces')
        # for e in entries:
        #     try:
        #         with netrino_interface[e['interface']](e['element']) as obj:
        #             method = getattr(obj, property)
        #             return method(req)
        #     except KeyError:
        #         raise NotFoundError(
        #             "Interface '%s' not registered" % e['interface'])

    def get(self, req, resp, srid):
        # Must repond with list of task id's for each model entry
        result= {"tasks": {}}
        result['tasks'][2] = {"result": {"virtual-network": {'uuid':"fake-uuid"}}}
        return result






