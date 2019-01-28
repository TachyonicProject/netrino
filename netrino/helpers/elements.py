from luxon import g
from luxon import db
from luxon.helpers.api import raw_list


def elements_with_interface(interface):
    """For a given interface, return all elements that supports this
    interface.

    Args:
        interface (str): Netrino Interface in question.

    Returns:
        list of elements id's and their names that supports this interface.
    """
    sql = 'SELECT netrino_element.name,netrino_element_interface.element_id ' \
          'FROM netrino_element,netrino_element_interface ' \
          'WHERE interface=? AND ' \
          'netrino_element.id = netrino_element_interface.element_id'
    with db() as conn:
        return raw_list(g.current_request,
                        conn.execute(sql,interface).fetchall())
