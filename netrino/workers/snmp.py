import json

from uuid import uuid4
from easysnmp import Session
from netrino.functions import sysdesc_to_vendor
from easysnmp.exceptions import EasySNMPTimeoutError
from luxon import GetLogger

log = GetLogger(__name__)

def discover_element(ipnet, community, client):
    """Uses SNMPv2 to discover Elements and Hostnames.

    Also adds discovered devices to Element manager, and snmp driver.

    Args:
        ipnet (obj): pypcalc.IPNetwork object to scan.
        community (str): SNMP community string.
        client (obj): psychokinetic client object.
    """
    for ip in ipnet:
        session = Session(hostname=ip.network(), community=community, version=2)
        element = {}
        try:
            # getting system.sysDescr.0
            sysdescription = session.get('1.3.6.1.2.1.1.1.0')
            vendor, os, os_ver = sysdesc_to_vendor(sysdescription.value)
            hostnamereq = session.get('.1.3.6.1.2.1.1.5.0')
            address = 'ipv%s' % ip.version()
            element['name'] = hostnamereq.value
            element[address] = ip.network()
            ce = client.execute('POST', 'v1/element',
                                element, endpoint="netrino")
            element_id = json.loads(ce.body.decode())['id']
            client.execute('POST', 'v1/element/' + element_id + '/driver',
                           {'driver':'snmp'}, endpoint="netrino")
        except EasySNMPTimeoutError as e:
            # print(str(e))
            # sys.exit(0)
            log.info("SNMP timeout on %s with community %s" %
                     (ip.network(), community))

    # (@Vuader) for now pretending to be a minion,
    # until that functionality has been added
    return {'task_id': str(uuid4())}
