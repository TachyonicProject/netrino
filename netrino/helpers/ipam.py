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
from netrino.ext import Radix
from netrino.models.ipam import netrino_prefix, netrino_prefix_tag

from pyipcalc import IPNetwork, IPIter


class IPAM(object):
    def __init__(self):
        self._rtree = Radix()
        self._id_references = {}
        self._id_tags = {}
        self._avail = {}

    def add_prefix(self, name, prefix):
        prefix = IPNetwork(prefix)
        model = netrino_prefix()
        model['name'] = name
        model['prefix'] = prefix.prefix()
        self._rtree.add(prefix.prefix())
        self._id_references[prefix.prefix()] = model['id']
        #if ((prefix.version() == 4 and prefix._bits < 32) or
        #        (prefix.version() == 6 and prefix._bits < 128)):
        #    test = IPIter(prefix.prefix(), prefix._bits + 1)
        #    for a in test:
        #        print(a)
        return model

    def add_tag(self, prefix, tag):
        prefix = IPNetwork(prefix)
        model = netrino_prefix_tag()
        model['prefix'] = self._id_references[prefix.prefix()]
        model['tag'] = tag
        if tag not in self._id_tags:
            self._id_tags[tag] = []
        self._id_tags[tag] += [ prefix.prefix() ]


    def delete_prefix(self, prefix):
        self._rtree.delete(prefix)

    def find(self, length, tag):
        for prefix in self._id_tags[tag]:
            covered = self.find_covered(prefix)
            scan = IPIter(prefix, length)
            for a in scan:
                match = self.find_longer(a.prefix())
                if match.prefix == prefix:
                    if len(self.find_covered(a.prefix())) == 0:
                        self.add_prefix('bleh', a.prefix())
                        return a

    def find_longer(self, ip):
        """Find / Match on Longer.

        Find will return the longest matching prefix
        that contains the search ip (routing-style lookup).
        """
        return self._rtree.search_best(ip)

    def find_exact(self, ip):
        """Find / Match exact Prefix.

        Exact search will only return prefix you have entered.
        """
        return self._rtree.search_exact(ip)
       
    def find_covered(self, ip):
        """Find Covered.

        Covered search will return all prefixes inside the given
        search term, as a list (including the search term itself,
        if present in the tree)
        """
        return self._rtree.search_covered(ip)


ipam = IPAM()
ipam.add_prefix('test', '196.25.1.0/20')
ipam.add_tag('196.25.1.0/20', 'test_tag')
for a in range(2000):
    print(ipam.find(32, 'test_tag'))

#print(ipam.find_covered('0/0'))
