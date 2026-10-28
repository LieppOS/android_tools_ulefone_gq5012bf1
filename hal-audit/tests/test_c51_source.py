"""C51 native implementation tests; no counterfeit Android headers or phone access."""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from lieppos_hal_audit.inventory import audit

PROJECT = Path(__file__).absolute().parents[1]
WORKSPACE = PROJECT.parents[3]
MTK = WORKSPACE / 'android/hardware/mediatek/mt6878'
BOARD = WORKSPACE / 'android/hardware/ulefone/gq5012bf1'
COMPILER = '/usr/x86_64-pc-linux-gnu/gcc-bin/16/x86_64-pc-linux-gnu-g++'


@unittest.skipUnless(os.environ.get('LIEPPOS_C51_SOURCE_TESTS') == '1', 'opt-in local C51 implementation tests')
class C51Source(unittest.TestCase):
    def test_native_backend_compiles_and_passes_twelve_behavior_cases(self):
        parent = PROJECT / '.tmp'
        parent.mkdir(exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(dir=parent) as tmp:
                base = Path(tmp)
                sources = [MTK / 'vibrator/Controller.cpp', MTK / 'vibrator/LedSwitch.cpp', MTK / 'vibrator/OneShot.cpp', MTK / 'vibrator/DriverTimed.cpp', MTK / 'vibrator/tests/ControllerTest.cpp']
                for mode, flags in [('native', []), ('sanitized', ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
                    binary = base / mode
                    cmd = [os.environ.get('CXX', COMPILER), '-std=c++17', '-pthread', '-Wall', '-Wextra', '-Werror', '-O1', '-g', *flags,
                           '-I' + str(MTK / 'vibrator/include'), *map(str, sources), '-o', str(binary)]
                    build_env = dict(os.environ, TMPDIR=str(base))
                    built = subprocess.run(cmd, env=build_env, capture_output=True, text=True, timeout=90)
                    self.assertEqual(built.returncode, 0, built.stderr)
                    fixtures = base / (mode + '-fixtures')
                    fixtures.mkdir()
                    run_env = dict(build_env, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
                    run = subprocess.run([str(binary), str(fixtures)], env=run_env, capture_output=True, text=True, timeout=30)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    self.assertIn('TOTAL 12/12', run.stdout)
        finally:
            try: parent.rmdir()
            except OSError: pass

    def test_adapter_declares_exact_frozen_v2_method_set(self):
        fixture = (PROJECT / 'tests/fixtures/IVibrator-V2.aidl').read_bytes()
        self.assertEqual(hashlib.sha256(fixture).hexdigest(), '51161792eba95aee28a92723a1430b235e57e75751c24db04d84f7d83cca318e')
        license_text = (PROJECT / 'tests/fixtures/LICENSE.apache-2.0').read_bytes()
        self.assertEqual(hashlib.sha256(license_text).hexdigest(), 'cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30')
        methods = set(re.findall(r'^\s*[\w.]+(?:\[\])?\s+(\w+)\([^;]*\);', fixture.decode(), re.M))
        header = (BOARD / 'vibrator/Vibrator.h').read_text()
        declared = set(re.findall(r'ScopedAStatus\s+(\w+)\([^;]*\) override;', header))
        definitions = set(re.findall(r'ScopedAStatus Vibrator::(\w+)\(', (BOARD / 'vibrator/Vibrator.cpp').read_text()))
        self.assertEqual(len(methods), 24)
        self.assertEqual(declared, methods)
        self.assertEqual(definitions, methods)
        # This is a real-API/source conformance check, NOT Binder compilation or VTS.

    def test_source_build_fragment_init_and_registration_links(self):
        result = audit([MTK, BOARD])
        row = next(r for r in result['inventory'] if r['interface'] == 'android.hardware.vibrator.IVibrator')
        self.assertEqual((row['version'], row['instance'], row['transport']), ('2', 'default', 'binder'))
        self.assertEqual(row['init_service'], 'vendor.vibrator-default')
        self.assertTrue(row['properties']['IMPLEMENTED_IN_SOURCE'])
        self.assertEqual(row['registration'], 'SOURCE_REFERENCE_NOT_RUNTIME')
        module = row['modules'][0]
        self.assertIn('android.hardware.vibrator-V2-ndk', module['properties']['shared_libs'])
        self.assertIn('libmtk_regulator_vibrator', module['properties']['static_libs'])
        self.assertTrue(any(m['name'] == 'libmtk_regulator_vibrator' and m['source_status'] == 'IMPLEMENTED_IN_SOURCE' for m in result['modules']))
        self.assertEqual(row['selinux'][0]['context'], 'u:object_r:hal_vibrator_default_exec:s0')
        self.assertIsNone(row['properties']['HARDWARE_VERIFIED'])

    def test_service_has_no_invented_label_or_privilege_requirement(self):
        rc = (BOARD / 'vibrator/vibrator-gq5012bf1.rc').read_text()
        self.assertIn('user system', rc)
        self.assertNotIn('user root', rc)
        source = (BOARD / 'vibrator/main.cpp').read_text()
        # C51D: canonical device evidenced by live DT/sysfs and stock genfscon;
        # no LED-class enumeration (would need broad sysfs_leds/other-LED access).
        self.assertIn('"/sys/devices/platform/regulator-vibrator", "vibrator"', source)
        self.assertNotIn('"/sys/class/leds', source)
        self.assertIn('controller->off()', source)
        self.assertIn('AServiceManager_addService', source)
        self.assertNotIn('setenforce', source)
