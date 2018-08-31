from luxon.core.app import App
from luxon import db
from luxon.exceptions import NotFoundError, ValidationError

from netrino.helpers.ipam import IPAM
from netrino.models.ipam import netrino_prefix
from netrino.models.ipam import netrino_prefix_tag

from pyipcalc import IPNetwork, ip_to_int, int_128_to_32

import pytest

app = App(name="Test", ini='/dev/null')
app.config['database'] = {}
app.config['database']['type'] = 'sqlite3'

netrino_prefix().create_table()
netrino_prefix_tag().create_table()

with db() as conn:
    conn.execute('DELETE from netrino_prefix')
    conn.execute('DELETE FROM netrino_prefix_tag')

ipam = IPAM()

def test_add_supernet():
    global sup
    sup = ipam.add_prefix('supernet', '196.25.0.0/20')
    ipam.add_tag(sup['id'], 'test_tag')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE id=?"
        result = conn.execute(sql,sup['id']).fetchall()
    assert len(result)==1
    result[0].pop('creation_time')
    model = netrino_prefix()
    model.sql_id(result[0].pop('id'))
    model.update(result[0])
    assert sup['id'] in ipam.id_tags('test_tag')

def test_find_initial():
    prefix_len = 24
    result = ipam.find(prefix_len,'test_tag')
    assert result == '196.25.0.0/24'
    prefix = IPNetwork(result)
    ip = ip_to_int('196.25.0.0')
    ip = int_128_to_32(ip)
    with db() as conn:
        sql = "SELECT id FROM netrino_prefix " \
              "WHERE a1=? AND a2=? AND a3=? AND a4=? AND prefix_len=?"
        result = conn.execute(sql,ip+(prefix_len,)).fetchall()
    assert len(result)==1

def test_find_second():
    prefix_len = 24
    result = ipam.find(prefix_len,'test_tag')
    assert result == '196.25.1.0/24'
    prefix = IPNetwork(result)
    ip = ip_to_int('196.25.1.0')
    ip = int_128_to_32(ip)
    with db() as conn:
        sql = "SELECT id FROM netrino_prefix " \
              "WHERE a1=? AND a2=? AND a3=? AND a4=? AND prefix_len=?"
        result = conn.execute(sql,ip+(prefix_len,)).fetchall()
    assert len(result)==1

def test_add_child_with_no_allocated_children():
    global sup
    global empty_child
    empty_child = ipam.add_prefix('child', '196.25.2.0/24')
    ipam.add_tag(empty_child['id'], 'child_with_no_children')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE id=?"
        result = conn.execute(sql,empty_child['id']).fetchall()
    assert len(result)==1
    result[0].pop('creation_time')
    model = netrino_prefix()
    model.sql_id(result[0].pop('id'))
    model.update(result[0])
    assert model['parent'] == sup['id']

def test_add_child_with_allocated_children():
    global sup
    child = ipam.add_prefix('prefix_with_children', '196.25.0.0/23')
    ipam.add_tag(child['id'], 'child_prefix_with_children')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE id=?"
        result = conn.execute(sql, child['id']).fetchall()
        new_parent = conn.execute("SELECT parent FROM netrino_prefix WHERE "
                                  "a4=3289972736 AND prefix_len=24").fetchone()
        new_parent = new_parent['parent']
        new_parent2 = conn.execute("SELECT parent FROM netrino_prefix WHERE "
                                  "a4=3289973248 AND prefix_len=24").fetchone()
        new_parent2 = new_parent2['parent']
    assert len(result) == 1
    result[0].pop('creation_time')
    model = netrino_prefix()
    model.sql_id(result[0].pop('id'))
    model.update(result[0])
    assert model['parent'] == sup['id']
    assert new_parent == child['id']
    assert new_parent2 != child['id']

def test_add_prefix_above_supernet():
    very_top = ipam.add_prefix('superdupernet', '196.25.0.0/19')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE id=?"
        existed = conn.execute(sql, sup['id']).fetchone()
    assert existed['parent'] == very_top['id']
    assert existed['id'] == empty_child['parent']


def test_allocate_from_empty_child_prefix():
    global pl30
    prefix_len = 30
    alloc_30 = ipam.find(prefix_len,'child_with_no_children')
    assert alloc_30 == '196.25.2.0/30'
    with db() as conn:
        sql = "SELECT id,parent FROM netrino_prefix " \
              "WHERE a4=? AND prefix_len=?"
        pl30 = conn.execute(sql,(3289973248,prefix_len)).fetchall()
    assert len(pl30)==1
    pl30 = pl30[0]
    assert pl30['parent'] == empty_child['id']

def test_allocate_from_fully_populated_block():
    prefix_len = 30
    with pytest.raises(NotFoundError) as nfinfo:
        ipam.find(prefix_len, 'child_prefix_with_children')
    assert "Unable to allocate address from pool 'child_prefix_with_children'" in str(
        nfinfo.value)

def test_allocate_non_free_prefix():
    with pytest.raises(ValidationError) as veinfo:
        ipam.allocate_prefix('already_used','196.25.0.0/24','allocated')
    assert "Unable to allocate '196.25.0.0/24', not free" in str(
        veinfo.value)

def test_allocate_free_prefix():
    result = ipam.allocate_prefix('new_prefix','196.25.4.0/24','allocated')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE id=?"
        result = conn.execute(sql, result['id']).fetchall()
    assert len(result) == 1
    assert result[0]['a4'] == 3289973760
    result[0].pop('creation_time')
    model = netrino_prefix()
    model.sql_id(result[0].pop('id'))
    model.update(result[0])
    assert model['parent'] == sup['id']

def test_add_prefix_above_existing():
    intermediate = ipam.add_prefix('child', '196.25.2.0/23')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE id=?"
        existed = conn.execute(sql, empty_child['id']).fetchone()
    assert existed['parent'] == intermediate['id']
    allocated = conn.execute(sql, pl30['id']).fetchone()
    assert allocated['parent'] == empty_child['id']

def test_delete_prefix_with_assigned_children():
    supernet_is_parent = ipam.add_prefix('child', '196.25.4.0/24')
    ipam.delete_prefix('196.25.0.0/23')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE a4=? AND " \
              "prefix_len>=? ORDER BY prefix_len"
        rows = conn.execute(sql,(3289972736,22)).fetchall()
    assert len(rows) == 3
    assert rows[1]['free'] == False
    assert rows[2]['free'] == False
    assert rows[1]['parent'] == rows[2]['parent'] == rows[0]['parent']
    assert supernet_is_parent['parent'] == sup['id']

def test_delete_prefix_with_child():
    ipam.delete_prefix('196.25.2.0/23')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE a4=? AND " \
              "prefix_len>=? ORDER BY prefix_len"
        rows = conn.execute(sql,(3289973248,23)).fetchall()
    assert len(rows) > 1
    assert rows[0]['type']=='hidden'
    assert rows[0]['free'] == False
    assert rows[1]['parent'] == sup['id']
    assert rows[2]['parent'] == rows[1]['id']

def test_delete_prefix_with_child_assignments():
    ipam.delete_prefix('196.25.2.0/24')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE a4=? AND " \
              "prefix_len>=? ORDER BY prefix_len"
        rows = conn.execute(sql,(3289973248,24)).fetchall()
    assert len(rows) > 1
    assert rows[0]['type']=='hidden'
    assert rows[0]['free'] == False
    assert rows[1]['parent'] == sup['id']
    assert rows[2]['parent'] == sup['id']

def test_release_non_existing_prefix():
    ipam.release_prefix('1.1.1.1/32')

def test_release_prefix_not_assigned():
    # this is not an assignment, it was created
    with pytest.raises(ValidationError) as veinfo:
        ipam.release_prefix('196.25.0.0/23')
    assert "sub" in str(veinfo.value)
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE a4=? AND " \
              "prefix_len>=? ORDER BY prefix_len"
        rows = conn.execute(sql,(3289972736,23)).fetchall()
    assert len(rows)>1
    assert rows[0]['free'] == False
    assert rows[0]['type'] == "hidden"

def test_release_assigned_prefix():
    ipam.release_prefix('196.25.0.0/24')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE a4=? AND " \
              "prefix_len>=? ORDER BY prefix_len"
        rows = conn.execute(sql,(3289972736,24)).fetchall()
    assert len(rows) == 1
    assert rows[0]['type'] == 'hidden'
    assert rows[0]['free'] == True

def test_release_only_assignment_in_parent():
    ipam.release_prefix('196.25.1.0/24')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE a4>=? AND a4<=? " \
              "AND prefix_len>=? ORDER BY prefix_len"
        rows = conn.execute(sql, (3289972736,3289972992,23)).fetchall()
    assert len(rows) == 1
    assert rows[0]['free'] == True

def test_add_delete_prefix():
    ipam.add_prefix('to_be_removed','10.0.0.0/16')
    ipam.delete_prefix('10.0.0.0/16')
    with db() as conn:
        sql = "SELECT * FROM netrino_prefix WHERE a4=? " \
              "AND prefix_len=? ORDER BY prefix_len"
        rows = conn.execute(sql, (167772160,16)).fetchall()
    assert len(rows) == 0


import time

def test_speed():
    start = time.time()
    for i in range(2000):
        ipam.find(32,'test_tag')
    end = time.time()
    duration = end-start
    assert duration<10
    with db() as conn:
        count = conn.execute("SELECT count(id) AS n FROM netrino_prefix "
                            "WHERE prefix_len=32").fetchone()
        assert count['n'] >= 2000

