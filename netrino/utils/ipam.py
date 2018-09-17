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
from pyipcalc import int_128_to_32, int_to_ip
from pyipcalc import IPNetwork, IPIter

MAX_32_BIT_INT = 4294967295
MAX_64_BIT_INT = 18446744073709551615
MAX_96_BIT_INT = 79228162514264337593543950335

def v6_where_lt(ip):
    """Returns string and tuple that can be used for SQL WHERE ipv6 < ?.

    where_str, where_tuple = v6_where_lt(ip)

    where_str will be "a1<? OR (a1=? AND a2<?) OR (a1=? AND a2=? AND a3<?) OR
                       (a1=? AND a2=? AND a3=? AND a4<?)"
                       or appropriate str based on length of ip
    where_tuple will contain the appropriate values

    Args:
        ip (Long int): Int value of ipv6 address.

    Returns:
        (str,tuple)
    """
    if ip <= MAX_32_BIT_INT:
        return 'a1=0 AND a2=0 AND a3=0 AND a4<?',(ip,)
    a1, a2, a3, a4 = int_128_to_32(ip)
    if ip > MAX_32_BIT_INT and ip <= MAX_64_BIT_INT:
        where_str = '(a1=0 AND a2=0 AND a3<?) OR ' \
                    '(a1=0 AND a2=0 AND a3=? AND a4<?)'
        where_tuple = (a3,a3,a4)
        return where_str, where_tuple
    if ip > MAX_64_BIT_INT and ip <= MAX_96_BIT_INT:
        where_str = '(a1=0 AND a2<?) OR' \
                    '(a1=0 AND a2=? AND a3<?) OR ' \
                    '(a1=0 AND a2=? AND a3=? AND a4<?)'
        where_tuple = (a2,a2,a3,a2,a3,a4)
        return where_str, where_tuple
    # At this point ip > MAX_96_BIT_INT
    where_str = 'a1<? OR' \
                '(a1=? AND a2<?) OR' \
                '(a1=? AND a2=? AND a3<?) OR ' \
                '(a1=? AND a2=? AND a3=? AND a4<?)'
    where_tuple = (a1,a1,a2,a1,a2,a3,a1,a2,a3,a4)
    return where_str, where_tuple

def v6_where_le(ip):
    """Returns string and tuple that can be used for SQL WHERE ipv6 <= ?.

    where_str, where_tuple = v6_where_le(ip)

    where_str will be "a1<=? OR (a1=? AND a2<=?) OR (a1=? AND a2=? AND a3<=?) OR
                       (a1=? AND a2=? AND a3=? AND a4<=?)"
                       or appropriate str based on length of ip
    where_tuple will contain the appropriate values

    Args:
        ip (Long int): Int value of ipv6 address.

    Returns:
        (str,tuple)
    """
    where_str, where_tuple = v6_where_lt(ip)
    return where_str.replace('<','<='), where_tuple


def v6_where_gt(ip):
    """Returns string and tuple that can be used for SQL WHERE ipv6 > ?.

    where_str, where_tuple = v6_where_gt(ip)

    where_str will be "a1>? OR (a1=? AND a2>?) OR (a1=? AND a2=? AND a3>?) OR
                       (a1=? AND a2=? AND a3=? AND a4>?)"
                       or appropriate str based on length of ip
    where_tuple will contain the appropriate values

    Args:
        ip (Long int): Int value of ipv6 address.

    Returns:
        (str,tuple)
    """
    where_str, where_tuple = v6_where_lt(ip)
    return where_str.replace('<', '>'), where_tuple


def v6_where_ge(ip):
    """Returns string and tuple that can be used for SQL WHERE ipv6 <= ?.

    where_str, where_tuple = v6_where_le(ip)

    where_str will be "a1>=? OR (a1=? AND a2>=?) OR (a1=? AND a2=? AND a3>=?) OR
                       (a1=? AND a2=? AND a3=? AND a4>=?)"
                       or appropriate str based on length of ip
    where_tuple will contain the appropriate values

    Args:
        ip (Long int): Int value of ipv6 address.

    Returns:
        (str,tuple)
    """
    where_str, where_tuple = v6_where_lt(ip)
    return where_str.replace('<', '>='), where_tuple

def other_half(ip):
    """For IP x.x.x.x/y returns other x.x.x.x/y of x.x.x.x/y-1

    Args:
        ip (obj): pyipcalc.IPNetwork obj

    Returns:
        IPNetwork object of the other /y in /y-1
    """
    parent = IPNetwork('%s/%s' % (ip.network(),ip._bits-1))
    if parent._network != ip._network:
        return IPNetwork('%s/%s' % (parent.network(), ip._bits))
    add = 1
    if ip.version() == 4:
        add = 2
    net_int = parent._network + ip._size + add
    net = int_to_ip(net_int,ip.version())
    return IPNetwork('%s/%s' % (net, ip._bits,))
