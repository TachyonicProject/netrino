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
from luxon import SQLModel
from luxon.utils.timezone import now

@register.model()
class netrino_prefix(SQLModel):
    id = SQLModel.Uuid(internal=True, default=uuid4)
    a1 = SQLModel.BigInt()
    a2 = SQLModel.BigInt()
    a3 = SQLModel.BigInt()
    a4 = SQLModel.BigInt(null=False)
    name = SQLModel.Text(null=False)
    parent = SQLModel.Uuid()
    version = SQLModel.Integer(default=4)
    free = SQLModel.Boolean()
    rib = SQLModel.String()
    prefix_len = SQLModel.Integer()
    type = SQLModel.String(null=True)
    creation_time = SQLModel.DateTime(default=now, readonly=True)
    prefix_indices = SQLModel.Index(name,a1,a2,a3,a4,prefix_len,rib,type)
    primary_key = id


@register.model()
class netrino_prefix_tag(SQLModel):
    id = SQLModel.Uuid(default=uuid4, internal=True)
    prefix = SQLModel.String()
    tag = SQLModel.Text(null=False)
    creation_time = SQLModel.DateTime(default=now, readonly=True)
    unique_prefix_tag = SQLModel.UniqueIndex(prefix, tag)
    prefix_tag_prefix_ref = SQLModel.ForeignKey(prefix, netrino_prefix.id)
    primary_key = id
