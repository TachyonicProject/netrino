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

from netrino.interfaces.interface import Interface as BaseInterface
from netrino.utils.interface import getScope

from psychokinetic import Openstack
from psychokinetic import Contrail

from luxon.exceptions import FieldMissing
from luxon import g


class Interface(BaseInterface):
    """Contrail Interface/driver.

    Wrapper around psychokinetic.Contrail obj

    .. code:: python

        with Interface('element-uuid') as ct:
            networks = ct.execute(req)

    Element credentials obtained from metadata in database.
    req body must contain "uri", "data", "method" and either "project_name"
    or "project_id". domain is obtained from req.context_domain.
    execute methods are overwritten to return json.

    Args:
        uuid (str): UUID of element
    """

    def __init__(self, uuid):
        super().__init__(uuid, "contrail")

        if not 'keystone_url' in self.metadata:
            raise FieldMissing(field="keystone_url",
                               label="Keystone URL",
                               description="No Keystone URL for element '%s'" %
                                           self.uuid)


        self.os = Openstack(self.metadata['keystone_url'],
                            self.metadata['region'],
                            self.metadata['interface'])
        self.contrail = Contrail(self.os, self.metadata['contrail_url'])

    def __enter__(self):
        self.contrail.authenticate(self.metadata['username'],
                                   self.metadata['password'],
                                   g.current_request.context_domain)
        return self

    def __exit__(self, *args, **kwargs):
        self.os.identity.revoke(self.os._login_token)

    def __getattr__(self, name):
        return getattr(self.contrail, name)

    def execute(self, req, *args, **kwargs):
        # Since we are wrapping around psychokinetic's contrail
        # client, we have to modify the execute method to:
        # * take req as first arg, and
        # * return json instead of the default reponse object.
        method = req.json['method']
        uri = req.json['uri']
        if 'data' in req.json:
            kwargs['data'] = req.json['data']
        self.contrail.scope(
            **getScope(req, infinitystone=['domain'],
                       one_of=['project_id', 'project_name']))
        result = self.contrail.execute(method, uri, *args, **kwargs)
        return result.json
