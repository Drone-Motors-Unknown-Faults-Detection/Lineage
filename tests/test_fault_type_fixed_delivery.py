import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from experiments.fault_type_fixed_delivery import verify_archive


class FixedDeliveryTests(unittest.TestCase):
    def fixture(self,root,bad=False):
        path=root/'results.zip'; data=b'not raw data'
        index={'files':[{'path':'output/results.json','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest() if not bad else '0'*64}]}
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('output/results.json',data); z.writestr('BUNDLE_INDEX.json',json.dumps(index))
        return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_files':1}

    def test_verified_archive_and_whole_sha_tamper(self):
        with tempfile.TemporaryDirectory() as folder:
            item=self.fixture(Path(folder))
            self.assertEqual(verify_archive(item)['member_sha_status'],'PASS')
            with self.assertRaisesRegex(ValueError,'whole SHA'): verify_archive(dict(item,sha256='0'*64))

    def test_member_digest_tamper_with_valid_crc_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,'member SHA'): verify_archive(self.fixture(Path(folder),bad=True))


if __name__=='__main__': unittest.main()
