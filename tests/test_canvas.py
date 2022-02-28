import unittest
from httpx import AsyncClient
import asyncio
from canvas.canvas import Canvas

init_cookie = r'''ps_rvm_ZkiN={"pssid":"cUfHplPvgnivwQ3R-1641287405864","last-visit":"1641287408017"}; log_session_id=5e1a4f5641b3b064e8ce886c4a5fba7f; _legacy_normandy_session=hdpPmm_00h29fyt09UYvjA+efztve0sPZqBQf2rGW7KkaKfXr9swCyyGzG4WQnRwxx-daT9p6SUC7-kPMTZaAeHw4R_ncoyiTp2nD7-wKPhAGwtIxQ3apzIDqZu89aQv9bApvZ77GL-8ruTWiAkLvXIq5_NNR_RptQd_p1YJXj6BIu6cmxh5wya935QFLJxhxnnmlw9uDJmGph0iQUGhZ6P9lTOUekGuK8u2hHOmLg4_5CJrkA2bFtVYcYpvvykH2M1RtsqX13a6hATdIUtp0-HJRb0bYMIWP31K7vQInQ6JyNdAcnaNkrjZEHY0i0Z5MnXaAFUBi3OjCdQdmyvP0X_lsOMNWZtrM8a__47BHfrSFToZwVudVCzUzDARem8LJIx0S3_s2sVYW47TF7sR4mBeqEPCPt9QrdGjp2UzR4p4NS_3sEAVVYzeZg7t5aAXfW6NdlYyS9ETszti7HWXbbl98MESrr4LFwRrI-gaBSdJUHB3MTZ7nE18gIOeXVl4fU-AjH_1iUVeJI0dM8JwpHt7ThzPdI8KjladVkT9ADmUMt8Xb-y936j8WZIUca21fy76elFO2K18lo8IZKzGoqKSd0omSrUD1DrluUutNRFJVRUa9P7PFSjWriiMiM8kxwbmFhXHKWzgrKVsoABhDbygW28b2OW5EuHs0ePvAFs3A.EsrHwIbsK_qpCd7ryxIxYXAmGgg.YhxKTQ; canvas_session=hdpPmm_00h29fyt09UYvjA+efztve0sPZqBQf2rGW7KkaKfXr9swCyyGzG4WQnRwxx-daT9p6SUC7-kPMTZaAeHw4R_ncoyiTp2nD7-wKPhAGwtIxQ3apzIDqZu89aQv9bApvZ77GL-8ruTWiAkLvXIq5_NNR_RptQd_p1YJXj6BIu6cmxh5wya935QFLJxhxnnmlw9uDJmGph0iQUGhZ6P9lTOUekGuK8u2hHOmLg4_5CJrkA2bFtVYcYpvvykH2M1RtsqX13a6hATdIUtp0-HJRb0bYMIWP31K7vQInQ6JyNdAcnaNkrjZEHY0i0Z5MnXaAFUBi3OjCdQdmyvP0X_lsOMNWZtrM8a__47BHfrSFToZwVudVCzUzDARem8LJIx0S3_s2sVYW47TF7sR4mBeqEPCPt9QrdGjp2UzR4p4NS_3sEAVVYzeZg7t5aAXfW6NdlYyS9ETszti7HWXbbl98MESrr4LFwRrI-gaBSdJUHB3MTZ7nE18gIOeXVl4fU-AjH_1iUVeJI0dM8JwpHt7ThzPdI8KjladVkT9ADmUMt8Xb-y936j8WZIUca21fy76elFO2K18lo8IZKzGoqKSd0omSrUD1DrluUutNRFJVRUa9P7PFSjWriiMiM8kxwbmFhXHKWzgrKVsoABhDbygW28b2OW5EuHs0ePvAFs3A.EsrHwIbsK_qpCd7ryxIxYXAmGgg.YhxKTQ; _csrf_token=NsIjQhe1TnzdeSgzVOPbUDzMxZe361/vmEGTqLzvQyxkp3BwVuUqNo4pW1UEmbo7a7Tx9tCFHIT0NOrkhY5sZQ=='''

class TestCanvas(unittest.TestCase):

    def setUp(self) -> None:
        self.canvas = Canvas()

    def test_initialize(self):
        self.assertEqual(type(self.canvas), Canvas)

    def test_get_marked_courses(self):
        self.client = AsyncClient()
        self.client.headers.update({'cookie': init_cookie})
        res = asyncio.run(self.canvas.get_marked_courses(self.client))
        self.assertFalse(res == [])
        