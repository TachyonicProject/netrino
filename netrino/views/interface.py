# -*- coding: utf-8 -*-
# Copyright (c) 2018 David Kruger.
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
from luxon import db

from luxon.utils.pkg import EntryPoints
from luxon.exceptions import NotFoundError
from luxon.helpers.api import raw_list

from netrino.helpers.elements import elements_with_interface

METHODS = ('GET','POST','PUT','DELETE','PATCH',
           'OPTIONS','HEAD','TRACE','CONNECT')

@register.resources()
class Interface():
    def __init__(self):
        router.add('GET','/v1/interfaces', self.list, tag='services')
        router.add('GET', '/v1/interfaces/{interface}', self.list_elements,
                   tag='services')
        router.add(METHODS,
                   '/v1/interface/{id}/{interface}/{property}',
                   self.interface, tag='services')
        router.add(METHODS,
                   '/v1/interface/{id}/{interface}/{property}/{method}',
                   self.property, tag='services')

    def list(self, req, resp):
        """Lists all the registered netrino_interfaces Entrypoints.
        """
        interfaces = []
        for e in EntryPoints('netrino_interfaces'):
            interfaces.append({'id': e, 'name': e})
        return raw_list(req, interfaces)

    def list_elements(self, req, resp, interface):
        """For a given interface, list all elements that supports this
        interface

        Args:
            interface (str): Netrino Interface in question.

        Returns:
            list of elements id's that supports this interface.
        """
        return elements_with_interface(interface)



    def interface(self, req, resp, id, interface, property):
        """ Interact with element via given interface and method.

        Args:
            interface (str): Netrino Interface to use.
            property (str): Method to run on Interface object.
            id(str): UUID of element.

        Returns:
            Executes the method, and returns the result.
        """
        netrino_interface = EntryPoints('netrino_interfaces')

        try:
            with netrino_interface[interface](id) as obj:
                method = getattr(obj, property)
                return method(req)
        except KeyError:
            raise NotFoundError("Interface '%s' not registered" % interface)

    def property(self, req, resp, id, interface, property, method):
        """ Interact with element via given interface, with property method.

        Args:
            interface (str): Netrino Interface to use.
            property (str): Property on Netrino Interface that returns obj with
                            method
            method (str): Method to run on Interface property object.
            id(str): UUID of element.

        Returns:
            Executes the method, and returns the result.
        """
        netrino_interface = EntryPoints('netrino_interfaces')
        with netrino_interface[interface](id) as obj:
            prop_obj = getattr(obj, property)
            method = getattr(prop_obj, method)
            return method(req)
