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

from luxon import Model


class Element(Model):
    host = Model.String(null=False)
    username = Model.String(null=False)
    password = Model.String(null=True, password=True)
    port = Model.Integer(null=True)
    timeout = Model.Integer(null=True)
    private_key = Model.Text(null=True)


class Interface(BaseInterface):
    """Netconf Interface/driver.

    Acts as ncclient.manager connection obj. Use with with:

    Eg.

    .. code:: python

        with Interface('element-uuid') as m:
            m.lock()

    Element credentials obtained from metadata in database.

    Args:
        uuid (str): UUID of element
        default_operation (str): default Netconf operation. (defaults to merge)
        target (str): Netconf target. (defaults to candidate)
    """
    model = Element

    def __init__(self, uuid, default_operation="merge", target="candidate"):
        super().__init__(uuid, "netconf")
        self.conn = None
        self.default_operation = default_operation
        self.target = target

        self.conn = manager.connect(**self.metadata)
        if not self.conn:
            raise NotFoundError(
                "Unable to connect to element '%s'" % self.uuid)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.conn.close_session()

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def config(self, req):
        """Update element configuration via ncclient's .edit-config()

        Args:
            req (obj): Luxon WSGI request object containing context.api and
                       json body

        Returns:
             str version of ncclient edit_config result.
        """
        rfc7951dict = RFC7951dict(req.context.api)
        config = rfc7951dict.to_etree(req.json)
        self.conn.lock()
        result = self.conn.edit_config(config=config,
                                      default_operation=self.default_operation,
                                      target=self.target)
        self.conn.commit()
        self.conn.unlock()
        return {'result': str(result)}



