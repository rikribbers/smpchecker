import hashlib
import logging

import dns

log = logging.getLogger(__name__)


def check(participantid):
    '''
    Checks whether the given participant id exists in the SML by doing an DNS lookup
    returns true if so otherwise false
    '''

    # Calculate the hash of the ID according to the SML specification
    # peppol needs the organisation to be lower case
    hash = hashlib.md5(str.lower(participantid).encode('UTF-8')).hexdigest()
    hostname = "b-" + hash + ".iso6523-actorid-upis.edelivery.tech.ec.europa.eu"
    log.debug('Hostname to resolve %s', hostname)

    # Look up the hostname in the SML; if the lookup succeeds, we know
    # there is an SMP for this organization, and we are done.
    # Normally, the calling application would then contact the SMP for
    # endpoint details.
    resolver = dns.resolver.Resolver()
    try:
        answers = resolver.query(hostname, "A")
    except dns.resolver.NXDOMAIN:
        log.error("Got NXDOMAIN for %s", hostname)
        return False

    for rdata in answers:
        log.debug('DNS A record found: %'
                  's', rdata)

    if len(answers) > 0:
        return True
    else:
        return False
