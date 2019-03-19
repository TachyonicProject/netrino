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
from lxml import objectify
from luxon import router
from luxon import register
from luxon.constants import APPLICATION_XML


@register.resources()
class Workflow():
    def __init__(self):
        router.add('GET',
                   '/workflow/{process_id}',
                   self.get_workflow)

        router.add('PUT',
                   '/workflow/{process_id}',
                   self.update_workflow)

    def get_workflow(self, req, resp, process_id):
        resp.content_type = APPLICATION_XML
        empty = """<mxGraphModel>
    <root>
        <Workflow label="MyWorkflow" description="" id="0"/>
        <Layer label="Default Layer" description="">
            <mxCell parent="0"/>
        </Layer>
    </root>
</mxGraphModel>"""
        graph = """
<mxGraphModel><root><Workflow label="MyWorkflow" description="" id="0"><mxCell/></Workflow><Layer label="Default Layer" description="" id="1"><mxCell parent="0"/></Layer><Task label="Task" description="" href="" id="11"><mxCell vertex="1" parent="1"><mxGeometry x="150" y="100" width="72" height="32" as="geometry"/></mxCell></Task><Task label="Task" description="" href="" id="12"><mxCell vertex="1" parent="1"><mxGeometry x="300" y="160" width="72" height="32" as="geometry"/></mxCell></Task><Edge label="" description="" id="13"><mxCell style="straightEdge" edge="1" parent="1" source="11" target="12"><mxGeometry relative="1" as="geometry"/></mxCell></Edge><Task label="Task" description="" href="" id="14"><mxCell vertex="1" parent="1"><mxGeometry x="80" y="180" width="72" height="32" as="geometry"/></mxCell></Task><Edge label="" description="" id="15"><mxCell style="straightEdge" edge="1" parent="1" source="11" target="14"><mxGeometry relative="1" as="geometry"/></mxCell></Edge><Task label="Task" description="" href="" id="16"><mxCell vertex="1" parent="1"><mxGeometry x="210" y="240" width="72" height="32" as="geometry"/></mxCell></Task><Edge label="" description="" id="17"><mxCell edge="1" parent="1" source="14" target="16"><mxGeometry relative="1" as="geometry"/></mxCell></Edge></root></mxGraphModel>
"""
        return graph

    def update_workflow(self, req, resp, process_id):
        resp.content_type = APPLICATION_XML
        objectify.fromstring(req.read())

        return None
