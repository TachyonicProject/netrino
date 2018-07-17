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
from luxon import router
from luxon import register

from netrino.workers.snmp import discover_element

from pyipcalc import IPNetwork


@register.resources()
class DiscoverElements():
    def __init__(self):
        router.add('POST', '/v1/snmp/{ip}',
                     self.discover, tag='operations')

        router.add('POST', '/v1/snmp/{ip}/{subnet}',
                     self.discover, tag='operations')
        
    
    def discover(self, req, resp, ip, subnet=None):
        """ Discover devices with SNMP v2.
        
        POST to 'v1/snmp/x.x.x.x' or
                'v1/snmp/x.x.x.x/yy'
        where x.x.x.x is an IP address, and yy the subnet mask.

        Body should contain value for 'community', otherwise the default
        of 'public' is used.

        Args:
            ip (str): IP address to be scanned.
            subnet (str): Subnet mask.
            community: SNMP v2 community string

        """
        if subnet:
            ip = ip + '/' + subnet
        ipnet = IPNetwork(ip)
        if 'community' not in req.json:
            req.json['community'] = 'public'

        task_id = discover_element(ipnet, req.json['community'], g.client)

        return task_id
