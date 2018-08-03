# -*- coding: utf-8 -*-
# Copyright (c) 2018 Dave Kruger.
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

from luxon import db
from luxon.exceptions import FieldMissing


def get_element_metadata(uuid, interface):
    """Finds element login metadata for a given uuid.

    Args:
        uuid(str): Uuid of the element.
        interface(str): The Interface in question.

    Returns:
        dict build from json fetched from the database, if any, else None.
    """
    with db() as cur:
        sql = 'SELECT metadata FROM netrino_element_interface WHERE ' \
              'id=? AND interface=?'
        result = cur.execute(sql, (uuid, interface))
        result = result.fetchone()
    if result:
        return json.loads(result['metadata'])
    return None

def getScope(req, infinitystone=[], one_of=[], all_of=[]):
    """Gets scope from luxon wsgi req obj's json attribute.

    Args:
        req (obj): luxon.core.handlers.wsgi.request.Request obj with json
                   attribute
        infinitystone (list): list of keys to be obtained from infinitystone
                              context. May contain 'domain', 'interface',
                              'tenant_id', and 'region'
        one_of (list): list of keys to look for in req.json. Will raise
                       FieldMissing error if none of them are found.
        all_of (list): list of keys to look for in req.json. Will raise
                       FieldMissing error if one of them are not present.

    Returns:
        dict containing domain, tenant_id, interface and region obtained from
        context, and other keys as retrieved from req.json
    """
    scope = {}
    gotOne = False
    gotAll = True

    for key in infinitystone:
        scope[key] = getattr(req,'context_'+key)

    for key in one_of:
        try:
            scope[key] = req.json[key]
            gotOne = True
        except KeyError:
            pass

    for key in all_of:
        try:
            scope[key] = req.json[key]
        except KeyError:
            gotAll = False

    if not gotOne and one_of:
        raise FieldMissing(field="%s" % one_of,
                           label="Scope",
                           description="At least one is required")
    if not gotAll:
        raise FieldMissing(field="%s" % all_of,
                           label="Scope",
                           description="All is required")

    return scope
