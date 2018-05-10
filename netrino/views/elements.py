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
import json

from luxon import register_resource
from luxon import db
from infinitystone.utils.api import model
from netrino.models.elements import luxon_element
from netrino.models.elements import luxon_element_driver


@register_resource('GET', '/v1/elements', 'operations')
def list_elements(req, resp):
    """List all Elements

    Returns:
         List of available Elements
    """
    elements = model(luxon_element)
    return elements

@register_resource('POST', '/v1/element', 'operations')
def add_element(req, resp):
    """Add Element

    Args:
         name (str): Name of the Element.
         ipv4 (str): IPv4 address to manage element.
         ipv6 (str): IPv6 address to manage element.
         driver (str): Python library that is used to communicate to element.
         domain (str): Domain if element is to be created inside a domain.
         enabled (bool): Set to false to make inactive (default is True)

    Returns:
        Completed model of element in case createion was successful.
    """
    element = model(luxon_element, values=req.json)
    element.commit()
    return element

@register_resource(['PUT', 'PATCH'], '/v1/element/{id}', 'operations')
def update_element(req, resp, id):
    """Add Element

    Args:
         name (str): Name of the Element.
         ipv4 (str): IPv4 address to manage element.
         ipv6 (str): IPv6 address to manage element.
         driver (str): Python library that is used to communicate to element.
         domain (str): Domain if element is to be created inside a domain.
         enabled (bool): Set to false to make inactive (default is True)

    Returns:
        Completed model of element in case creation was successful.
    """
    element = model(luxon_element, id=id, values=req.json)
    element.commit()
    return element

@register_resource('DELETE', '/v1/element/{id}', 'operations')
def update_element(req, resp, id):
    """Remove an Element.

    Returns:
         200 OK if successful.
    """
    element = model(luxon_element, id=id)
    element.delete()

@register_resource('POST', '/v1/element/{id}/driver', 'operations')
def add_element_driver(req, resp, id):
    """Add Element Driver

    Args:
         id (str): UUID of the Element.
         driver (str): Name of the driver.

    Returns:
        Completed model of element_driver in case creation was successful.
    """
    req.json['element_id'] = id
    from luxon import GetLogger
    log = GetLogger(__name__)
    driver = model(luxon_element_driver, values=req.json)
    driver.commit()
    return driver

@register_resource('DELETE', '/v1/element/{id}/driver/{driver}', 'operations')
def delete_element_driver(req, resp, id, driver):
    """Delete Element Driver

    Args:
         id (str): UUID of the Element.
         driver (str): Name of the driver.

    Returns:
        200 OK if successful.
    """
    values = {'element_id': id, "driver": driver}
    driver = model(luxon_element_driver, values=values)
    driver.delete()

@register_resource('GET', '/v1/element/{id}/drivers', 'operations')
def view_element_driver(req, resp, id):
    """View Element Driver

    Args:
         id (str): UUID of the Element.

    Returns:
        instance of luxon_element_driver model.
    """
    sql = "SELECT * FROM luxon_element_driver WHERE element_ID=?"
    with db() as cur:
        results = cur.execute(sql, id).fetchall()
    return json.dumps(results)
