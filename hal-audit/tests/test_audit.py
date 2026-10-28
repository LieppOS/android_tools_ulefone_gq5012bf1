"""Integration, deterministic serialization and no-source-mutation tests."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from lieppos_hal_audit.inventory import audit, COLUMNS
from lieppos_hal_audit.device import apply_device_coverage, attach_runtime, runtime_properties
from lieppos_hal_audit.report import export, csv_text, validate_report
from lieppos_hal_audit.safety import safe_output, write_output, checked_path, open_directory
from test_parsers import AIDL, HIDL

PROJECT = Path(__file__).absolute().parents[1]


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp_parent = PROJECT / '.tmp'
        self.temp_parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.temp_parent)
        self.base = Path(self.temp.name)
        self.root = self.base / 'source'
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()
        try: self.temp_parent.rmdir()
        except OSError: pass

    def put(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def codes(self, result):
        return [d['code'] for d in result['diagnostics']]

    def full_source(self):
        self.put('hal.xml', AIDL)
        self.put('hal.rc', 'service test /vendor/bin/hw/test\n    interface aidl android.hardware.test.ITest/default\n    seclabel u:r:test:s0\n')
        self.put('main.cpp', 'int main() { return 0; }')
        self.put('Android.bp', 'cc_binary { name: "test", srcs: ["main.cpp"], init_rc: ["hal.rc"], vintf_fragments: ["hal.xml"], }')
        self.put('file_contexts', '/vendor/bin/hw/test u:object_r:test_exec:s0\n')

    def test_full_source_links(self):
        self.full_source()
        result = audit([self.root])
        row = result['inventory'][0]
        self.assertTrue(row['properties']['IMPLEMENTED_IN_SOURCE'])
        self.assertEqual(row['init_service'], 'test')
        self.assertEqual(row['executable'], '/vendor/bin/hw/test')
        self.assertEqual(row['selinux'][0]['context'], 'u:object_r:test_exec:s0')
        self.assertIsNone(row['properties']['HARDWARE_VERIFIED'])
        self.assertNotIn('MISSING_INIT_IN_SCAN', self.codes(result))
        self.assertNotIn('MISSING_EXECUTABLE_REFERENCE', self.codes(result))

    def test_missing_service(self):
        self.put('hal.xml', AIDL)
        result = audit([self.root])
        self.assertIn('MISSING_IMPLEMENTATION_IN_SCAN', self.codes(result))
        self.assertIn('MISSING_INIT_IN_SCAN', self.codes(result))
        self.assertEqual(result['inventory'][0]['implementation_status'], 'UNKNOWN')

    def test_duplicate_detection(self):
        self.put('one.xml', AIDL)
        self.put('two.xml', AIDL)
        result = audit([self.root])
        self.assertEqual(self.codes(result).count('DUPLICATE_HAL'), 1)
        self.assertEqual(len(result['inventory']), 1)
        self.assertEqual(len(result['declarations']), 2)

    def test_odm_override_not_duplicate_error(self):
        self.put('one.xml', AIDL)
        self.put('two.xml', AIDL.replace('format="aidl"', 'format="aidl" override="true"'))
        result = audit([self.root])
        self.assertIn('OVERRIDE_OVERLAP', self.codes(result))
        self.assertNotIn('DUPLICATE_HAL', self.codes(result))

    def test_potential_aidl_hidl_conflict(self):
        self.put('one.xml', AIDL)
        self.put('two.xml', HIDL)
        self.assertIn('POTENTIAL_AIDL_HIDL_CONFLICT', self.codes(audit([self.root])))

    def test_multiple_versions_review(self):
        self.put('one.xml', AIDL)
        self.put('two.xml', AIDL.replace('<version>2</version>', '<version>3</version>'))
        self.assertIn('MULTIPLE_HAL_VERSIONS', self.codes(audit([self.root])))

    def test_passthrough_does_not_need_init(self):
        self.put('one.xml', HIDL.replace('hwbinder', 'passthrough'))
        self.assertNotIn('MISSING_INIT_IN_SCAN', self.codes(audit([self.root])))

    def test_missing_executable(self):
        self.put('hal.rc', 'service foo /vendor/bin/hw/nonexistent\n')
        self.assertIn('MISSING_EXECUTABLE_REFERENCE', self.codes(audit([self.root])))

    def test_missing_vintf_only_explicit_registration(self):
        self.put('hal.rc', 'service foo /vendor/bin/foo\n    interface aidl x.y.IFoo/default\nservice helper /vendor/bin/helper\n')
        result = audit([self.root])
        self.assertEqual(self.codes(result).count('MISSING_VINTF_IN_SCAN'), 1)

    def test_proprietary_candidate_does_not_imply_presence(self):
        self.put('hal.xml', AIDL)
        self.put('proprietary-files.txt', 'vendor/bin/hw/android.hardware.test-service.vendor\n')
        row = audit([self.root])['inventory'][0]
        self.assertEqual(len(row['binary_candidates']), 1)
        self.assertFalse(row['properties']['IMPLEMENTED_IN_SOURCE'])
        self.assertIsNone(row['properties']['PROPRIETARY_IMPLEMENTATION'])
        self.assertIsNone(row['properties']['SERVICE_PRESENT'])

    def test_prebuilt_module_not_source_implementation(self):
        self.put('hal.xml', AIDL)
        self.put('Android.bp', 'cc_prebuilt_binary { name: "test", srcs: ["blob.cpp"], vintf_fragments: ["hal.xml"], }')
        self.put('blob.cpp', 'not source built')
        row = audit([self.root])['inventory'][0]
        self.assertFalse(row['properties']['IMPLEMENTED_IN_SOURCE'])
        self.assertEqual(row['modules'][0]['source_status'], 'PREBUILT_REFERENCE')

    def test_partial_source_unresolved(self):
        self.put('hal.xml', AIDL)
        self.put('Android.bp', 'cc_binary { name: "test", srcs: ["missing.cpp"], vintf_fragments: ["hal.xml"], }')
        self.assertEqual(audit([self.root])['inventory'][0]['implementation_status'], 'UNKNOWN')

    def test_one_missing_source_keeps_partial_module_unknown(self):
        self.full_source()
        self.put('Android.bp', 'cc_binary { name: "test", srcs: ["main.cpp", "missing.cpp"], vintf_fragments: ["hal.xml"], }')
        result = audit([self.root])
        self.assertIn('SOURCE_REFERENCE_UNRESOLVED', self.codes(result))
        self.assertEqual(result['inventory'][0]['implementation_status'], 'UNKNOWN')

    def test_missing_root_is_diagnostic(self):
        result = audit([self.base / 'unavailable'])
        self.assertIn('ROOT_UNAVAILABLE', self.codes(result))
        self.assertEqual(result['inventory'], [])

    def test_empty_root_not_fake_data(self):
        result = audit([self.root])
        self.assertEqual(result['inventory'], [])
        self.assertEqual(result['roots'][0]['text_files'], 0)

    def test_deterministic_overlap_roots(self):
        self.put('sub/hal.xml', AIDL)
        one = audit([self.root, self.root / 'sub'])
        two = audit([self.root / 'sub', self.root])
        self.assertEqual(one, two)
        self.assertEqual(len(one['declarations']), 1)

    def test_json_csv_markdown_export(self):
        self.full_source()
        result = audit([self.root])
        output = safe_output(self.base / 'output', [self.root])
        export(result, output)
        loaded = json.loads((output / 'HAL-INVENTORY.json').read_text())
        self.assertTrue(validate_report(loaded))
        rows = list(csv.DictReader(io.StringIO((output / 'HAL-INVENTORY.csv').read_text())))
        self.assertEqual(list(rows[0]), COLUMNS)
        self.assertEqual(rows[0]['interface'], 'android.hardware.test.ITest')
        self.assertIn('Not a Soong build', (output / 'SCAN-SUMMARY.md').read_text())

    def test_shape_validation_rejects_invalid_report(self):
        self.put('hal.xml', AIDL)
        result = audit([self.root])
        result['inventory'][0]['version'] = 2
        with self.assertRaises(ValueError): validate_report(result)

    def test_quoted_csv(self):
        self.put('hal.xml', AIDL)
        result = audit([self.root])
        result['inventory'][0]['notes'] = 'quote "this", newline\nhere'
        rows = list(csv.DictReader(io.StringIO(csv_text(result))))
        self.assertEqual(rows[0]['notes'], result['inventory'][0]['notes'])

    def test_read_only_source_hashes_and_metadata(self):
        self.full_source()
        def snap():
            return {str(p): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns, p.stat().st_mode) for p in self.root.rglob('*') if p.is_file()}
        before = snap()
        audit([self.root])
        self.assertEqual(before, snap())

    def test_no_source_file_execution(self):
        sentinel = self.base / 'executed'
        self.put('evil.sh', 'touch ' + str(sentinel))
        self.put('evil.rc', 'on boot\n    exec /bin/sh -c "touch ' + str(sentinel) + '"\n')
        self.put('Android.bp', 'execute("touch ' + str(sentinel) + '")')
        audit([self.root])
        self.assertFalse(sentinel.exists())

    def test_symlink_input_not_followed(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'hal.xml').write_text(AIDL)
        (self.root / 'linked').symlink_to(outside, target_is_directory=True)
        (self.root / 'file.xml').symlink_to(outside / 'hal.xml')
        result = audit([self.root])
        self.assertEqual(result['declarations'], [])
        self.assertEqual(self.codes(result).count('SYMLINK_SKIPPED'), 2)

    def test_symlink_root_and_ancestor_rejected(self):
        (self.base / 'link').symlink_to(self.root, target_is_directory=True)
        self.put('sub/hal.xml', AIDL)
        for path in [self.base / 'link', self.base / 'link/sub']:
            self.assertIn('ROOT_UNAVAILABLE', self.codes(audit([path])))

    def test_output_cannot_be_inside_or_above_source(self):
        for output in [self.root, self.root / 'reports', self.base]:
            with self.assertRaises(ValueError): safe_output(output, [self.root])

    def test_output_symlink_rejected(self):
        (self.base / 'link').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError): safe_output(self.base / 'link/out', [])

    def test_output_file_symlink_rejected(self):
        self.put('original.xml', AIDL)
        output = self.base / 'output'
        output.mkdir()
        (output / 'HAL-INVENTORY.json').symlink_to(self.root / 'original.xml')
        with self.assertRaises(OSError): write_output(output, 'HAL-INVENTORY.json', 'bad')
        self.assertEqual((self.root / 'original.xml').read_text(), AIDL)

    def test_output_hardlink_rejected_before_truncate(self):
        p = self.put('original.xml', AIDL)
        output = self.base / 'output'
        output.mkdir()
        os.link(p, output / 'HAL-INVENTORY.json')
        with self.assertRaises(ValueError): write_output(output, 'HAL-INVENTORY.json', 'bad')
        self.assertEqual(p.read_text(), AIDL)

    def test_secret_calibration_and_binary_files_skipped(self):
        for name in ['private_key.xml', 'secret.xml', 'calibration.xml', 'keys/hal.xml', 'firmware/hal.xml', 'blob.so', 'certificate.pem']:
            self.put(name, AIDL)
        self.put('nul.xml', '\0binary')
        self.put('invalid.xml', '<manifest/>').write_bytes(b'\xff')
        result = audit([self.root])
        self.assertEqual(result['declarations'], [])
        self.assertEqual(len(result['provenance']), 0)
        self.assertIn('BINARY_SKIPPED', self.codes(result))
        self.assertIn('ENCODING_UNKNOWN', self.codes(result))

    def test_protected_path_rejected_lexically(self):
        # No filesystem calls into the forbidden directory, even for this test.
        with self.assertRaises(ValueError): checked_path('/home/armol/androido_dalykai/not-accessed')

    def test_size_cap(self):
        self.put('large.xml', 'x' * (2 * 1024 * 1024 + 1))
        self.assertIn('FILE_TOO_LARGE', self.codes(audit([self.root])))

    def test_runtime_properties_redacted(self):
        p = self.base / 'getprop.txt'
        p.write_text('[ro.serialno]: [PRIVATE]\n[init.svc.nfc_hal_service]: [running]\n[sys.boot_completed]: [1]\n')
        evidence = runtime_properties(p)
        self.assertEqual(len(evidence['selected_properties']), 2)
        self.assertNotIn('PRIVATE', json.dumps(evidence))

    def test_runtime_not_hardware_verified(self):
        self.put('proprietary-files.txt', '# stock init service nfc_hal_service\nvendor/bin/hw/android.hardware.nfc-service-st\n')
        result = audit([self.root])
        apply_device_coverage(result)
        p = self.base / 'getprop.txt'
        p.write_text('[init.svc.nfc_hal_service]: [running]\n')
        attach_runtime(result, runtime_properties(p))
        row = result['inventory'][0]
        self.assertTrue(row['properties']['SERVICE_STARTED'])
        self.assertIsNone(row['properties']['HARDWARE_VERIFIED'])
        self.assertEqual(row['interface'], 'UNKNOWN')

    def test_runtime_sensitive_path_rejected(self):
        with self.assertRaises(ValueError): runtime_properties(self.base / 'private_key.txt')

    def test_empty_device_coverage_does_not_invent_rows(self):
        result = audit([self.root])
        apply_device_coverage(result)
        self.assertEqual(result['inventory'], [])
        self.assertEqual(len(result['coverage']), 24)
        self.assertTrue(all(c['required_by_device'] == 'UNKNOWN' for c in result['coverage']))

    def test_cli_dry_run(self):
        self.put('hal.xml', AIDL)
        before = sorted(p.name for p in self.root.iterdir())
        env = dict(os.environ, PYTHONPATH=str(PROJECT / 'src'), PYTHONDONTWRITEBYTECODE='1')
        p = subprocess.run([sys.executable, '-B', '-m', 'lieppos_hal_audit.cli', '--root', str(self.root)], env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['records'], 1)
        self.assertEqual(before, sorted(p.name for p in self.root.iterdir()))

    def test_cli_strict_diagnostics_exit(self):
        self.put('hal.xml', AIDL)
        env = dict(os.environ, PYTHONPATH=str(PROJECT / 'src'), PYTHONDONTWRITEBYTECODE='1')
        p = subprocess.run([sys.executable, '-B', '-m', 'lieppos_hal_audit.cli', '--root', str(self.root), '--fail-on-diagnostics'], env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)

    def test_dynamic_bp_does_not_claim_complete_source(self):
        self.full_source()
        self.put('Android.bp', 'cc_binary { name: "test", srcs: ["main.cpp"] + unknown_sources, vintf_fragments: ["hal.xml"], }')
        result = audit([self.root])
        self.assertEqual(result['inventory'][0]['implementation_status'], 'UNKNOWN')
        self.assertIn('BP_DYNAMIC', self.codes(result))

    def test_source_registration_and_kernel_references(self):
        self.full_source()
        self.put('main.cpp', 'auto node = "/dev/test";\nAServiceManager_addService(service, "android.hardware.test.ITest/default");\n')
        row = audit([self.root])['inventory'][0]
        self.assertEqual(row['registration'], 'SOURCE_REFERENCE_NOT_RUNTIME')
        self.assertEqual(len(row['kernel_dependencies']), 1)
        self.assertIn('/dev/test', row['kernel_dependency'])

    def test_filename_alone_does_not_invent_kernel_dependency(self):
        self.put('vendor/lieppos/lieppos.mk', '# unrelated content')
        self.put('proprietary-files.txt', 'vendor/bin/hw/android.hardware.health-service.example\n')
        result = audit([self.root])
        apply_device_coverage(result)
        self.assertEqual(result['inventory'][0]['kernel_dependencies'], [])

    def test_retained_vs_extract_only_proprietary_classification(self):
        self.put('proprietary-files.txt', 'vendor/bin/hw/android.hardware.nfc-service-st\nvendor/bin/hw/android.hardware.health-service.example;EXTRACT_ONLY\n')
        result = audit([self.root])
        apply_device_coverage(result)
        by_category = {r['subsystem']: r for r in result['inventory']}
        self.assertEqual(by_category['NFC']['implementation_status'], 'PROPRIETARY_IMPLEMENTATION')
        self.assertIsNone(by_category['NFC']['properties']['SERVICE_PRESENT'])
        self.assertEqual(by_category['Health']['implementation_status'], 'UNKNOWN')

    def test_security_category_does_not_hide_keymint_artifact(self):
        self.put('hal.xml', AIDL.replace('android.hardware.test', 'android.hardware.secure_element'))
        self.put('proprietary-files.txt', 'vendor/bin/hw/android.hardware.security.keymint@3.0-service.trustkernel\n')
        result = audit([self.root])
        apply_device_coverage(result)
        self.assertEqual(len(result['inventory']), 2)
        self.assertTrue(any('keymint' in row['executable'] for row in result['inventory']))

    def test_thermal_app_reference_not_invented_native_hal(self):
        self.put('Android.bp', 'android_app_import { name: "M170infisens", apk: "missing.apk", }')
        result = audit([self.root])
        apply_device_coverage(result)
        row = result['inventory'][0]
        self.assertEqual(row['subsystem'], 'Thermal camera')
        self.assertEqual(row['interface'], 'UNKNOWN')
        self.assertEqual(row['source_availability'], 'PREBUILT_APP_REFERENCE')
        self.assertEqual(row['source_repository'], str(self.root))
        self.assertFalse(row['properties']['IMPLEMENTED_IN_SOURCE'])

    def test_ancillary_hardware_artifact_is_included(self):
        self.put('proprietary-files.txt', 'vendor/bin/hw/android.hardware.memtrack-service.mediatek\n')
        result = audit([self.root])
        apply_device_coverage(result)
        self.assertEqual(len(result['inventory']), 1)

    def test_sh_binary_src_resolves_executable_without_execution(self):
        self.put('script.sh', '#!/bin/sh\nexit 0\n')
        self.put('script.rc', 'service script /system/bin/script\n')
        self.put('Android.bp', 'sh_binary { name: "script", src: "script.sh", init_rc: ["script.rc"], }')
        result = audit([self.root])
        self.assertEqual(result['modules'][0]['source_status'], 'IMPLEMENTED_IN_SOURCE')
        self.assertNotIn('MISSING_EXECUTABLE_REFERENCE', self.codes(result))

    def test_prebuilt_config_not_classified_proprietary_code(self):
        self.put('Android.bp', 'prebuilt_etc { name: "permissions.xml", src: "permissions.xml", }')
        result = audit([self.root])
        self.assertEqual(result['modules'][0]['source_status'], 'CONFIGURATION_REFERENCE')

    def test_runtime_symlink_rejected(self):
        actual = self.base / 'actual.txt'
        actual.write_text('[sys.boot_completed]: [1]')
        (self.base / 'getprop.txt').symlink_to(actual)
        with self.assertRaises(OSError): runtime_properties(self.base / 'getprop.txt')

    def test_cli_export_smoke(self):
        self.full_source()
        env = dict(os.environ, PYTHONPATH=str(PROJECT / 'src'), PYTHONDONTWRITEBYTECODE='1')
        out = self.base / 'reports'
        p = subprocess.run([sys.executable, '-B', '-m', 'lieppos_hal_audit.cli', '--root', str(self.root), '--output', str(out)], env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(validate_report(json.loads((out / 'HAL-INVENTORY.json').read_text())))
