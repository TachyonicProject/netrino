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

"""
Mappers are functions used to map json paths to values. It returns a dict.
Each dict key corresponds to the
Service Template entry, eg dict[1] will contain the mappings for entry_no 1
Each value is also a dictionary, with the path as key and its mapped
value as the value.

1. Decorate each function with @self_reference
2. if the Entrypoint name is different than the function name,
    set self.name equal to the entrypoint name, and
3. initialize with self = prepare_mapper(self)

E.g. a typical mapping function looks like this:

@self_reference
def some_mapper(self=None):
    self.name = 'mapper_entry_point_name'
    self = prepare_mapper(self)
    # some statements
    return self.results

"""
import time

from luxon.utils.pkg import EntryPoints
from luxon.exceptions import HTTPNotFound, HTTPError
from luxon import memoize
from luxon import g

from netrino.utils.service_template import self_reference, find_entry
from netrino.helpers.service_template import ALLOCATIONS


@memoize()
def tenant_name_from_context():
    api = g.current_request.context.api
    tenant_id = g.current_request.context_tenant_id
    if not tenant_id:
        return None
    response = api.execute('get', '/v1/tenant/%s' % tenant_id)
    return response.json['name']


@memoize()
def get_service_template():
    api = g.current_request.context.api
    stid = g.current_request.json['service_template']
    return api.execute('GET', 'v1/service-template/' + stid,
                       endpoint="netrino").json


def prepare_mapper(self):
    """Adds attributes to mapper function containing filtered data.

    Adds:
        self.data: a dict that contains complete "mappings" entries,
                   but only for the entries that includes this mapping function
        self.results: An empty dict that can be used to populate results with.
        self.service_template: The Complete Service template in dict format.

    Usage:
        self = prepare_mapper(self)

    Args:
        req (obj): luxon request object
        self (function): a reference to the function itself.
                        (decorate with self_reference to have the 'self'
                        functionality)
    Returns:
        Modified function with these additional attributes:
        self.data is a dict containing a list of dicts.
            Keys are the int entry number, and values are list of dicts
            containing the mapping entries where the mapper equals this mapping
            function.
        self.results is an empty dict that can be used to add results to.
        self.service_template: The entire Service template in dict format.
    """
    self.service_template = _data = get_service_template()
    _entries = _data['models'] if 'models' in _data else []
    self.data = {}
    self.results = {}
    if not hasattr(self, 'name'):
        self.name = self.__name__
    # This loop filters to contain only the relevant mappings for each entry.
    for e in _entries:
        if "mappings" in e:
            entry_no = e['entry_no']
            self.data[entry_no] = []
            for map in e['mappings']:
                if map['mapper'] == self.name:
                    self.data[entry_no].append(map)

    return self


@self_reference
def domain_from_context(self=None):
    self.name = 'infinitystone_domain'
    self = prepare_mapper(self)
    for e in self.data:
        self.results[e] = {}
        for m in self.data[e]:
            self.results[e][m['path']] = g.current_request.context_domain
    return self.results


@self_reference
def tenant_from_context(self=None):
    self.name = 'infinitystone_tenant'
    self = prepare_mapper(self)
    tenant_name = tenant_name_from_context()
    for e in self.data:
        self.results[e] = {}
        for m in self.data[e]:
            self.results[e][m['path']] = tenant_name
    return self.results


@self_reference
def contrail_vn_name_from_context(self=None):
    """Returns 'domain:tenant:mapper_data[0]' for each path.

    mapper_data must be a string containing the value of the VN name.
    """
    self = prepare_mapper(self)
    domain = g.current_request.context_domain
    project = tenant_name_from_context()
    for e in self.data:
        self.results[e] = {}
        for m in self.data[e]:
            name = m['mapper_data'][0]
            self.results[e][m['path']] = '%s:%s:%s' % (domain, project, name)
    return self.results


@self_reference
def contrail_vn_plus_existing(self=None):
    """Returns a list of existing VNs on router plus supplied VN.

    mapper_data must be a dict containing:
        router (str): uuid of physical router on which vn's are extended
        entry (int): Entry number of service template that created the VN
                     that must be added to the list

    Will try 3 times, with 1 sec timeout to fetch the existing VN id.
    """
    self = prepare_mapper(self)
    req = g.current_request
    _domain = req.context_domain
    _project = tenant_name_from_context()
    netrino_interface = EntryPoints('netrino_interfaces')
    srid = req.json['id']
    for e in self.data:
        self.results[e] = {}
        contrail_id = find_entry(e, self.service_template['models'])["element"]
        for me in self.data[e]:
            router = me['mapper_data']['router']
            vn_entry = str(me['mapper_data']['entry'])
            task = None
            vn_id = None
            # trying 3 times to fetch ID of created VN
            for i in range(3):
                task = req.context.api.execute('GET',
                                               '/v1/service-request/' + srid,
                                               endpoint='netrino')
                if not task or task.status_code > 299 or not \
                        vn_entry in task.json['tasks'] or not \
                        'result' in task.json['tasks'][vn_entry]:
                    # didn't find it, trying again
                    time.sleep(1)
                    continue
                # Found it!
                vn_id = task.json['tasks'][vn_entry]['result'][
                    'virtual-network']['uuid']
                break
            if not vn_id:
                raise HTTPNotFound("Unable to determine Virtual Network ID "
                                   "for Service Request '%s' entry '%s'" % (
                                       srid, vn_entry,))
            with netrino_interface['contrail'](contrail_id) as ct:
                ct.contrail.scope(domain=_domain, project_name=_project)
                existing = []
                try:
                    r = ct.contrail.execute('GET',
                                            '/physical-router/' + router)
                    vns = r.json["physical-router"]["virtual_network_refs"]
                    for vn in vns:
                        existing.append({"uuid": vn['uuid']})
                except HTTPError as e:
                    raise Exception(
                        "Unable to Get router '%s' from Contrail: %s" % (
                            router, e))
            self.results[e][me['path']] = existing + [{"uuid": vn_id}]
    return self.results
