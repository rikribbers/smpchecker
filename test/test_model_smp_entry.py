import os
import smpchecker
import unittest
import tempfile
import sqlite3
from smpchecker.model import model as model
from datetime import datetime
from smpchecker import smpcheckerapp

peppol_id = None
doc_id = 'doc_id:1'


class TestSmpEntry(unittest.TestCase):

    def test_all(self):
        self.db_fd, smpchecker.app.config['DATABASE'] = tempfile.mkstemp()
        smpchecker.app.config['TESTING'] = True
        self.app = smpchecker.app.test_client()
        with smpchecker.app.app_context():
            smpcheckerapp.init_db()
            self.create_with_existing_peppol_member()
            self.create_with_non_existing_peppol_member()
            self.create_with_not_null_endpointurl()
            self.create_with_not_null_not_after()
            self.create_with_not_null_not_before()

        os.close(self.db_fd)
        os.unlink(smpchecker.app.config['DATABASE'])

    def create_with_existing_peppol_member(self):
        p = model.PeppolMember('peppol_id')
        p.create()
        p.reload()

        # create with existing PEPPOL member
        e = model.SMPEntry(doc_id, p.id)

        e_dummy = model.SMPEntry(p.id, 'doc_id:dummy')
        self.assertFalse(e.exists())
        self.assertFalse(e_dummy.exists())
        e.certificate_not_after = datetime.now()
        e.certificate_not_before = datetime.now()
        e.endpointurl = 'url'
        e.create()
        self.assertTrue(e.exists())
        self.assertFalse(e_dummy.exists())

    def create_with_non_existing_peppol_member(self):
        e = model.SMPEntry(doc_id, None)
        self.assertFalse(e.exists())
        e.certificate_not_after = datetime.now()
        e.certificate_not_before = datetime.now()
        e.endpointurl = 'url'
        with self.assertRaises(sqlite3.IntegrityError):
            e.create()

    def create_with_not_null_not_after(self):
        p = model.PeppolMember('create_with_not_null_not_after')
        p.create()
        p.reload()

        e = model.SMPEntry(doc_id, p.id)
        self.assertFalse(e.exists())
        # do not set  e.certificate_not_after = datetime.now()
        e.certificate_not_before = datetime.now()
        e.endpointurl = 'url'
        with self.assertRaises(sqlite3.IntegrityError):
            e.create()

    def create_with_not_null_not_before(self):
        p = model.PeppolMember('create_with_not_null_not_before')
        p.create()
        p.reload()

        e = model.SMPEntry(doc_id, p.id)
        self.assertFalse(e.exists())
        e.certificate_not_after = datetime.now()
        # do not set e.certificate_not_before = datetime.now()
        e.endpointurl = 'url'
        with self.assertRaises(sqlite3.IntegrityError):
            e.create()

    def create_with_not_null_endpointurl(self):
        p = model.PeppolMember('create_with_not_null_endpointurl')
        p.create()
        p.reload()

        e = model.SMPEntry(doc_id, p.id)
        self.assertFalse(e.exists())
        e.certificate_not_after = datetime.now()
        e.certificate_not_before = datetime.now()
        # do not set e.endpointurl = 'url'
        with self.assertRaises(sqlite3.IntegrityError):
            e.create()


if __name__ == '__main__':
    # intialise the database
    unittest.main()
