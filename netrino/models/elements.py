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

from luxon import database_model
from luxon import SQLModel
from luxon import Uuid
from luxon import Text
from luxon import DateTime
from luxon import Boolean
from luxon import Index
from luxon import UniqueIndex
from luxon import Fqdn
from luxon import ForeignKey
from infinitystone.models.domains import luxon_domain


from luxon.utils.timezone import now

@database_model()
class luxon_element(SQLModel):
    id = Uuid(default=uuid4, internal=True)
    parent_id = Uuid()
    name = Text(null=False)
    ipv4 = Text()
    ipv6 = Text()
    enabled = Boolean(default=True)
    domain = Fqdn(internal=True)
    creation_time = DateTime(default=now, readonly=True)
    primary_key = id
    element_domain_ref = ForeignKey(domain, luxon_domain.name)
    unique_element_ipv4 = UniqueIndex(ipv4)
    unique_element_ipv6 = UniqueIndex(ipv6)
    elements = Index(id)

@database_model()
class luxon_element_driver(SQLModel):
    id = Uuid(default=uuid4, internal=True)
    element_id = Uuid(null=False)
    driver = Text(null=False)
    creation_time = DateTime(default=now, readonly=True)
    element_ref = ForeignKey(element_id, luxon_element.id)
    unique_element_driver = UniqueIndex(element_id, driver)
    element_driver = Index(element_id, driver)
    primary_key = id
