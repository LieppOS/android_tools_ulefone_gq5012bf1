"""C51B opt-in tests: real core/policy, fake sysfs and child processes; NOT Binder IPC."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_c51_source import PROJECT, WORKSPACE, MTK, BOARD, COMPILER
from lieppos_hal_audit.inventory import audit
from lieppos_hal_audit.device import apply_device_coverage


@unittest.skipUnless(os.environ.get('LIEPPOS_C51_SOURCE_TESTS') == '1', 'opt-in local C51B tests')
class C51BLifecycle(unittest.TestCase):
    def test_native_policy_lifecycle_and_fault_cases(self):
        parent = PROJECT / '.tmp'
        parent.mkdir(exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(dir=parent) as tmp:
                base = Path(tmp)
                sources = [MTK / ('vibrator/' + n) for n in ['Controller.cpp', 'LedSwitch.cpp', 'OneShot.cpp', 'DriverTimed.cpp']]
                sources.append(BOARD / 'vibrator/tests/LifecycleTest.cpp')
                for mode, flags in [('native', []), ('asan-ubsan', ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']),
                                    ('tsan', ['-fsanitize=thread', '-fno-omit-frame-pointer'])]:
                    binary = base / mode
                    command = [os.environ.get('CXX', COMPILER), '-std=c++17', '-pthread', '-Wall', '-Wextra', '-Werror', '-O1', '-g', *flags,
                               '-I' + str(MTK / 'vibrator/include'), '-I' + str(BOARD / 'vibrator'), *map(str, sources), '-o', str(binary)]
                    env = dict(os.environ, TMPDIR=str(base), ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1', TSAN_OPTIONS='halt_on_error=1')
                    built = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
                    self.assertEqual(built.returncode, 0, built.stderr)
                    fixtures = base / (mode + '-fixtures')
                    fixtures.mkdir()
                    run = subprocess.run([str(binary), str(fixtures)], env=env, capture_output=True, text=True, timeout=30)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    self.assertIn('TOTAL 22/22', run.stdout)
        finally:
            try: parent.rmdir()
            except OSError: pass

    def test_deployment_gate_precedes_all_device_io_and_registration(self):
        source = (BOARD / 'vibrator/main.cpp').read_text()
        self.assertLess(source.index('deploymentAllowed()'), source.index('discoverDriverTimedRegulatorLed('))
        self.assertLess(source.index('discoverDriverTimedRegulatorLed('), source.index('controller->off()'))
        self.assertLess(source.index('controller->off()'), source.index('AServiceManager_addService('))
        self.assertNotIn('discoverRegulatorLed(', source)
        policy = (BOARD / 'vibrator/VibratorPolicy.h').read_text()
        self.assertIn('deploymentAllowed() { return false; }', policy)
        rc = (BOARD / 'vibrator/vibrator-gq5012bf1.rc').read_text()
        self.assertIn('\n    disabled\n', rc)
        self.assertIn('\n    oneshot\n', rc)
        self.assertNotIn('user root', rc)
        report = audit([MTK, BOARD])
        apply_device_coverage(report)
        row = next(r for r in report['inventory'] if r['interface'] == 'android.hardware.vibrator.IVibrator')
        self.assertIn('Driver-owned timeout ABI v1', row['source_coverage']['kernel_timeout_dependency'])
        self.assertTrue(any(p.endswith('/vibrator/OneShot.cpp') for p in row['source_coverage']['implementation_files']))
        self.assertIsNone(row['validation_properties']['SOONG_BUILD_PASSED'])
        self.assertIsNone(row['validation_properties']['HARDWARE_VERIFIED'])

    def test_kernel_config_proposal_is_unapplied_and_dry_runs_in_owned_fixture(self):
        kernel = WORKSPACE / 'android/kernel/ulefone/gq5012bf1'
        relative = Path('arch/arm64/configs/gki_defconfig')
        data = (kernel / relative).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), '6416f396c578a92b57e94b30edefda1629a63ef6baeb9f94bd87832943a8cee5')
        self.assertNotIn(b'CONFIG_LEDS_TRIGGER_ONESHOT=y', data)
        parent = PROJECT / '.tmp'
        parent.mkdir(exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(dir=parent) as tmp:
                out = Path(tmp) / relative
                out.parent.mkdir(parents=True)
                out.write_bytes(data)
                result = subprocess.run(['patch', '--dry-run', '-p1', '-i', str(MTK / 'vibrator/oneshot-config-proposal.patch')], cwd=tmp, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(out.read_bytes(), data)
        finally:
            try: parent.rmdir()
            except OSError: pass
        self.assertEqual((kernel / relative).read_bytes(), data)

    def test_transport_remains_genuine_and_unsupported_features_share_tested_policy(self):
        source = (BOARD / 'vibrator/Vibrator.cpp').read_text()
        self.assertIn('status(policy_.on(timeoutMs, static_cast<bool>(callback)))', source)
        self.assertIn('status(policy_.off())', source)
        self.assertIn('Policy::capabilities()', source)
        self.assertIn('fromServiceSpecificError(result.error)', source)
        self.assertIn('EX_UNSUPPORTED_OPERATION', source)
        self.assertIn('EX_ILLEGAL_ARGUMENT', source)
        # 24 frozen methods minus capabilities/on/off/effects/amplitude = 19.
        self.assertEqual(source.count('{ return unsupported(); }'), 24 - 5)
        self.assertIn('#include <aidl/android/hardware/vibrator/BnVibrator.h>', (BOARD / 'vibrator/Vibrator.h').read_text())
        # No execution/ABI claim: this check links tested request logic to the
        # still-uncompiled genuine Android adapter; it does not mock BnVibrator.
