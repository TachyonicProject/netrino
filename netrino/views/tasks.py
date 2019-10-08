# -*- coding: utf-8 -*-
# Copyright (c) 2019 Dave Kruger.
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
from luxon import register
from luxon import router
from luxon import db

from luxon.helpers.api import sql_list, raw_list, obj
from luxon.exceptions import HTTPError
from luxon.utils import sql
from luxon.utils.uri import decode

from netrino.models.tasks import netrino_task

OPERATORS_RE = '=|>=|<=|<|>|\*='


def gen_where(field, operator, value):
    if operator == '=':
        return sql.Field(field) == sql.Value(value)
    if operator == '>=':
        return sql.Field(field) >= sql.Value(value)
    if operator == '<=':
        return sql.Field(field) <= sql.Value(value)
    if operator == '<':
        return sql.Field(field) < sql.Value(value)
    if operator == '>':
        return sql.Field(field) > sql.Value(value)
    if operator == '*=':
        return sql.Field(field) ^ sql.Value(value)

    raise HTTPError(title="Unsupported Operator",
                    description='"%s" operator not supported in '
                                'query string' % operator)


def params_to_sql(select, query_string):
    is_encoded = '+' in query_string or '%' in query_string
    if is_encoded:
        query_string = decode(query_string)

    for i in query_string.split('&'):
        if ';' in i:
            conds = []
            for orred in i.split(';'):
                operator = re.search(OPERATORS_RE, orred).group(0)
                field, value = orred.split(operator)
                conds.append(gen_where(field, operator, value))

            select.where = sql.Group(sql.Or(*conds))
            continue

        operator = re.search(OPERATORS_RE, i).group(0)
        field, value = i.split(operator)

        if ',' in value:
            conds = []
            for val in value.split(','):
                conds.append(gen_where(field, operator, val))
            select.where = sql.Group(sql.Or(*conds))
        else:
            select.where = gen_where(field, operator, value)

    return select


@register.resources()
class Tasks:
    def __init__(self):
        router.add('GET', '/v1/tasks', self.list,
                   tag='internal')
        router.add('GET', '/v1/task/{task_id}', self.view,
                   tag='internal')
        router.add('POST', '/v1/task', self.create,
                   tag='internal')
        router.add(['PUT', 'PATCH'], '/v1/task/{task_id}', self.update,
                   tag='internal')
        router.add('DELETE', '/v1/task', self.delete,
                   tag='internal')

    def list(self, req, resp):
        qs = req.query_string
        select = sql.Select('netrino_task')

        if not qs:
            return sql_list(req, select)

        select = params_to_sql(select, qs)

        with db() as conn:
            results = conn.execute(select.query, select.values).fetchall()

        return raw_list(req, results)

    def create(self, req, resp):
        task = obj(req, netrino_task)
        task.commit()

        return task

    def update(self, req, resp, task_id):
        task = obj(req, netrino_task, sql_id=task_id)
        task.commit()

        return task

    def view(self, req, resp, task_id):
        return obj(req, netrino_task, sql_id=task_id)

    def delete(self, req, resp, task_id):
        task = obj(req, netrino_task, sql_id=task_id)
        task.delete()
        task.commit()
