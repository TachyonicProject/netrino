# -*- coding: utf-8 -*-
# Copyright (c) 2018 Dave Kruger.
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
import builtins

from collections import OrderedDict

from luxon import db, g
from luxon.exceptions import FieldMissing, NotFoundError
from luxon.utils.pkg import EntryPoints

from netrino.models.service_templates import netrino_servicetemplate_mappings
from netrino.models.service_templates import netrino_servicetemplate_static
from netrino.models.service_templates import netrino_servicetemplate_pool
from netrino.models.service_templates import netrino_servicetemplate_copy
from netrino.models.service_templates import netrino_user_select
from netrino.models.service_templates import netrino_task_output
from netrino.utils.service_template import find_entry
from netrino.utils.jsonpath import set_or_update

from jsonpath_ng import parse

ALLOCATIONS = OrderedDict(
    {'static_assignments': netrino_servicetemplate_static,
    'pool_allocations': netrino_servicetemplate_pool,
    'mappings': netrino_servicetemplate_mappings,
    'user_select':netrino_user_select,
    'task_output': netrino_task_output,
    'copy_entries': netrino_servicetemplate_copy}
)

def populate_req_json():
    """Populates the Request.json obj with missing data.
    """
    req = g.current_request
    if not 'service_template' in req.json:
        raise FieldMissing("service_template","service_template",
                           "Required Field")
    stid = req.json['service_template']
    sql = 'SELECT id,entry_no FROM netrino_service_template_entry ' \
          'WHERE service_template=? ORDER BY entry_no'
    with db() as conn:
        entries = conn.execute(sql,stid).fetchall()
        entries = {eid['entry_no']:eid['id'] for eid in entries}
    if len(entries) == 0:
        raise NotFoundError("Unable to find Service Template '%s'" % stid)
    for a in ALLOCATIONS:
        globals()[a](entries)

def static_assignments(entries):
    """Updates req.json to have static entries as specified by 'entries'.

    Args:
        entries (dict): Dict containing entry no's and id's to use
                        in the format {entry_no (int): entry_id}
    """
    req = g.current_request
    sql = "SELECT * FROM netrino_servicetemplate_static WHERE " \
          "servicetemplate_entry=?"
    with db() as conn:
        for e in entries:
            static_entries = conn.execute(sql,entries[e]).fetchall()
            entry = find_entry(e, req.json['models'])
            if not entry:
                entry = {'entry_no': e, 'data': {}}
                req.json['models'].append(entry)
            elif entry and 'data' not in entry:
                entry['data'] = {}
            for se in static_entries:
                if se['type'] in ('int',):
                    se['value'] = getattr(builtins,se['type'])(se['value'])
                elif se['type'] == 'bool':
                    se['value'] = se['value'].lower() == 'true'
                elif se['type'] in ('null','None'):
                    se['value'] = None
                set_or_update(se['path'], entry['data'], se['value'])

def pool_allocations(entries):
    pass

def mappings(entries):
    """Updates req.json to have values supplied by mapping funtions.

        Args:
            entries (dict): Dict containing entry no's and id's to use
                            in the format {entry_no (int): entry_id}
    """
    req = g.current_request
    sql_entries = []
    for e in entries:
        sql_entries.append(entries[e])
    sql_where = ['servicetemplate_entry=?'] * len(entries)
    sql_where = ' OR '.join(sql_where)
    sql = "SELECT DISTINCT(mapper) FROM netrino_servicetemplate_mappings " \
          "WHERE %s" % sql_where
    with db() as conn:
        mappers = conn.execute(sql, sql_entries).fetchall()
        mappers = [m['mapper'] for m in mappers]
        for m in mappers:
            map_entries = EntryPoints('netrino_mappers')[m]()
            for me in map_entries:
                entry = find_entry(me, req.json['models'])
                if not entry:
                    entry = {'entry_no': me, 'data': {}}
                    req.json['models'].append(entry)
                elif entry and 'data' not in entry:
                    entry['data'] = {}
                for e in map_entries[me]:
                    set_or_update(e, entry['data'], map_entries[me][e])


def user_select(entries):
    pass

def task_output(entries):
    pass

def copy_entries(entries):
    """Updates req.json to have values equal to another entry's value.

        Args:
            entries (dict): Dict containing entry no's and id's to use
                            in the format {entry_no (int): entry_id}
    """
    req = g.current_request
    sql = "SELECT * FROM netrino_servicetemplate_copy WHERE " \
          "servicetemplate_entry=?"
    with db() as conn:
        for e in entries:
            copy_entries = conn.execute(sql, entries[e]).fetchall()
            entry = find_entry(e, req.json['models'])
            if not entry:
                entry = {'entry_no': e, 'data': {}}
                req.json['models'].append(entry)
            elif entry and 'data' not in entry:
                entry['data'] = {}
            for ce in copy_entries:
                jsonpath_expr = parse(ce['source_path'])
                # In case entry_no was omitted, it means THIS entry.
                if not ce['entry_no']:
                    ce['entry_no'] = e
                source_entry = find_entry(ce['entry_no'], req.json['models'])[
                    'data']
                try:
                    copy_val = jsonpath_expr.find(source_entry)[0].value
                except IndexError:
                    raise NotFoundError("Unable to locate value to copy for "
                                        "%s' in entry '%s' ('%s')."
                                        % (ce['source_path'],ce['entry_no'],
                                           source_entry))
                set_or_update(ce['path'], entry['data'], copy_val)

