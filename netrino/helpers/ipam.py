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
from netrino.utils.ipam import v6_where_le, v6_where_lt
from netrino.utils.ipam import v6_where_ge, other_half
from luxon import db

from luxon.exceptions import NotFoundError, ValidationError
from uuid import uuid4
from luxon.utils.timezone import now

from pyipcalc import IPNetwork, IPIter
from pyipcalc import ip_to_int, int_128_to_32
from pyipcalc import int_to_ip, int_32_to_128

from luxon import GetLogger

log = GetLogger(__name__)


class IPAM(object):
    # Todo: instead of passing conn object around,
    # how about setting attribute?
    def _free(self, ip, rib):
        """Checks if ip is free in rib

        Args:
            ip (obj): IPNetwork obj
            rib (str): Name of RIB

        Returns:
            True if exists and free, or does not exist.
        """
        int_ip = ip_to_int(ip.network())
        split_ip = int_128_to_32(int_ip)
        sql = "SELECT free FROM netrino_prefix WHERE prefix_len=? AND " \
              "version=? AND rib=? AND a4=?"
        vals = [ip._bits, ip.version(), rib, split_ip[3]]
        if ip.version() == 6:
            sql += " AND a1=? AND a2=? AND a3=?"
            vals += [split_ip[0], split_ip[1], split_ip[2]]
        with db() as conn:
            cur = conn.execute(sql, vals)
            result = cur.fetchone()
            if result:
                return result['free']
        return True

    def _closest_free_in_prefix(self, conn, prefix_ids, prefix_len):
        """Finds free prefix

        Does a top-down search. For a given prefix_len, will find the smallest
        free prefix that may contain a prefix of length prefix_len, but falls
        within the range of one of the prefixes with id in list of prefix_ids

        Args:
            conn (obj): db conn obj
            prefix_ids (list): list of id's of prefixes to be searched
            prefix_len (int): Size of prefix that can be contained in the
                              returned prefix.

        Returns:
            DB dict entry of closest free prefix that can contain a prefix
            of length prefix_len
        """
        where = ['parent=?' for pid in prefix_ids]
        where = ' OR '.join(where)
        sql = "SELECT * " \
              "FROM netrino_prefix WHERE free AND prefix_len<? AND (%s) " \
              "ORDER BY prefix_len DESC" % where
        row = conn.execute(sql, [prefix_len] + prefix_ids).fetchone()
        if not row:
            # None of the supernets contained a free block of requested size
            # Grabbing the first available free supernet
            where = ['id=?' for pid in prefix_ids]
            where = ' OR '.join(where)
            sql = "SELECT * FROM netrino_prefix WHERE free AND (%s)" % where
            free = conn.execute(sql, prefix_ids).fetchone()
            if free:
                # Whatever is using this function, will most likely want
                # to use free['parent'], but since this is the supernet, it
                # won't have a parent. So being nice and setting the value
                # of parent to it's own id
                free['parent'] = free['id']
                return free
            return None

        return row

    def _closest_above_prefix(self, conn, supernet, prefix, rib):
        """Finds Closest/Smallest prefix

        Does a bottom up search. For a given prefix, will look for the
        smallest free prefix that contains this prefix, but falls
        in range of the supernet.

        Args:
            conn (obj): db conn obj
            supernet (tuple): 4 32bit integers comprising the supernet
            prefix (obj): IPNetwork obj
            rib (str): Name of RIB

        Returns:
            Tuple containing IPNetwork obj and DB dict entry of the
            found prefix
        """
        sup_int = int_32_to_128(supernet['a1'], supernet['a2'], supernet['a3'],
                                supernet['a4'])
        sup_ip = int_to_ip(sup_int, supernet['version'])
        sup_net = IPNetwork('%s/%s' % (sup_ip, supernet['prefix_len']))
        gwhere, gvals = v6_where_ge(sup_int)
        lwhere, lvals = v6_where_lt(sup_int + sup_net._size)
        sql = "SELECT * FROM netrino_prefix WHERE (%s) AND (%s) AND free " \
              "AND prefix_len <? AND rib=? ORDER BY prefix_len DESC" % (
                  gwhere, lwhere,)
        rows = conn.execute(sql,
                            gvals + lvals + (prefix._bits, rib,)).fetchall()
        for r in rows:
            ip = int_32_to_128(r['a1'], r['a2'], r['a3'], r['a4'])
            ip = int_to_ip(ip, r['version'])
            ip = IPNetwork('%s/%s' % (ip, r['prefix_len'],))
            if prefix in ip:
                # Whatever is using this function, will most likely want
                # to use ip['parent']. But if this is the supernet, it
                # won't have a parent. So being nice and setting the value
                # of parent to it's own id
                if not r['parent']:
                    r['parent'] = r['id']
                return ip, r
        return None, None

    def _get_supernet(self, conn, ip, rib, length, version=4):
        """Finds Supernet containing ip in RIB

        Args:
            conn (obj): Database connection object
            ip (int): Integer version of IP
            rib (str): RIB name
            length (int): prefix length of IP
            version (int): IP version 4 or 6

        Returns:
            Tuple containing IPNetwork obj and DB dict entry of the
            found supernet.
        """
        sql = "SELECT * FROM netrino_prefix " \
              "WHERE version=4 AND a4<=? AND type != 'hidden' " \
              "AND rib=? AND prefix_len<? ORDER BY prefix_len"
        vals = (ip, rib, length)
        if version == 6:
            where, vals = v6_where_le(ip)
            sql = "SELECT * FROM netrino_prefix " \
                  "WHERE (%s) AND version==6 AND type != 'hidden' AND " \
                  "rib=? AND prefix_len<? ORDER BY prefix_len" % where
            vals += (rib, length,)
        ip = IPNetwork('%s/%s' % (int_to_ip(ip, version), length,))
        candidates = conn.execute(sql, vals).fetchall()
        for row in candidates:
            cip = int_32_to_128(row['a1'], row['a2'], row['a3'], row['a4'])
            cip = int_to_ip(cip, version)
            candidate = IPNetwork('%s/%s' % (cip, row['prefix_len']))
            if ip in candidate:
                return candidate, row
        return None, None

    def _update_children(self, conn, old_parent, new_parent,
                         prefix, rib='default'):
        """Updates children with new parent ID.

        Args:
            conn (obj): Database connection object
            old_parent (str): UUID of old parent.
            new_parent (str): UUID of new parent.
            prefix (obj): IPNetwork obj of the new parent
            rib (str): Name of RIB
        """
        lower = ip_to_int(prefix.network())
        upper = ip_to_int(prefix.last())
        lwhere, lvals = v6_where_le(upper)
        gwhere, gvals = v6_where_ge(lower)
        sql = 'UPDATE netrino_prefix SET parent=? WHERE parent=? ' \
              'AND prefix_len>? AND rib=? AND (%s) AND (%s)' % (lwhere, gwhere)
        vals = (prefix._bits, rib) + lvals + gvals
        if old_parent is None:
            sql = sql.replace('WHERE parent=?', 'WHERE parent IS NULL')
        else:
            vals = (old_parent,) + vals
        conn.execute(sql, (new_parent,) + vals)

    def _populate_prefix_len(self, conn, prefix, length, parent, ver, rib,
                             name, pref_type, specific=None):
        """Populates the IPAM with prefixes until the given prefix_len is
        reached.

        Also allocates that prefix.

        Used eg by find() and allocate_prefix() when the requested prefix
        or prefix_len does not yet exist.

        If specific is not specified, the first available prefix found will
        be returned.

        Args:
            conn (obj): Database connection object
            prefix (obj): IPNetwork obj of the new parent
            prefix_len (int): Desired length of prefix to be created.
            parent(str): UUID of parent the created prefixes must belong to.
            ver (int): IP version 4 or 6
            rib (str): Name of RIB
            name (str): Name of the prefix.
            pref_type (str): User settable type of the prefix that will be
                            allocated. Auto created prefixes will have
                            type 'hidden'
            specific (obj): IPNetwork object in the case where a specific
                            prefix must be allocated.
        Returns:
            IPNetwork() obj of allocated IP.
        """
        # Not using model here, rather using db conn object,
        # so that we only do one commit after all has been added
        sql = 'INSERT INTO netrino_prefix VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)'
        prefix_len = prefix._bits
        children = IPIter(prefix.prefix(), prefix_len + 1)
        for child in children:
            uid = str(uuid4())
            a1, a2, a3, a4 = int_128_to_32(ip_to_int(child.network()))
            conn.execute(sql, (uid,
                               a1, a2, a3, a4,
                               "Available",
                               parent,
                               ver,
                               False,
                               rib,
                               prefix_len + 1,
                               'hidden',
                               now()))
            # One of the children needs to remain free. (The one that does
            # not contain the prefix that will be allocated.
            if specific:
                if specific in child:
                    ipnet = child
                    last_id = uid
                else:
                    # When providing a specific prefix to be allocated,
                    # and this child does not contain that prefix, we need
                    # to set free=True
                    conn.execute('UPDATE netrino_prefix SET free=? WHERE id=?',
                                 (True, uid))
            else:
                if child.network() == prefix.network():
                    last_id = uid

        if not specific:
            # when we don't specify a specific prefix to be allocated
            ipnet = IPNetwork(prefix.network() + '/' + str(prefix_len + 1))
            # The last/higher child will remain free
            conn.execute('UPDATE netrino_prefix SET free=? WHERE id=?',
                         (True, uid))

        # Found one!
        if prefix_len + 1 == length:
            conn.execute('UPDATE netrino_prefix SET type=?,name=? WHERE id=?',
                         (pref_type, name, last_id))
            if specific:
                return specific
            return IPNetwork('%s/%s' % (prefix.network(), length))

        return self._populate_prefix_len(conn, ipnet, length, parent,
                                         ver, rib, name, pref_type, specific)

    def _populate_exist(self, conn, prefix, version, parent, rib):
        """Populates the IPAM with prefixes until a more specific existing is
        found.

        Used typically when a prefix is added that covers another, already
        present prefix.

        Args:
            conn (obj): Database connection object
            prefix (obj): IPNetwork obj of the new parent
            version (int): IP version 4 or 6
            parent(str): UUID of parent the created prefixes must belong to.
            rib (str): Name of RIB
        """
        sql = 'INSERT INTO netrino_prefix VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)'
        prefix_len = prefix._bits
        children = IPIter(prefix.prefix(), prefix_len + 1)
        descendants = self._top_descendants(conn, prefix, rib)
        if len(descendants) == 0:
            # No need to create children if there are no descendants
            return
        for child in children:
            exist = self._get_prefix(conn, child, rib)
            if not exist:
                uid = str(uuid4())
                a1, a2, a3, a4 = int_128_to_32(ip_to_int(child.network()))
                conn.execute(sql, (uid,
                                   a1, a2, a3, a4,
                                   "Available",
                                   parent,
                                   version,
                                   True,
                                   rib,
                                   prefix_len + 1,
                                   'hidden',
                                   now()))
                if self._descendant_in_prefix(child, descendants):
                    self._populate_exist(conn, child, version, parent, rib)

    def _reserve(self, conn, prefix, prefix_id, length, parent, version, rib,
                 name, pref_type, specific=None):
        """Reserves a prefix so that it can be allocated.

        Called when free block of requested size does not yet exist. Will
        set free=false for prefix_id, and call _populate() to create all
        necessary blocks.

        Args:
            conn (obj): db conn obj.
            prefix (obj): IPNetwork() prefix to allocate out of
            prefix_id (str): UUID of this specific free prefix
            length (int): Prefix length to be allocated.
            parent (str): UUID of free parent prefix to allocate from.
            version (int): IP version 4 or 6
            rib (str): Name of rib
            name (str): Name of the prefix.
            pref_type (str): The type to set on the eventually allocated prefix
            specific (obj): specific IPNetwork() to allocate.

        Returns:
            IPNetwork() obj of allocated IP.
        """
        sql_reserve = 'UPDATE netrino_prefix SET free=? WHERE id=?'
        conn.execute(sql_reserve, (False, prefix_id,))
        result = self._populate_prefix_len(conn, prefix, length, parent,
                                           version, rib, name, pref_type,
                                           specific)

        return result

    def allocate_prefix(self, name, prefix, prefix_type='container',
                        rib='default'):
        """Allocates a prefix.

        Sets free=false and name + type. If it does not exist yet, will be
        created and ipam populated.

        Args:
            name (str): Name of the prefix.
            prefix (str): IP Prefix to allocate.
            prefix_type (str): Custom type of prefix.
            rib (str): Name of RIB from which to allocate.

        Returns:
            netrino_prefix() model version of allocated prefix.
        """
        # First verifying that it is free
        ip = IPNetwork(prefix)
        if not self._free(ip, rib):
            raise ValidationError(message="Unable to allocate '%s', not free"
                                          % prefix)
        allocated = self.add_prefix(name, prefix, prefix_type, rib)
        allocated['free'] = False
        allocated.commit()
        return allocated

    def add_prefix(self, name, prefix, prefix_type='container', rib='default'):
        """Used to add a prefix to the IPAM.

        This prefix can then be used as a pool to allocate from.
        Adding a prefix sets its status as Free. (free=true)

        Checks to see if the prefix fits inside a bigger, existing prefix
        in the same RIB, and if so, will populate the IPAM with the remaining
        prefixes. This means all ancestors of the added prefix will no longer
        be free.

        Args:
            name (str): Name of the prefix.
            prefix (str): IP Prefix to allocate.
            prefix_type (str): Custom type of prefix.
            rib (str): Name of RIB from which to allocate.

        Returns:
            netrino_prefix() model version of allocated prefix.
        """
        prefix = IPNetwork(prefix)
        ip = ip_to_int(prefix.network())
        split_ip = int_128_to_32(ip)
        version = prefix.version()
        with db() as conn:
            supernet, srow = self._get_supernet(conn, ip, rib, prefix._bits,
                                                version)
            model = netrino_prefix()
            # This is the supernet
            if not supernet:
                sql = 'INSERT INTO netrino_prefix VALUES ' \
                      '(?,?,?,?,?,?,?,?,?,?,?,?,?)'
                uid = str(uuid4())
                vals = [uid]
                vals += list(split_ip)
                vals += ["Available", None, version, True, rib]
                vals += [prefix._bits, prefix_type, now()]
                conn.execute(sql, vals)
                self._populate_exist(conn, prefix, version, uid, rib)
                self._update_children(conn, None, uid, prefix,
                                      rib)
                conn.commit()
                model.sql_id(uid)
                return model
            # This is not a supernet
            # Checking if it exists already
            sql = "SELECT id,parent FROM netrino_prefix WHERE rib=? " \
                  "AND prefix_len=? AND version=? AND a4=?"
            vals = [rib, prefix._bits, version, split_ip[3]]
            if version == 6:
                sql += " AND a1=? AND a2=? AND a3=?"
                vals += [split_ip[0], split_ip[1], split_ip[2]]
            exist = conn.execute(sql, vals).fetchone()
            # It exists
            if exist:
                conn.execute('UPDATE netrino_prefix SET type=? WHERE id=?',
                             (prefix_type, exist['id'],))
                self._update_children(conn, exist['parent'], exist['id'],
                                      prefix, rib)
                conn.commit()
                model.sql_id(exist['id'])
                return model
            # It does not yet exist
            # Must reserve and create.
            parent, prow = self._closest_above_prefix(conn, srow, prefix, rib)
            self._reserve(conn, parent, prow['id'], prefix._bits,
                          prow['parent'], version, rib, name, prefix_type,
                          prefix)
            # _reserve creates two prefixes of the requested length.
            # One has free=false, other has free=true. Since we are adding
            # a prefix, it has to remain free.
            sql = "UPDATE netrino_prefix SET free=?,type=? " \
                  "WHERE rib=? AND prefix_len=? AND version=? AND a4=?"
            if version == 6:
                sql += " AND a1=? AND a2=? AND a3=?"
            conn.execute(sql, [True, prefix_type] + vals)
            sql = "SELECT id FROM netrino_prefix WHERE " \
                  "rib=? AND prefix_len=? AND version=? " \
                  "AND a4=?"
            if version == 6:
                sql += " AND a1=? AND a2=? AND a3=?"
            uid = conn.execute(sql, vals).fetchone()
            uid = uid['id']
            conn.commit()
            model.sql_id(uid)
            return model

        return None

    def add_tag(self, prefix_id, tag):
        """Adds tag to prefix

        Args:
            prefix_id (str): UUID of prefix
            tag (str): Tag name
        """
        model = netrino_prefix_tag()
        model['prefix'] = prefix_id
        model['tag'] = tag
        model.commit()

    def id_tags(self, tag):
        """Returns list of prefix ids matching tag

        Args:
            tag (str): Name of tag

        Returns:
            List of id's of prefixes associated with tag.
        """
        sql = "SELECT netrino_prefix.id " \
              "FROM netrino_prefix,netrino_prefix_tag " \
              "WHERE tag=? " \
              "AND netrino_prefix.id = netrino_prefix_tag.prefix"
        with db() as conn:
            cur = conn.execute(sql, (tag,))
            results = cur.fetchall()
        return [r['id'] for r in results]

    def delete_prefix(self, prefix, rib='default'):
        """Delete's a prefix

        Opposite of add_prefix.
        Also deletes assignments.
        Reverts type back to hidden.
        Prunes IPAM as required.

        Args:
            prefix (str): IP Prefix to be deleted
            rib (str): Name of RIB.
        """
        prefix = IPNetwork(prefix)
        ip = ip_to_int(prefix.network())
        split_ip = int_128_to_32(ip)
        version = prefix.version()
        # Checking if it actually exists
        sql = "SELECT * FROM netrino_prefix WHERE rib=? " \
              "AND prefix_len=? AND version=? AND a4=?"
        vals = [rib, prefix._bits, version, split_ip[3]]
        if version == 6:
            sql += " AND a1=? AND a2=? AND a3=?"
            vals += [split_ip[0], split_ip[1], split_ip[2]]
        with db() as conn:
            exist = conn.execute(sql, vals).fetchone()
            # It doesn't exist:
            if not exist:
                log.info("Received request to delete prefix '%s' in rib '%s', "
                         "but it was not found" % (prefix, rib,))
                return

            sql_update = "UPDATE netrino_prefix SET type='hidden' " \
                         "WHERE id=?"
            conn.execute(sql_update, exist['id'])
            # It's descendants will be getting a new parent
            update_kids = "UPDATE netrino_prefix SET parent=? WHERE " \
                          "parent=?"
            cur = conn.execute(update_kids, (exist['parent'], exist['id'],))
            # Cleanup time
            # If it has no chidren, it can be freed
            if cur.rowcount == 0:
                # If this is the supernet, we can completely remove
                if not exist['parent']:
                    conn.execute('DELETE FROM netrino_prefix WHERE id=?',
                                 exist['id'])
                    conn.commit()
                    return True
                # Else we set it free
                conn.execute('UPDATE netrino_prefix SET free=? WHERE id=?',
                             (True, exist['id'],))
            # Either it was already free, or it is now:
            if exist['free'] or cur.rowcount == 0:
                # Checking if this prefix's other half is also free
                oh = other_half(prefix)
                int_oh = ip_to_int(oh.network())
                split_oh = int_128_to_32(int_oh)
                vals = [rib, prefix._bits, version, split_oh[3]]
                if version == 6:
                    vals += [split_oh[0], split_oh[1], split_oh[2]]
                clean = conn.execute(sql, vals).fetchone()
                # It is free, so both can be deleted, and direct ancestor
                # can be freed up:
                if clean and clean['free'] and clean['type'] == "hidden":
                    anc_ip = ip if ip < int_oh else int_oh
                    anc_net = int_to_ip(anc_ip, version)
                    anc_net = IPNetwork(
                        '%s/%s' % (anc_net, prefix._bits - 1))
                    self.prune(conn, exist['id'], clean['id'], anc_net,
                               rib, version)

            conn.commit()
            return True

    def has_descendants(self, prefix, rib):
        """Checks wether prefix has any prefixes or allocations underneath

        Args:
            prefix (str): string version of IP
            rib (str): RIB to search in

        Returns:
            True if prefix has any descendants.
        """
        ip = IPNetwork(prefix)
        version = ip.version()
        net = ip_to_int(ip.network())
        last = net + ip._size
        gwhere, gvals = v6_where_ge(net)
        lwhere, lvals = v6_where_le(last)
        sql = "SELECT id FROM netrino_prefix WHERE rib=? " \
              "AND prefix_len>? AND version=? AND (%s) AND (%s) " \
              "LIMIT 1" % (gwhere, lwhere,)
        vals = (rib, ip._bits, version) + gvals + lvals
        with db() as conn:
            has = conn.execute(sql, vals).fetchone()
        if has:
            return True
        return False

    def _top_descendants(self, conn, prefix, rib):
        """List of parentless descendants for prefix in rib

        Args:
            conn (onj): DB conn obj.
            prefix (str): string version of IP
            rib (str): RIB to search in

        Returns:
            List of DB entries of parentless descendants.
        """
        version = prefix.version()
        net = ip_to_int(prefix.network())
        last = net + prefix._size
        gwhere, gvals = v6_where_ge(net)
        lwhere, lvals = v6_where_le(last)
        sql = "SELECT * FROM netrino_prefix WHERE rib=? " \
              "AND prefix_len>? AND version=? AND parent IS NULL AND " \
              "(%s) AND (%s) ORDER BY prefix_len" % (gwhere, lwhere,)
        vals = (rib, prefix._bits, version) + gvals + lvals
        rows = conn.execute(sql, vals).fetchall()
        result = []
        for r in rows:
            ip = int_32_to_128(r['a1'], r['a2'], r['a3'], r['a4'])
            ip = int_to_ip(ip, r['version'])
            result.append(IPNetwork('%s/%s' % (ip, r['prefix_len'],)))
        return result

    def _descendant_in_prefix(self, prefix, descendants):
        """Returns True if one of the descendants fall within prefix

        Args:
            prefix (obj): IPNetwork obj of prefix to check.
            descendants (list): List of IPNetwork() descendants to check
        """
        for d in descendants:
            log.critical("%s in %s?" % (d, prefix))
            if d in prefix:
                log.critical("yes")
                return True

    def prune(self, conn, pid1, pid2, ancestor, rib, version):
        """Prunes the IPAM

        Deletes both prefixes with id's pid1 and pid2
        Sets their ancestor as Free
        checks if all of the following are true:
        * Ancestor is hidden,
        * Ancestor's other half is hidden
        * Ancestor's other half is free
        And if so, repeats the process with the two ancestor ID's
        by calling itself

        Args:
            conn (obj): DB conn obj.
            pid1 (str): UUID of one of the pair of prefixes to be pruned.
            pid2 (str): UUID of other of the pair of prefixes to be pruned.
            ancestor (obj): IPNetwork obj of direct ancestor of the above two.
            rib (str): Name of RIB
            version (int): IP version 4 or 6.
        """
        # First deleting both
        conn.execute('DELETE FROM netrino_prefix WHERE id=? OR id=?',
                     (pid1, pid2,))
        # Grabbing ID of ancestor
        ip = ip_to_int(ancestor.network())
        split_ip = int_128_to_32(ip)
        sql = "SELECT * FROM netrino_prefix WHERE rib=? AND version=? " \
              "AND prefix_len=? AND a4=?"
        vals = [rib, version, ancestor._bits, split_ip[3]]
        if version == 6:
            sql += " AND a1=? AND a2=? AND a3=?"
            vals += [split_ip[0], split_ip[1], split_ip[2]]
        anc = conn.execute(sql, vals).fetchone()
        # Setting Ancestor as free
        sql_update = "UPDATE netrino_prefix SET free=? WHERE id=?"
        conn.execute(sql_update, (True, anc['id'],))
        # Checking if it was hidden
        if anc['type'] == 'hidden':
            # Checking if other half is free and hidden
            oh = other_half(ancestor)
            int_oh = ip_to_int(oh.network())
            split_oh = int_128_to_32(int_oh)
            vals = [rib, version, ancestor._bits, split_oh[3]]
            if version == 6:
                vals += [split_oh[0], split_oh[1], split_oh[2]]
            cleanup = conn.execute(sql, vals).fetchone()
            # It is free, so both can be deleted, and direct ancestor can
            # be freed up
            if cleanup['free'] and cleanup['type'] == "hidden":
                anc_ip = ip if ip < int_oh else int_oh
                anc_net = int_to_ip(anc_ip, version)
                anc_net = IPNetwork('%s/%s' % (anc_net, ancestor._bits - 1))
                self.prune(conn, anc['id'], cleanup['id'], anc_net, rib,
                           version)

    def find(self, length, tag, name, pref_type="Assigned"):
        """Find free prefix of given length out of prefix ranges with
        given tag.

        Searches for next available, and if found, allocates that prefix
        by setting name, type and free=False.

        If not initially found, prefix of requested size is created
        (if possible).

        Args:
            length (int): size of prefix to allocate.
            tag (str): Tag name of parent to allocate from.
            name (str): Name to apply to allocated prefix.
            pref_type (str): Custom type of the prefix to allocate.

        Returns:
            String version of allocated prefix.
        """
        prefix_ids = self.id_tags(tag)
        with db() as conn:
            p = self._closest_free_in_prefix(conn, prefix_ids, length)
            if p:
                sql = "SELECT id,a1,a2,a3,a4,version FROM netrino_prefix " \
                      "WHERE free AND prefix_len=? AND parent=?"
                parent = int_32_to_128(p['a1'], p['a2'], p['a3'], p['a4'])
                parent_ip = int_to_ip(parent, p['version'])
                parent_net = IPNetwork('%s/%s' % (parent_ip, p['prefix_len'],))
                cur = conn.execute(sql, (length, p['parent']))
                c = cur.fetchone()
                if c is not None:
                    sql_reserve = "UPDATE netrino_prefix SET free=?,name=?," \
                                  "type=? WHERE id=?"
                    conn.execute(sql_reserve, (False,name,pref_type,c['id']))
                    conn.commit()
                    int_ip = int_32_to_128(c['a1'], c['a2'], c['a3'], c['a4'])
                    return int_to_ip(int_ip, c['version']) + '/' + str(length)
                    # Boo - we did not find a free block of requested size.
                    # Lets create one and return that.
                reserved = self._reserve(conn, parent_net, p['id'], length,
                                         p['parent'], p['version'], p['rib'],
                                         name, pref_type)
                if reserved:
                    conn.commit()
                    return reserved.prefix()

        raise NotFoundError("Unable to allocate address from pool '%s'" % tag)

    def _get_prefix(self, conn, ip, rib):
        """Returns prefix row

        Args:
            conn (obj): DB conn obj.
            ip (obj): IPNetwork obj of the prefix to retreive.
            rib (str): Name of RIB

        Returns:
            DB row of found prefix.
        """
        int_ip = ip_to_int(ip.network())
        split_ip = int_128_to_32(int_ip)
        sql = "SELECT id FROM netrino_prefix WHERE prefix_len=? AND " \
              "version=? AND rib=? AND a4=?"
        vals = [ip._bits, ip.version(), rib, split_ip[3]]
        if ip.version() == 6:
            sql += " AND a1=? AND a2=? AND a3=?"
            vals += [split_ip[0], split_ip[1], split_ip[2]]
        cur = conn.execute(sql, vals)
        return cur.fetchone()

    def get_prefix(self, ip, rib):
        """Returns prefix model

        Returns None if not found.

        Args:
            ip (obj): IPNetwork obj of the prefix to retreive.
            rib (str): Name of RIB

        Returns:
            DB row of found prefix.
        """
        with db() as conn:
            result = self._get_prefix(conn, ip, rib)
            if result:
                prefix = netrino_prefix()
                prefix.sql_id(result['id'])
                return prefix

    def release_prefix(self, prefix, rib="default"):
        """The opposite of allocate_prefix.

        So in essecence will set free=True, but will also set type to
        "hidden". And Prune if required.

        Args:
            prefix (str): IP prefix to be released
            rib (str): RIB to release from
        """
        # First verifying that it exists
        ip = self.get_prefix(IPNetwork(prefix), rib)
        err_msg = "Received request to release prefix '%s' in rib '%s', " % (
            prefix, rib,)
        if not ip or ip['free']:
            log.info(err_msg + "but no such allocation was not found")
            return

        # If this is really an assignment, it won't have any children
        if self.has_descendants(prefix, rib):
            raise ValidationError(err_msg + "but it has sub-assigments")

        # It is in use (free=false) so valid candidate for deletion
        if ip['type'] != "hidden":
            # This is really an allocation.
            ip['free'] = True
            # Can use delete_prefix() to remove/prune, but it will only delete
            # "hidden", so we need to set it that way first
            ip['type'] = 'hidden'
            ip.commit()
            return self.delete_prefix(prefix, rib)
