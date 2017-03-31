from smpchecker import smpchecker as smpchecker
from enum import Enum
from datetime import datetime

class Event(Enum):
     spotted = 1


class PeppolMember:
    '''
    Object representing a PeppolMember
    '''

    def __init__(self, peppolidentifier):
        self.id= None
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
        rows = smpchecker.query_db('select id, peppolidentifier, first_seen, last_seen from peppolmembers where peppolidentifier=?',
                                       [peppolidentifier])
        if len(rows) > 0:
            row = rows.pop(0)
            self.id=row[0]
            self.peppolidentifier=row[1]
            self.firstseen=row[2]
            self.lastseen=row[3]


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
        self.lastseen=time

    def get_smpentries(self):
        rows = smpchecker.query_db('select peppolmember_id, documentidentifier from smpentries where peppolmember_id=?',
                            [self.id])
        result = []
        for row in rows:
            e = SMPEntry(row[1], row[0])
            e.reload()
            result.append(e)
        return result



class SMPEntry:
    '''
    Object representing SMP entry
    '''

    def __init__(self, documentidentifier, peppolmember_id):
        self.id = None
        self.documentidentifier=documentidentifier
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
        self.load(self.documentidentifier,self.peppolmember_id)

    def load(self, documentidentifier, peppolmember_id):
        sql = 'select id, documentidentifier, certificate_not_before, certificate_not_after,'
        sql += 'endpointurl, peppolmember_id, first_seen, last_seen from smpentries where documentidentifier=? '
        sql += 'and peppolmember_id=?'
        rows = smpchecker.query_db(sql, [documentidentifier, peppolmember_id])

        if len(rows) > 0:
            row = rows.pop(0)
            self.id=row[0]
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
        self.lastseen=time




