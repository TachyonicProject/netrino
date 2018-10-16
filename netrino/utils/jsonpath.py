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
import re

JSP_RE = '[^\[]+(?=\])|[^\.\[\]]+'

def intIfInt(s):
    """Returns Int version of s if possible, else s"""
    try:
        return int(s)
    except ValueError:
        return s

def recurse_set(p, o, val=None):
    """Creates the key/entries of json path list 'p' in obj 'o'.

    Sets value of path 'p' in obj 'o' to 'val' if specified, else None.

    Leaves value unchanged if exists already.

    Args:
        p (list): json path in list format. Strings are dict keys, and int's
                  are list indexes
        o (list or dict): obj in which to create keys/dicts/lists/value
        val: Value to set
    """
    if len(p) == 0:
        return
    elif len(p) == 1:
        init = val
    else:
        if isinstance(p[1], str):
           init = {}
        elif isinstance(p[1], int):
           init = []
    if isinstance(o, dict):
        o.setdefault(p[0], init)
    elif isinstance(o, list):
        for _ in range(len(o), p[0]):
            o.append(None)
        o.append(init)
    recurse_set(p[1:], o[p[0]], val)


def set_if_not_exist(path, obj, val=None):
    """Sets entry in obj as specified by json path 'path' equal to 'val' if
    not yet present.

    Sets value to None if 'val' not specified.
    Creates all entries required to do so.
    Leaves value unchanged if it exists already.

    Eg. when o = {}, then set_if_not_exist('foo[1].bar',o,"baz") will update o
    to become o = {'foo': [None, {'bar': 'baz'}}

    Args:
         path (str): json path
         obj (dict or list): object to manipulate
         val: Value to set
    """
    split_path = re.findall(JSP_RE, path)
    split_path = [i.strip('"') for i in split_path]
    split_path = [i.strip("'") for i in split_path]
    split_path = [intIfInt(i) for i in split_path]
    recurse_set(split_path, obj, val)
