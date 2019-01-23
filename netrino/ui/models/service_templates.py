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
from luxon import Model
from luxon.utils.timezone import now

# from infinitystone.models.elements import infinitystone_element
# from infinitystone.models.elements import infinitystone_element_tag

@register.model()
class netrino_service_template(Model):
    id = Model.Uuid(default=uuid4, internal=True)
    name = Model.String(null=False)
    creation_time = Model.DateTime(default=now, readonly=True)

@register.model()
class netrino_service_template_entry(Model):
    id = Model.Uuid(default=uuid4, internal=True)
    service_template = Model.Uuid(hidden=True)
    entry_no = Model.Integer(null=False)
    yang_model = Model.Enum(null=False)
    element = Model.Uuid(null=True,
                           data_url='/v1/elements',
                           data_endpoint='orchestration')
    interface = Model.Uuid(default="netconf",
                           data_url='/v1/interfaces',
                           data_endpoint='orchestration')
    function = Model.Text(default="config")
    method = Model.Text()
    element_tag = Model.String(null=True)
    creation_time = Model.DateTime(default=now, readonly=True)

@register.model()
class netrino_servicetemplate_pool(Model):
    id = Model.Uuid(default=uuid4, internal=True)
    path = Model.String(null=False)
    type = Model.String(null=False)
    pool = Model.String(null=False)
    servicetemplate_entry = Model.Uuid(null=False, hidden=True)

@register.model()
class netrino_servicetemplate_mappings(Model):
    id = Model.Uuid(default=uuid4, internal=True)
    path = Model.String(null=False)
    mapper = Model.String(null=False)
    mapper_data = Model.Json()
    servicetemplate_entry = Model.Uuid(null=False, hidden=True)

@register.model()
class netrino_user_select(Model):
    id = Model.Uuid(default=uuid4, internal=True)
    path = Model.String(null=False)
    name = Model.String()
    description = Model.String()
    type = Model.String(default='text')
    url = Model.String()
    endpoint = Model.String()
    servicetemplate_entry = Model.Uuid(null=False, hidden=True)

@register.model()
class netrino_task_output(Model):
    id = Model.Uuid(default=uuid4, internal=True)
    path = Model.String(null=False)
    entry_no = Model.Integer(null=False)
    output_path = Model.String(null=False)
    servicetemplate_entry = Model.Uuid(null=False, hidden=True)

@register.model()
class netrino_servicetemplate_static(Model):
    id = Model.Uuid(default=uuid4, internal=True)
    path = Model.String(null=False)
    value = Model.String(null=False)
    type = Model.String(default="str")
    servicetemplate_entry = Model.Uuid(null=False, hidden=True)

@register.model()
class netrino_servicetemplate_copy(Model):
    """Used when a copy of an already entered/generated value is to be used.

    When entry_no is ommitted, THIS entry is assumed.
    """
    id = Model.Uuid(default=uuid4, internal=True)
    path = Model.String(null=False)
    source_path = Model.String(null=False)
    entry_no = Model.Integer()
    servicetemplate_entry = Model.Uuid(null=False, hidden=True)

@register.model()
class netrino_custom_resource(Model):
    id = Model.Uuid(default=uuid4, internal=True)
    type = Model.String(null=False)
    name = Model.String(null=False)
    value = Model.String()
    domain = Model.Fqdn(internal=True)
    tenant_id = Model.Uuid(internal=True)
    creation_time = Model.DateTime(default=now, readonly=True)
