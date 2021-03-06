# -*- coding: utf-8 -*-
# Copyright (c) 2019 Christiaan Frans Rademan.
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

from netrino.models.processes import netrino_process


@register.model()
class netrino_workflow(SQLModel):
    id = SQLModel.Uuid(default=uuid4, internal=True)
    process_id = SQLModel.Uuid()
    node = SQLModel.Integer(signed=False, null=True)
    node_id = SQLModel.String(null=True)
    node_type = SQLModel.String(null=True)
    node_parent = SQLModel.Integer(signed=False, null=True)
    node_parent_id = SQLModel.String(null=True)
    node_label = SQLModel.String()
    node_description = SQLModel.String()
    node_style = SQLModel.String()
    node_x = SQLModel.Integer(null=True)
    node_y = SQLModel.Integer(null=True)
    node_width = SQLModel.Integer(null=True)
    node_height = SQLModel.Integer(null=True)
    node_source = SQLModel.Integer(null=True)
    node_source_id = SQLModel.String(null=True)
    node_target = SQLModel.Integer(null=True)
    node_target_id = SQLModel.String(null=True)
    node_link_target_x = SQLModel.Integer(null=True)
    node_link_target_y = SQLModel.Integer(null=True)
    node_link_source_x = SQLModel.Integer(null=True)
    node_link_source_y = SQLModel.Integer(null=True)
    node_link_point_x = SQLModel.Integer(null=True)
    node_link_point_y = SQLModel.Integer(null=True)
    node_removed = SQLModel.Boolean(default=False)
    updated_time = SQLModel.DateTime(null=True, internal=True)
    entry_point = SQLModel.String()
    metadata = SQLModel.MediumText(null=True)
    workflow_node_index = SQLModel.Index(node_id)
    workflow_parent_ref = SQLModel.ForeignKey(node_parent_id, node_id)
    workflow_target_ref = SQLModel.ForeignKey(node_target_id, node_id)
    workflow_source_ref = SQLModel.ForeignKey(node_source_id, node_id)
    workflow_process_ref = SQLModel.ForeignKey(process_id, netrino_process.id)
    workflow_unique_obj = SQLModel.UniqueIndex(process_id, node_id)
    primary_key = id
