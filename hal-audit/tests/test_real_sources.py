"""Opt-in read-only tests of explicitly authorized local inputs, never phone tests."""
import json
import os
from pathlib import Path
import unittest
from lieppos_hal_audit.device import apply_device_coverage, attach_runtime, runtime_properties
from lieppos_hal_audit.inventory import audit
from lieppos_hal_audit.report import csv_text, validate_report

ROOTS = ['/home/armol/LieppOS/android/' + p for p in [
    'device/ulefone/gq5012bf1', 'vendor/ulefone/gq5012bf1', 'vendor/mediatek/mt6878',
    'vendor/lieppos', 'hardware/mediatek/mt6878', 'hardware/ulefone/gq5012bf1']]
RUNTIME = '/mnt/SamsungSSD/lieppos-c46/hardware-approved/live-slotb-getprop-1.txt'


@unittest.skipUnless(os.environ.get('LIEPPOS_REAL_SOURCE_TESTS') == '1', 'opt-in authorized local inputs only')
class RealSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.one = audit(ROOTS)
        cls.before = {p['path']: (Path(p['path']).lstat().st_mtime_ns, Path(p['path']).lstat().st_mode) for p in cls.one['provenance']}
        cls.two = audit(list(reversed(ROOTS)))
        cls.after = {p: (Path(p).lstat().st_mtime_ns, Path(p).lstat().st_mode) for p in cls.before}

    def test_real_device_vendor_sources_parsed(self):
        self.assertEqual(len(self.one['roots']), 6)
        self.assertTrue(any(d['package'] == 'android.hardware.audio' for d in self.one['declarations']))
        self.assertTrue(any(b['path'].endswith('camerahalserver') for b in self.one['proprietary_entries']))
        self.assertTrue(any(m['name'] == 'TinyScreenService' for m in self.one['modules']))

    def test_repeated_real_scans_byte_deterministic(self):
        self.assertEqual(json.dumps(self.one, sort_keys=True), json.dumps(self.two, sort_keys=True))
        self.assertEqual(csv_text(self.one), csv_text(self.two))

    def test_source_hashes_and_metadata_unchanged(self):
        self.assertEqual(self.before, self.after)
        self.assertEqual(self.one['provenance'], self.two['provenance'])

    def test_device_lens_keeps_missing_implementations_unknown(self):
        result = json.loads(json.dumps(self.one))
        apply_device_coverage(result)
        self.assertTrue(validate_report(result))
        self.assertEqual(result['summary']['source_implemented_records'], 0)
        self.assertEqual(result['summary']['hardware_verified_records'], 0)
        self.assertEqual(len(result['coverage']), 24)

    def test_historical_android17_evidence_not_hal_certification(self):
        result = json.loads(json.dumps(self.one))
        apply_device_coverage(result)
        evidence = runtime_properties(RUNTIME)
        attach_runtime(result, evidence)
        props = {p['property']: p['value'] for p in evidence['selected_properties']}
        self.assertEqual(props['sys.boot_completed'], '1')
        self.assertEqual(props['ro.build.version.sdk'], '37')
        self.assertEqual(result['summary']['hardware_verified_records'], 0)
