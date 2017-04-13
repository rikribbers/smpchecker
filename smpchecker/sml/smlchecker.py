import hashlib
import logging

from dns import resolver

log = logging.getLogger(__name__)


def check(peppoid):
    '''
    Checks whether the given PEPPOL identifier exists in the SML by doing an DNS lookup
    returns True if so otherwise False

    :param peppoid: a PEPPOL identifier
    :return: True or False
    '''

    if smpaddress(peppoid) is None:
        return False
    else:
        return True


def smpaddress(peppoid):
    '''
    Checks whether the given participant id exists in the SML by doing a DNS lookup
    returns None or the DNS A-record (ipaddress)

    :param peppolid: a PEPPOL identifier
    :return: str or None
    '''

    h = hostname(peppoid)
    log.debug('Hostname to resolve %s', h)
    # Look up the hostname in the SML; if the lookup succeeds, we know
    # there is an SMP for this organization, and we are done.
    # Normally, the calling application would then contact the SMP for
    # endpoint details.
    r = resolver.Resolver()
    try:
        answers = r.query(h, "A")
    except resolver.NXDOMAIN:
        log.error("Got NXDOMAIN for %s", h)
        return None

    for rdata in answers:
        log.debug('DNS A record found: %'
                  's', rdata)

    return str(answers[0])


def hostname(peppoid):
    '''
    Calculates the hostname for a specific PEPPOL identifier
    :param peppoid:
    :return:
    '''
    # Calculate the hash of the ID according to the SML specification
    # peppol needs the organisation to be lower case
    hash = hashlib.md5(str.lower(peppoid).encode('UTF-8')).hexdigest()
    return "b-" + hash + ".iso6523-actorid-upis.edelivery.tech.ec.europa.eu"
