"""Focused C51C source/shared-policy regression. NOT Linux timer or hardware execution."""
import hashlib
import os
from pathlib import Path
import subprocess
import unittest

from test_c51_source import WORKSPACE

KERNEL = WORKSPACE / 'android/kernel/ulefone/gq5012bf1'


@unittest.skipUnless(os.environ.get('LIEPPOS_C51_SOURCE_TESTS') == '1', 'opt-in local C51C source tests')
class C51CKernel(unittest.TestCase):
    def test_actual_shared_policy_native_sanitized_and_source_order_guards(self):
        result = subprocess.run(['python3', '-B', str(KERNEL / 'tools/ulefone/gq5012bf1/tests/vibrator/run-tests.py')],
                                capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count('TOTAL 12/12'), 3)
        self.assertIn('SOURCE_ORDER 4/4', result.stdout)

    def test_actual_recipe_and_stable_kernel_abi_not_generic_trigger_patch(self):
        data = (KERNEL / 'configs/c44-reference.config').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), '40de208ba474abfac862ada26301d5a8b26490141e8c944ed303a3ccce8fd2fc')
        self.assertIn(b'# CONFIG_LEDS_TRIGGER_ONESHOT is not set', data)
        self.assertIn(b'CONFIG_LEDS_REGULATOR_VIBRATOR=m', data)
        self.assertIn(b'CONFIG_CFI_CLANG=y', data)
        self.assertIn(b'CONFIG_MODVERSIONS=y', data)
        source = (KERNEL / 'drivers/leds/regulator-vibrator.c').read_text()
        self.assertIn('vibr->vibr_cdev.groups = vibr_groups', source)
        self.assertIn('CLOCK_BOOTTIME', source)
        self.assertIn('reg_vibr_due(&vibr->state', source)
        self.assertNotIn('create_singlethread_workqueue', source)
        self.assertNotIn('led_blink_set_oneshot', source)
        for attribute in ['timeout_abi', 'max_duration_ms', 'duration_ms', 'last_error']:
            self.assertIn('dev_attr_' + attribute + '.attr', source)
        # Source presence does not certify the running kernel, permissions,
        # asynchronous PMIC OFF success, KMI or hardware process-death behavior.
