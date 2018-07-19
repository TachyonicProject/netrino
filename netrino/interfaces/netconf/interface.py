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
import atexit

from netrino.interfaces.interface import Interface as BaseInterface
from luxon.exceptions import FieldMissing

# (@Vuader) Note: until ncclient has merged Tachyonic's pull request,
# remember to clone ncclient from TachyonicProject.
from ncclient import manager

from luxon import GetLogger

log = GetLogger(__name__)

class Interface(BaseInterface):
    """Netconf Interface/driver.

    Acts as ncclient.manager connection obj. Call it or use with with:

    Eg.

    .. code:: python

        manager = Interface('element-uuid')
        m = manager()
        m.lock()


    or

    .. code:: python

        manager = Interface('element-uuid')
        with manager() as m:
            m.lock()

    Args:
        uuid(str): UUID of element

    Element credentials obtained from metadata in database.

    """
    def __init__(self, uuid):
        super().__init__(uuid, "netconf")
        self.conn = None

    def __call__(self):
        self.conn = manager.connect(**self.metadata)
        # (@Vuader) If this object is called multiple times,
        # the exit function is registered multiple times atexit
        # So if it is called twice eg, the close() method is run twice.
        # Does not seem ideal.
        atexit.register(self.close)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.conn.close_session()

    def __getattr__(self, name):
        return getattr(self.conn, name)

    def close(self):
        """Close ncclient manager connection if it is still open.

         Used with atexit.
        """
        try:
            self.conn.close_session()
        except:
            pass

    #def edit_config(self, *args, **kwargs):


