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
from luxon.exceptions import FieldMissing

# (@Vuader) Note: until ncclient has merged Tachyonic's pull request,
# remember to clone ncclient from TachyonicProject.
from ncclient import manager

class Interface(BaseInterface):
    def __init__(self, uuid):
        super().__init__(uuid, "netconf")

    def __getattr__(self, name):
        # Instead of checking all the fields here one by one,
        # we should load model, and verify self.metadata against it.
        # Raise Fieldmissing if so, else continue here
        if not 'ip' in self.metadata:
            raise FieldMissing(
                'No IP to use for Netconf to element "%s"' % self.uuid)

        with manager.connect(host=self.metadata['ip'],
                             port=self.metadata['port'],
                             username=self.metadata['username'],
                             password=self.metadata['password'],
                             timeout=self.metadata['timeout']) as m:
                             # Todo: pass self.metadata['private_key']
            return getattr(m, name)

