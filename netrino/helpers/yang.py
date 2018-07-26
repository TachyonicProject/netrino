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
import re
from lxml import etree

def module2namespace(location, client):
    """Helper function to extract namespace from YANG module.

    Args:
        location(str): Katalog location of YANG model.
        client(obj): psychokinetic.client.Client obj obtained from req.context.

    Returns:
        Name of namespace as str, if found. Else None.
    """
    namespace_regex = 'namespace +[\'"]([^\'"]*)[\'"]'
    res = client.execute('GET', location, endpoint='katalog')
    for line in res.iter_lines:
        match = re.search(namespace_regex, str(line))
        if match:
            return match.group(1)
    return None

class RFC7951dict():
    """Class to generate obj's to process RFC7951 formatted JSON dicts.

    Args:
        client(obj): psychokinetic.client.Client obj obtained from req.context.

    """
    def __init__(self, client):
        self._client = client

    def to_etree(self, json_dict, element=etree.Element("config")):
        """Adds xml namespace from RFC7951 defined dict to lxml.etree

        Any keys starting with "-" will be added as an attribute to the parent
        element (without the "-").

        Args:
            json_dict(dict): python dict converted from RFC7951 formatted json.
            element(ob): lxml.etree element.

        Returns:
            lxml.etree obj with namespace.
        """
        for k in json_dict:
            if k[0] == '-':
                element.attrib[k[1:]] = json_dict[k]
                continue
            elif ':' in k:
                module, key = k.split(':')
                namespace = module2namespace('yang/%s.yang' % module,
                                             self._client)
                sub_ele = etree.SubElement(element, key,
                                           nsmap={None: namespace})
            else:
                sub_ele = etree.SubElement(element, k)

            if isinstance(json_dict[k], str):
                sub_ele.text = json_dict[k]
            elif isinstance(json_dict[k], (dict, )):
                self.to_etree(json_dict[k], sub_ele)
        return element
