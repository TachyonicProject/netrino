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
from luxon.helpers.api import sql_list, obj
from netrino.models.resources import netrino_custom_resource


@register.resources()
class CustomResource(object):
    def __init__(self):
        router.add('GET', '/v1/resources/custom', self.list, tag='services')
        router.add('POST', '/v1/resources/custom', self.create, tag='services')
        router.add('GET', '/v1/resources/custom/{rid}',
                   self.get, tag='services')
        router.add(['PUT', 'PATCH'], '/v1/resources/custom/{rid}', self.update,
                   tag='roles:admin')
        router.add('DELETE', '/v1/resources/custom/{rid}', self.delete,
                   tag='roles:admin')
        router.add('GET','v1/resource/custom/{rtype}',
                   self.list_custom,
                   tag='services:view')

    def list(self, req, resp):
        """Returns a list of custom resources
        """
        return sql_list(req, 'netrino_custom_resource',
                        sql_fields=('id', 'type', 'name', 'value'))

    def create(self, req, resp):
        resource = obj(req, netrino_custom_resource)
        resource.commit()
        return resource

    def get(self, req, resp, rid):
        return obj(req, netrino_custom_resource, sql_id=rid)

    def update(self, req, resp, rid):
        resource = obj(req, netrino_custom_resource, sql_id=rid)
        resource.commit()
        return resource

    def delete(self, req, resp, rid):
        resource = obj(req, netrino_custom_resource, sql_id=rid)
        resource.commit()
        return resource

    def list_custom(self, req, resp, rtype):
        """Returns a list of custom resources of a specific type
        """
        return sql_list(req, 'netrino_custom_resource', type=rtype, 
                        sql_fields=('id', 'type', 'name', 'value'))






