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
from luxon import g
from luxon import router
from luxon import register

from luxon.helpers.api import raw_list
from psychokinetic import Openstack


@register.resources()
class OpenstackProxy():
    def __init__(self):
        router.add('GET',
                   'v1/openstack/{element}/{endpoint}/{resource}',
                   self.proxy,
                   tag='services')


    def proxy(self, req, resp, element, endpoint, resource):
        # This was copied from another endpoint. If it is going to
        # remain in netrino, this api.execute should be changed to
        # database lookup instead.

        # Todo: perhaps store 'os_token' in session...
        md = req.context.api.execute('GET',
                                     'v1/element/%s/openstack' % element,
                                     endpoint='netrino')
        md = md.json['metadata']

        os = Openstack(md['keystone_url'],md['region'])
        os.identity.authenticate(md['username'], md['password'],
                                 req.context_domain)
        os.identity.scope(project_name=g.tenant_name(req),
                          domain=req.context_domain)
            # req.session['os_token'] = os._scoped_token
            # req.session.save()
        results = getattr(os, endpoint).execute('GET',resource).json

        return raw_list(req, results[resource], context=False)

