"""Source relationship classification, not one-process-per-instance assumptions."""
import tempfile
from pathlib import Path
import unittest
from lieppos_hal_audit.inventory import audit
from test_parsers import AIDL, HIDL

PROJECT = Path(__file__).absolute().parents[1]


class C51Relationships(unittest.TestCase):
    def setUp(self):
        self.parent = PROJECT / '.tmp'
        self.parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.parent)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()
        try: self.parent.rmdir()
        except OSError: pass

    def put(self, name, content):
        (self.root / name).write_text(content)

    def test_shared_process_resolves_two_contracts_not_two_services(self):
        self.put('one.xml', AIDL)
        self.put('two.xml', AIDL.replace('ITest/default', 'ITest/second'))
        self.put('hal.rc', 'service shared /vendor/bin/hw/shared\n    interface aidl android.hardware.test.ITest/default\n    interface aidl android.hardware.test.ITest/second\n')
        result = audit([self.root])
        self.assertEqual(result['summary']['init_relationships_resolved'], 2)
        self.assertEqual({r['classification'] for r in result['init_relationships']}, {'SHARED_SERVICE'})
        self.assertEqual(len(result['init_services']), 1)

    def test_lazy_requires_rc_and_registration_evidence_not_disabled_alone(self):
        self.put('hal.xml', AIDL)
        self.put('hal.rc', 'service test /vendor/bin/hw/test\n    interface aidl android.hardware.test.ITest/default\n    disabled\n    oneshot\n')
        first = audit([self.root])
        self.assertEqual(first['init_relationships'][0]['classification'], 'RESOLVED_SERVICE')
        self.put('Android.bp', 'cc_binary { name: "test", srcs: ["main.cpp"], init_rc: ["hal.rc"], vintf_fragments: ["hal.xml"], }')
        self.put('main.cpp', 'AServiceManager_registerLazyService(service, instance);')
        second = audit([self.root])
        self.assertEqual(second['init_relationships'][0]['classification'], 'LAZY_SERVICE')

    def test_module_init_helper_is_not_automatically_the_hal_process(self):
        self.put('hal.xml', AIDL)
        self.put('hal.rc', 'service helper /vendor/bin/helper\n')
        self.put('Android.bp', 'cc_binary { name: "actual_hal", srcs: ["main.cpp"], init_rc: ["hal.rc"], vintf_fragments: ["hal.xml"], }')
        self.put('main.cpp', 'int main() { return 0; }')
        result = audit([self.root])
        self.assertFalse(result['init_relationships'][0]['resolved_in_source'])
        self.assertEqual(result['summary']['init_relationships_remaining'], 1)

    def test_proprietary_service_requires_exact_rc_not_filename_only(self):
        self.put('hal.xml', AIDL)
        self.put('hal.rc', 'service exact /vendor/bin/hw/blob\n    interface aidl android.hardware.test.ITest/default\n')
        self.put('proprietary-files.txt', 'vendor/bin/hw/blob\n')
        relation = audit([self.root])['init_relationships'][0]
        self.assertEqual(relation['classification'], 'PROPRIETARY_SERVICE')
        self.assertIn('SOURCE_UNAVAILABLE', relation['categories'])
        self.assertTrue(relation['resolved_in_source'])

    def test_framework_owner_is_not_confused_with_vendor_owner(self):
        self.put('hal.xml', AIDL.replace('type="device"', 'type="framework"'))
        self.put('hal.rc', 'service system_hal /system_ext/bin/hw/service\n    interface aidl android.hardware.test.ITest/default\n')
        relation = audit([self.root])['init_relationships'][0]
        self.assertEqual(relation['classification'], 'FRAMEWORK_OWNED')
        self.assertTrue(relation['resolved_in_source'])

    def test_stock_comment_candidate_stays_missing_metadata(self):
        self.put('hal.xml', AIDL)
        self.put('proprietary-files.txt', '# stock init service claimed\nvendor/bin/hw/android.hardware.test-service.vendor\n')
        relation = audit([self.root])['init_relationships'][0]
        self.assertEqual(relation['classification'], 'MISSING_METADATA')
        self.assertFalse(relation['resolved_in_source'])
        self.assertEqual(relation['unverified_process_candidates'][0]['name'], 'claimed')

    def test_passthrough_is_not_an_unresolved_init_service(self):
        self.put('hal.xml', HIDL.replace('hwbinder', 'passthrough'))
        result = audit([self.root])
        self.assertEqual(result['init_relationships'], [])
        self.assertEqual(result['summary']['init_relationships_remaining'], 0)

    def test_override_and_mixed_protocol_intent_not_platform_pass(self):
        self.put('base.xml', AIDL)
        self.put('override.xml', AIDL.replace('format="aidl"', 'format="aidl" override="true"'))
        self.put('hidl.xml', HIDL)
        review = audit([self.root])['vintf_review']
        self.assertEqual(review['overlaps'][0]['classification'], 'INTENTIONAL_OVERRIDE')
        self.assertEqual(review['mixed_transport'][0]['classification'], 'DISTINCT_PROTOCOL_IDENTITIES_REVIEWED')
        self.assertEqual(review['platform_validation'], 'NOT_RUN')
        self.assertIsNone(review['confirmed_platform_conflicts'])
