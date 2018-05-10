"""
.. module:: tachyonic.netrino.functions
   :platform: Posix
   :synopsis: This Module contains all the Functions used by the Netrino API.

.. moduleauthor:: Dave Kruger <dave.kruger@tachyonic.org>


"""
import re


def sysdesc_to_vendor(desc):
    """Detects Vendor from SNMP system description.

    See full list of supported vendors at
    http://tachyonic.org/rst/netrino

    Args:
        desc: SNMP system.sysDescr.0

    Returns:
        Tuple with strings (Vendor, os, os_version)
    """
    isCisco = re.match(
        'Cisco ([^,]+) Software.*Version ([^,]+)', desc)
    if isCisco:
        return ("Cisco", isCisco.group(1), isCisco.group(1))

    isJunOS = re.search('JUNOS ([^ ]+)', desc)
    if isJunOS:
        return ("Juniper", "Junos", isJunOS.group(1))

    return ("Unknown Vendor", None, None)
