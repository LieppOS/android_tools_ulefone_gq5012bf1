"""Synthetic contract, init, Blueprint and extraction parser tests."""
from pathlib import Path
import unittest
from lieppos_hal_audit.vintf import parse_xml
from lieppos_hal_audit.init_rc import parse_init
from lieppos_hal_audit.android_bp import parse_bp
from lieppos_hal_audit.proprietary_files import parse_proprietary

AIDL = '<manifest type="device"><hal format="aidl"><name>android.hardware.test</name><version>2</version><fqname>ITest/default</fqname></hal></manifest>'
HIDL = '<manifest><hal format="hidl"><name>android.hardware.test</name><transport>hwbinder</transport><fqname>@1.0::ITest/default</fqname></hal></manifest>'


class Parsers(unittest.TestCase):
    def setUp(self):
        self.diagnostics = []
        self.diag = lambda *args: self.diagnostics.append(args)

    def xml(self, text):
        return parse_xml(text, 'test.xml', self.diag)

    def codes(self):
        return [d[0] for d in self.diagnostics]

    def test_valid_fixture(self):
        rows, requirements = self.xml((Path(__file__).parent / 'fixtures/valid.xml').read_text())
        self.assertEqual(len(rows), 2)
        self.assertEqual(requirements, [])
        self.assertEqual(self.diagnostics, [])
        self.assertEqual(rows[0]['version'], '2')
        self.assertEqual(rows[1]['transport'], 'passthrough')

    def test_aidl_default_version_is_one(self):
        rows, _ = self.xml(AIDL.replace('<version>2</version>', ''))
        self.assertEqual(rows[0]['version'], '1')
        self.assertEqual(rows[0]['version_origin'], 'aidl-default-1')

    def test_structured_instances_and_versions(self):
        rows, _ = self.xml('<manifest><hal format="hidl"><name>x.y</name><version>2.0</version><version>2.1</version><transport>hwbinder</transport><interface><name>IFoo</name><instance>a</instance><instance>b</instance></interface></hal></manifest>')
        self.assertEqual(len(rows), 4)
        self.assertEqual({r['version'] for r in rows}, {'2.0', '2.1'})

    def test_redundant_fqname_structured_deduplicated(self):
        rows, _ = self.xml(AIDL.replace('</hal>', '<interface><name>ITest</name><instance>default</instance></interface></hal>'))
        self.assertEqual(len(rows), 1)

    def test_matrix_separate_from_declaration(self):
        ds, rs = self.xml(AIDL.replace('manifest', 'compatibility-matrix'))
        self.assertEqual(ds, [])
        self.assertEqual(len(rs), 1)

    def test_unknown_version(self):
        rows, _ = self.xml(AIDL.replace('<version>2</version>', '<version>future</version>'))
        self.assertEqual(rows[0]['version'], 'UNKNOWN')
        self.assertIn('UNKNOWN_VERSION', self.codes())

    def test_empty_explicit_aidl_version_unknown_not_default_one(self):
        rows, _ = self.xml(AIDL.replace('<version>2</version>', '<version/>'))
        self.assertEqual(rows[0]['version'], 'UNKNOWN')
        self.assertIn('UNKNOWN_VERSION', self.codes())

    def test_version_range_not_fabricated(self):
        rows, _ = self.xml(HIDL.replace('<fqname>@1.0::ITest/default</fqname>', '<version>1.0-3</version><interface><name>ITest</name><instance>default</instance></interface>'))
        self.assertEqual(rows[0]['version'], 'UNKNOWN')

    def test_malformed_xml_line_diagnostic(self):
        self.assertEqual(self.xml('<manifest>\n<hal></manifest>')[0], [])
        self.assertEqual(self.diagnostics[0][0], 'MALFORMED_XML')
        self.assertEqual(self.diagnostics[0][2], 2)

    def test_entity_rejected(self):
        self.assertEqual(self.xml('<!DOCTYPE manifest [<!ENTITY x "payload">]><manifest/>')[0], [])
        self.assertIn('XML_DTD_REJECTED', self.codes())

    def test_bad_fqname(self):
        rows, _ = self.xml(HIDL.replace('@1.0::ITest/default', 'unrecognized'))
        self.assertEqual(rows, [])
        self.assertIn('UNKNOWN_FQNAME', self.codes())

    def test_missing_package(self):
        rows, _ = self.xml(AIDL.replace('<name>android.hardware.test</name>', ''))
        self.assertEqual(rows, [])
        self.assertIn('UNKNOWN_HAL_HEADER', self.codes())

    def test_xml_comment_line_anchor(self):
        rows, _ = self.xml('<!-- <hal>fake</hal> -->\n' + AIDL)
        self.assertEqual(rows[0]['line'], 2)

    def test_permissions_xml_not_hal(self):
        self.assertEqual(self.xml('<permissions><feature name="android.hardware.nfc"/></permissions>'), ([], []))

    def test_regex_matrix_instance_unresolved(self):
        _, rows = self.xml('<compatibility-matrix><hal format="aidl"><name>x</name><interface><name>IFoo</name><regex-instance>.*</regex-instance></interface></hal></compatibility-matrix>')
        self.assertEqual(rows, [])
        self.assertIn('REGEX_INSTANCE', self.codes())

    def test_init_aidl_and_hidl(self):
        services = parse_init('service test /vendor/bin/hw/test --flag\n    interface aidl android.hardware.test.ITest/default\n    interface android.hardware.test@1.0::ITest a b\n    user system\n    group input log\n    seclabel u:r:test:s0\n    disabled\non boot\n    exec /evil\n', 'x.rc', self.diag)
        self.assertEqual(len(services), 1)
        self.assertEqual(len(services[0]['interfaces']), 3)
        self.assertEqual(services[0]['seclabel'], 'u:r:test:s0')
        self.assertTrue(services[0]['disabled'])
        self.assertEqual(services[0]['groups'], ['input', 'log'])

    def test_init_continuation(self):
        services = parse_init('service test /vendor/bin/test \\\n    --arg\n', 'x.rc', self.diag)
        self.assertEqual(services[0]['args'], ['--arg'])
        self.assertEqual(services[0]['line'], 1)

    def test_init_malformed_does_not_crash(self):
        parse_init('service broken\nservice quote "oops\nservice final /x \\', 'x.rc', self.diag)
        self.assertIn('MALFORMED_INIT', self.codes())
        self.assertIn('INIT_CONTINUATION', self.codes())

    def test_init_import_not_executed(self):
        parse_init('import /path/not/opened\n', 'x.rc', self.diag)
        self.assertIn('INIT_IMPORT_UNRESOLVED', self.codes())

    def test_bp_nested_properties_not_outer(self):
        modules = parse_bp('/* cc_binary { fake } */ cc_binary { name: "real", srcs: ["main.cpp"], arch: {arm64: {name: "not_real"}}, init_rc: ["a.rc"], vintf_fragments: ["a.xml"], }', 'Android.bp', self.diag)
        self.assertEqual(modules[0]['name'], 'real')
        self.assertEqual(modules[0]['properties']['srcs'], ['main.cpp'])

    def test_bp_braces_inside_strings(self):
        modules = parse_bp('cc_binary { name: "a", cflags: ["-DSTR={}"], }', 'Android.bp', self.diag)
        self.assertEqual(len(modules), 1)

    def test_bp_malformed(self):
        self.assertEqual(parse_bp('cc_binary { name: "x",', 'Android.bp', self.diag), [])
        self.assertIn('MALFORMED_BP', self.codes())

    def test_bp_dynamic_reported(self):
        parse_bp('cc_binary { name: "x", srcs: ["one.cc"] + variables, }', 'Android.bp', self.diag)
        self.assertIn('BP_DYNAMIC', self.codes())

    def test_proprietary_options_and_service_comment(self):
        entries = parse_proprietary('# hardware-facing ELF; stock init service actual.name\nvendor/bin/hw/foo;SYMLINK=vendor/bin/foo;EXTRACT_ONLY|1234\n# DT_NEEDED by vendor/bin/hw/foo\nvendor/lib64/libdep.so\n', 'proprietary-files.txt', self.diag)
        self.assertEqual(entries[0]['init_reference'], 'actual.name')
        self.assertEqual(entries[0]['aliases'], ['vendor/bin/foo'])
        self.assertTrue(entries[0]['extract_only'])
        self.assertEqual(entries[0]['hash_pin'], '1234')
        self.assertEqual(entries[1]['dependency_of'], ['vendor/bin/hw/foo'])

    def test_proprietary_rename_and_module(self):
        entries = parse_proprietary('-vendor/lib/a.so:vendor/lib/b.so;MODULE=foo\n', 'list', self.diag)
        self.assertEqual(entries[0]['path'], 'vendor/lib/b.so')
        self.assertTrue(entries[0]['module'])

    def test_proprietary_bad_path(self):
        entries = parse_proprietary('../secret.pem\n/absolute\n', 'list', self.diag)
        self.assertEqual(entries, [])
        self.assertIn('MALFORMED_EXTRACTION_ENTRY', self.codes())
