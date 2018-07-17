import json

from luxon import db

def get_element_metadata(uuid, interface):
    """Finds element login metadata for a given uuid.

    Args:
        uuid(str): Uuid of the element.
        interface(str): The Interface in question.

    Returns:
        dict build from json fetched from the database, if any, else None.
    """
    with db() as cur:
        sql = 'SELECT metadata FROM luxon_element_interface WHERE' \
              'id=? AND interface=?'
        result = cur.execute(sql, (uuid, interface))
        result = result.fetchone()
    if result:
        return json.loads(result)
    return None
