# -*- coding: utf-8 -*-
# Copyright (c) 2018 Christiaan Frans Rademan.
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

from luxon import register
from luxon import router
from luxon import db
from luxon.utils import js

from pyipcalc import (IPNetwork,
                      ip_to_int,
                      int_to_ip,
                      int_64_to_128,
                      int_128_to_64)

from netrino.models.ipam import netrino_ipam


def format_prefix(prefix):
    pf = {}
    pf['id'] = prefix['id']
    pf['parent_id'] = prefix['parent_id']
    pf['version'] = prefix['version']
    if prefix['version'] == 4:
        pf['prefix'] = int_to_ip(prefix['ipdec1'])
    else:
        ipdec = int_64_to_128(prefix['ipdec1'],
                              prefix['ipdec2'])
        pf['prefix'] = int_to_ip(ipdec, 6)

    pf['length'] = prefix['length']
    return pf


@register.resources()
class IPam(object):
    def __init__(self):
        router.add('GET', '/v1/prefixes/{version}',
                   self.list_prefixes,
                   tag='infrastructure:view')

        router.add('GET', '/v1/prefix/{pid}',
                   self.view_prefix,
                   tag='infrastructure:view')

        router.add('POST', '/v1/prefix',
                   self.add_prefix,
                   tag='infrastructure:admin')

        router.add(['PUT', 'PATCH'], '/v1/prefix/{pid}',
                   self.update_prefix,
                   tag='infrastructure:admin')

        router.add('DELETE', '/v1/prefix/{pid}',
                   self.delete_prefix,
                   tag='infrastructure:admin')


    def list_prefixes(self, req, resp, version):

        prefixes = []

        with db() as conn:
            crsr = conn.execute("SELECT * FROM netrino_ipam" +
                                " WHERE parent_id IS NULL")
            results = crsr.fetchall()

        for pf in results:
            prefixes.append(format_prefix(pf))

        return prefixes
        

    def add_prefix(self, req, resp):
        ipam = netrino_ipam()
        ipam['parent_id'] = req.json.get('parent_id')
        ipam['name'] = req.json.get('name')
        prefix = req.json.get('prefix')
        prefix = IPNetwork(prefix)

        network = prefix.network()
        version = prefix.version()
        length = prefix._bits

        ipam['length'] = length
        ipam['version'] = version
        ipam['ip'] = (ip_to_int(network)).to_bytes(16, byteorder="big")

        ipam.commit()
        #return ipam

    def view_prefix(self, req, resp, pid):
        pass

    def update_prefix(self, req, resp, pid):
        pass

    def delete_prefix(self, req, resp, pid):
        pass
