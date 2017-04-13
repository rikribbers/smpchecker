from smpchecker import smpcheckerapp as smpchecker
from enum import Enum
from datetime import datetime


class SupportedDocumentTypes(Enum):
    SI_10_CREDITNOTE = 'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2::CreditNote##urn:www.cenbii.eu:transaction:biicoretrdm014:ver1.0:#urn:www.peppol.eu:bis:peppol5a:ver1.0#urn:www.simplerinvoicing.org:si-ubl:credit-note:ver1.0.x::2.0'
    SI_10_INVOICE = 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:www.cenbii.eu:transaction:biicoretrdm010:ver1.0:#urn:www.peppol.eu:bis:peppol4a:ver1.0#urn:www.simplerinvoicing.org:si-ubl:invoice:ver1.0.x::2.0'
    PEPPOL_4A = 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:www.cenbii.eu:transaction:biitrns010:ver2.0:extended:urn:www.peppol.eu:bis:peppol4a:ver2.0::2.1'
    SI_11 = 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:www.cenbii.eu:transaction:biitrns010:ver2.0:extended:urn:www.peppol.eu:bis:peppol4a:ver2.0:extended:urn:www.simplerinvoicing.org:si:si-ubl:ver1.1.x::2.1'
    SI_12 = 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice##urn:www.cenbii.eu:transaction:biitrns010:ver2.0:extended:urn:www.peppol.eu:bis:peppol4a:ver2.0:extended:urn:www.simplerinvoicing.org:si:si-ubl:ver1.2::2.1'


class PeppolMember:
    '''
    Object representing a PeppolMember
    '''

    def __init__(self, peppolidentifier):
        self.id = None
        self.peppolidentifier = peppolidentifier
        self.firstseen = datetime.now()
        self.lastseen = None

    def create(self):
        smpchecker.query_db('insert into peppolmembers(peppolidentifier,first_seen) values (?,?)',
                            [self.peppolidentifier, self.firstseen])
        self.load(self.peppolidentifier)

    def reload(self):
        self.load(self.peppolidentifier)

    def load(self, peppolidentifier):
        rows = smpchecker.query_db(
            'select id, peppolidentifier, first_seen, last_seen from peppolmembers where peppolidentifier=?',
            [peppolidentifier])
        if len(rows) > 0:
            row = rows.pop(0)
            self.id = row[0]
            self.peppolidentifier = row[1]
            self.firstseen = row[2]
            self.lastseen = row[3]

    def exists(self):
        for row in smpchecker.query_db('select id from peppolmembers where peppolidentifier=?',
                                       [self.peppolidentifier]):
            return True
        # no rows found
        return False

    def update(self):
        time = datetime.now()
        smpchecker.query_db('update peppolmembers set last_seen=? where peppolidentifier=?',
                            [time, self.peppolidentifier])
        self.lastseen = time

    def get_scan_result(self):
        rows = smpchecker.query_db('select peppolmember_id, documentidentifier from smpentries where peppolmember_id=?',
                                   [self.id])
        result = []
        for row in rows:
            e = SMPEntry(row[1], row[0])
            e.reload()
            result.append(e)

        return SMPScanResult(self, result)

    def serialize(self):
        return {
            'peppolidentifier': self.peppolidentifier,
            'firstseen': self.firstseen,
            'lastseen': self.lastseen,
        }


class SMPEntry:
    '''
    Object representing SMP entry
    '''

    def __init__(self, documentidentifier, peppolmember_id):
        self.id = None
        self.documentidentifier = documentidentifier
        self.certificate_not_before = None
        self.certificate_not_after = None
        self.endpointurl = None
        self.peppolmember_id = peppolmember_id
        self.firstseen = datetime.now()
        self.lastseen = None

    def create(self):
        sql = 'insert into smpentries(documentidentifier, certificate_not_before, certificate_not_after, '
        sql += 'endpointurl, peppolmember_id, first_seen, last_seen) values (?,?,?,?,?,?,?)'
        smpchecker.query_db(sql, [self.documentidentifier, self.certificate_not_before,
                                  self.certificate_not_after, self.endpointurl,
                                  self.peppolmember_id, self.firstseen, self.lastseen])
        self.load(self.documentidentifier, self.peppolmember_id)

    def reload(self):
        self.load(self.documentidentifier, self.peppolmember_id)

    def load(self, documentidentifier, peppolmember_id):
        sql = 'select id, documentidentifier, certificate_not_before, certificate_not_after,'
        sql += 'endpointurl, peppolmember_id, first_seen, last_seen from smpentries where documentidentifier=? '
        sql += 'and peppolmember_id=?'
        rows = smpchecker.query_db(sql, [documentidentifier, peppolmember_id])

        if len(rows) > 0:
            row = rows.pop(0)
            self.id = row[0]
            self.documentidentifier = row[1]
            self.certificate_not_before = row[2]
            self.certificate_not_after = row[3]
            self.endpointurl = row[4]
            self.peppolmember_id = row[5]
            self.firstseen = row[6]
            self.lastseen = row[7]

    def exists(self):
        for row in smpchecker.query_db('select id from smpentries where peppolmember_id=? and documentidentifier=?',
                                       [self.peppolmember_id, self.documentidentifier]):
            return True
        # no rows found
        return False

    def update(self):
        # TODO update fiels from scan.
        time = datetime.now()
        smpchecker.query_db('update smpentries set last_seen=? where peppolmember_id=? and documentidentifier=?',
                            [time, self.peppolmember_id, self.documentidentifier])
        self.lastseen = time


class SMPScanResult:
    def __init__(self, member, smpentries):
        self.peppolidentifier = member.peppolidentifier
        self.si_10_creditnote = False
        self.si_10_invoice = False
        self.si_11 = False
        self.si_12 = False
        self.peppol4a = False
        self.smpentries = smpentries

        # SMP entries not supported if last_seen from smp_entry is before last seen peppol member
        # i.o.w. when the last scan is done the last_seen from smp entry is not updated
        # TODO make a unittest for this.
        for smpentry in smpentries:
            if SupportedDocumentTypes.SI_10_CREDITNOTE.value == smpentry.documentidentifier:
                self.si_10_creditnote = True
            elif SupportedDocumentTypes.SI_10_INVOICE.value == smpentry.documentidentifier:
                self.si_10_invoice = True
            elif SupportedDocumentTypes.SI_11.value == smpentry.documentidentifier:
                self.si_11 = True
            elif SupportedDocumentTypes.SI_12.value == smpentry.documentidentifier:
                self.si_11 = True
            elif SupportedDocumentTypes.PEPPOL_4A.value == smpentry.documentidentifier:
                self.si_11 = True


class Accesspoint:
    def __init__(self, endpointurl, certificate_not_after):
        self.endpointurl = endpointurl,
        self.certificate_not_after = certificate_not_after

    def serialize(self):
        return {
            'endpointurl': self.endpointurl,
            'certificate_not_after': self.certificate_not_after,
        }


class Accesspoints:
    def __init__(self):
        self.accesspoints = None

    def load(self):
        sql = 'select distinct endpointurl,certificate_not_after from smpentries'
        rows = smpchecker.query_db(sql)

        for row in rows:
            a = Accesspoint(row[0], row[2])
            self.accesspoints.append(a)
