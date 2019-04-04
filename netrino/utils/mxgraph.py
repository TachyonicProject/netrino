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
from lxml import objectify, etree

from luxon import GetLogger

log = GetLogger(__name__)


def mxgraph(result):
    result = sorted(result, key=lambda i: i['node'])

    def process_obj(obj):
        if obj['node_type']:
            user_obj = etree.SubElement(
                root, obj['node_type'],
                id=str(obj['node']),
                label=str(obj['node_label']),
                description=str(obj['node_description']),
                href='')
            mxcell_attribs = {}
            if obj['node_type'] != 'Edge':
                mxcell_attribs['vertex'] = "1"
            else:
                mxcell_attribs['edge'] = "1"

            if obj['node_style']:
                mxcell_attribs['style'] = str(obj['node_style'])

            if obj['node_parent']:
                mxcell_attribs['parent'] = str(obj['node_parent'])

            if obj['node_source']:
                mxcell_attribs['source'] = str(obj['node_source'])

            if obj['node_target']:
                mxcell_attribs['target'] = str(obj['node_target'])

            mxcell = etree.SubElement(user_obj, 'mxCell', **mxcell_attribs)
            mxgeo_attribs = {}

            if obj['node_x']:
                mxgeo_attribs['x'] = str(obj['node_x'])
                mxgeo_attribs['y'] = str(obj['node_y'])
                mxgeo_attribs['height'] = str(obj['node_height'])
                mxgeo_attribs['width'] = str(obj['node_width'])
            else:
                mxgeo_attribs['relative'] = "1"
            mxgeo_attribs['as'] = 'geometry'

            mxgeo = etree.SubElement(mxcell, 'mxGeometry', **mxgeo_attribs)

            if obj['node_link_source_x']:
                attribs = {'x': str(obj['node_link_source_x']),
                           'y': str(obj['node_link_source_y']),
                           'as': 'sourcePoint'}
                etree.SubElement(mxgeo, 'mxPoint', **attribs)
            if obj['node_link_target_x']:
                attribs = {'x': str(obj['node_link_target_x']),
                           'y': str(obj['node_link_target_y']),
                           'as': 'targetPoint'}
                etree.SubElement(mxgeo, 'mxPoint', **attribs)
            if obj['node_link_point_x']:
                points = mxcell = etree.SubElement(mxgeo, 'Array',
                                                   **{'as': 'points'})
                attribs = {'x': str(obj['node_link_point_x']),
                           'y': str(obj['node_link_point_y'])}
                etree.SubElement(points, 'mxPoint', **attribs)

    model = etree.Element('mxGraphModel')
    xml = etree.ElementTree(model)
    root = etree.SubElement(model, 'root')
    workflow = etree.SubElement(root, 'Workflow',
                                id='0',
                                label='Process',
                                description='')
    etree.SubElement(workflow, 'mxCell')
    layer = etree.SubElement(root, 'Layer',
                             id='1',
                             label='Process Layer',
                             description='')
    etree.SubElement(layer, 'mxCell',
                     parent="0")

    for obj in result:
        if obj['node_type'] != 'root' and obj['node_type'] == 'Swimlane':
            process_obj(obj)
    for obj in result:
        if (obj['node_type'] != 'root' and obj['node_type'] != 'Edge' and
                obj['node_type'] != 'Swimlane'):
            process_obj(obj)
    for obj in result:
        if obj['node_type'] != 'root' and obj['node_type'] == 'Edge':
            process_obj(obj)

    return etree.tostring(xml).decode()


class MxChangeDecoder(object):
    OBJECTS = ('Task', 'Merge', 'Fork',
               'Event', 'EventEnd', 'Edge',
               'Swimlane', )

    def __init__(self, xml, unique_id):
        self._root = objectify.fromstring(xml)
        self._unique_id = unique_id

    def _id(self, obj_id):
        if obj_id is not None:
            return "%s/%s" % (obj_id, self._unique_id,)
        return None

    def parse(self, element=None):
        if element is None:
            changes = []
            for e in self._root.getchildren():
                changes.append(self.parse(e))
            return changes
        else:
            obj = {}
            if not isinstance(element, list):
                element = [element]
            for e in element:
                if e.tag == 'mxChildChange':
                    obj['node_removed'] = 0
                    if 'parent' in e.attrib:
                        obj['node_parent'] = e.attrib.get('parent')
                        obj['node_parent_id'] = self._id(
                            e.attrib.get('parent'))
                        obj['node_removed'] = 0
                    elif 'previous' in e.attrib:
                        obj['node_parent'] = e.attrib.get('previous')
                        obj['node_parent_id'] = self._id(
                            e.attrib.get('previous'))
                        obj['node_removed'] = 1
                    obj['node'] = e.attrib.get('child')
                    obj['node_id'] = self._id(e.attrib.get('child'))
                    obj = {**obj, **self.parse(e.getchildren())}
                elif e.tag in self.OBJECTS:
                    obj['node'] = e.attrib.get('id')
                    obj['node_id'] = self._id(e.attrib.get('id'))
                    obj['node_type'] = e.tag
                    obj['node_label'] = e.attrib.get('label')
                    obj['node_description'] = e.attrib.get('description')
                    obj = {**obj, **self.parse(e.getchildren())}
                elif e.tag == 'mxCell':
                    obj['node_style'] = e.attrib.get('style')
                    obj['node_parent'] = e.attrib.get('parent')
                    obj['node_parent_id'] = self._id(
                        e.attrib.get('parent'))
                    obj['node_source'] = e.attrib.get('source')
                    obj['node_source_id'] = self._id(
                        e.attrib.get('source'))
                    obj['node_target'] = e.attrib.get('target')
                    obj['node_target_id'] = self._id(
                        e.attrib.get('target'))
                    obj['node_link_point_x'] = None
                    obj['node_link_point_y'] = None
                    obj['node_link_source_x'] = None
                    obj['node_link_source_y'] = None
                    obj['node_link_point_x'] = None
                    obj['node_link_point_y'] = None
                    obj['node_link_target_x'] = None
                    obj['node_link_target_y'] = None

                    if obj['node_source'] or obj['node_target']:
                        obj['node_type'] = 'Edge'

                    obj = {**obj, **self.parse(e.getchildren())}
                elif e.tag == 'mxGeometry':
                    obj['node_x'] = e.attrib.get('x')
                    obj['node_y'] = e.attrib.get('y')
                    obj['node_height'] = e.attrib.get('height')
                    obj['node_width'] = e.attrib.get('width')
                    obj = {**obj, **self.parse(e.getchildren())}
                elif e.tag == 'mxGeometryChange':
                    obj['node'] = e.attrib.get('cell')
                    obj['node_id'] = self._id(e.attrib.get('cell'))
                    obj = {**obj, **self.parse(e.getchildren())}
                elif e.tag == 'mxPoint':
                    obj['node_type'] = 'Edge'
                    if e.attrib.get('as') == 'sourcePoint':
                        obj['node_link_source_x'] = e.attrib.get('x')
                        obj['node_link_source_y'] = e.attrib.get('y')
                    elif e.attrib.get('as') == 'targetPoint':
                        obj['node_link_target_x'] = e.attrib.get('x')
                        obj['node_link_target_y'] = e.attrib.get('y')
                    else:
                        log.warning('MxChangeDecoder unknown MxPoint as value')
                elif e.tag == 'mxTerminalChange':
                    obj['node_type'] = 'Edge'
                    obj['node'] = e.attrib.get('cell')
                    obj['node_id'] = self._id(e.attrib.get('cell'))
                    if e.attrib['source'] == "1":
                        obj['node_source'] = e.attrib.get('terminal')
                        obj['node_source_id'] = self._id(
                            e.attrib.get('terminal'))
                        if obj['node_source'] is not None:
                            obj['node_link_point_x'] = None
                            obj['node_link_point_y'] = None
                            obj['node_link_source_x'] = None
                            obj['node_link_source_y'] = None
                            # obj['node_link_target_x'] = None
                            # obj['node_link_target_y'] = None
                    else:
                        obj['node_target'] = e.attrib.get('terminal')
                        obj['node_target_id'] = self._id(
                            e.attrib.get('terminal'))
                        if obj['node_target'] is not None:
                            obj['node_link_point_x'] = None
                            obj['node_link_point_y'] = None
                            # obj['node_link_source_x'] = None
                            # obj['node_link_source_y'] = None
                            obj['node_link_target_x'] = None
                            obj['node_link_target_y'] = None

                    obj = {**obj, **self.parse(e.getchildren())}
                elif e.tag == 'Array':
                    if e.attrib.get('as') == 'points':
                        # We only support one point in connector/edge.
                        for point in e.getchildren():
                            obj['node_link_point_x'] = point.attrib.get('x')
                            obj['node_link_point_y'] = point.attrib.get('y')
                else:
                    log.warning("MxChangeDecoder unknown tag '%s'" % (e.tag,) +
                                " with attributes '%s'" % (str(e.attrib),))
            return obj
