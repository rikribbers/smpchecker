import os
import smpchecker
import unittest
import tempfile
import sqlite3
from smpchecker.model import model as model
from datetime import datetime
from smpchecker import smpcheckerapp
class TestPeppolMember(unittest.TestCase):

    def test_all(self):
        self.db_fd, smpchecker.app.config['DATABASE'] = tempfile.mkstemp()
        smpchecker.app.config['TESTING'] = True
        self.app = smpchecker.app.test_client()
        with smpchecker.app.app_context():
            smpcheckerapp.init_db()
            self.init()
            self.create_and_exist()
            self.update_load()
            self.reload()
        os.close(self.db_fd)
        os.unlink(smpchecker.app.config['DATABASE'])

    def init(self):
        time = datetime.now()
        my_id = 'pepid_test_init'
        p = model.PeppolMember(my_id)
        self.assertEqual(my_id, p.peppolidentifier)
        self.assertTrue(time < p.firstseen)

    def create_and_exist(self):
        my_id = 'pepid_test_create'
        p = model.PeppolMember(my_id)
        p_dummy = model.PeppolMember('pepid_dummy')
        self.assertFalse(p.exists())
        self.assertFalse(p_dummy.exists())
        p.create()
        self.assertTrue(p.exists())
        self.assertFalse(p_dummy.exists())

    def update_load(self):
        id = 'pepid_test_update'
        p1 = model.PeppolMember(id)
        p1.create()
        p1.lastseen = datetime.now()
        p1.update()

        p2 = model.PeppolMember(id)
        p2.load(id)
        self.assertEquals(p1.peppolidentifier, p2.peppolidentifier)
        self.assertEquals(p1.firstseen, p2.firstseen)
        self.assertEquals(p1.lastseen, p2.lastseen)

    def reload(self):
        p1 = model.PeppolMember('pepid_reload')
        p1.create()
        p2 = model.PeppolMember('pepid_reload_dummy')
        # Test reload should through non exists exception
        #TODO catch proper exception
        with self.assertRaises(FileNotFoundError):
            p2.reload()
        # Overwrite p2 peppolid, reload and compare to p1
        p2.peppolidentifier = p1.peppolidentifier
        p2.reload()
        self.assertEqual(p1.firstseen, p2.firstseen)

if __name__ == '__main__':
    # intialise the database
    smpcheckerapp.init_db()
    unittest.main()
