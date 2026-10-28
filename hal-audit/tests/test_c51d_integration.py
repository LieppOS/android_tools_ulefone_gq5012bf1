"""C51D static integration-contract regression. NOT Soong linking, Binder IPC or hardware.

Pins the evidence behind the C51D decisions so a drifting premise fails loudly:
single IVibrator replacement versus the stock combined Manager service, the
canonical sysfs node and its stock SELinux label, and the kernel ABI constants.
"""
import hashlib
import os
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from test_c51_source import WORKSPACE, BOARD, MTK

PLATFORM = Path('/mnt/SamsungSSD/android/lineage-24.0')  # Read-only; never built here.
STOCK = WORKSPACE / 'android/vendor/ulefone/gq5012bf1/proprietary/vendor'
KERNEL = WORKSPACE / 'android/kernel/ulefone/gq5012bf1'
NODE = '/devices/platform/regulator-vibrator/leds/vibrator'


def hals(path):
    return [(h.findtext('name'), h.findtext('version'), h.findtext('fqname'))
            for h in ET.parse(path).getroot().iter('hal')]


@unittest.skipUnless(os.environ.get('LIEPPOS_C51_SOURCE_TESTS') == '1', 'opt-in local C51D tests')
class C51DIntegration(unittest.TestCase):
    def test_source_service_is_single_ivibrator_exclusive_with_stock_manager_binary(self):
        self.assertEqual(hals(BOARD / 'vibrator/vibrator-gq5012bf1.xml'),
                         [('android.hardware.vibrator', '2', 'IVibrator/default')])
        rc = (BOARD / 'vibrator/vibrator-gq5012bf1.rc').read_text()
        self.assertIn('interface aidl android.hardware.vibrator.IVibrator/default', rc)
        self.assertNotIn('IVibratorManager', rc)
        if not STOCK.is_dir():
            self.skipTest('read-only stock vendor evidence unavailable')
        binary = (STOCK / 'bin/hw/android.hardware.vibrator-service.mediatek').read_bytes()
        self.assertEqual(hashlib.sha256(binary).hexdigest(),
                         'ab4fc6285875b3f6ce70d1a7f15b10465d149fbb34a6c3bd8caa8d2d95b6573a')
        # One stock process serves BOTH instances; they cannot be split.
        for marker in [b'BnVibratorManager', b'BnVibrator12createBinder', b'AServiceManager_addService']:
            self.assertIn(marker, binary)
        self.assertEqual(sorted(hals(STOCK / 'etc/vintf/manifest/vibrator-mtk-default.xml')),
                         [('android.hardware.vibrator', '2', 'IVibrator/default'),
                          ('android.hardware.vibrator', '2', 'IVibratorManager/default')])
        stock_rc = (STOCK / 'etc/init/vibrator-mtk-default.rc').read_text()
        name = re.compile(r'^service (\S+) ', re.M)
        # Same init service name: both rc files can never be installed together.
        self.assertEqual(name.findall(stock_rc), name.findall(rc))

    def test_framework_falls_back_to_single_default_vibrator_without_manager(self):
        java = PLATFORM / 'frameworks/base/services/core/java/com/android/server/vibrator/VintfHalVibratorManager.java'
        native = PLATFORM / 'frameworks/native/services/vibratorservice/VibratorManagerHalController.cpp'
        if not java.is_file() or not native.is_file():
            self.skipTest('read-only Android 17 platform source unavailable')
        j = java.read_text()
        self.assertIn('ServiceManager.isDeclared(IVibratorManager.DESCRIPTOR + "/default")', j)
        self.assertIn('ServiceManager.isDeclared(IVibrator.DESCRIPTOR + "/default")', j)
        self.assertIn('new LegacyHalVibratorManager(', j)
        n = native.read_text()
        self.assertIn('AServiceManager_isDeclared(serviceName.c_str())', n)
        self.assertIn('return std::make_shared<LegacyManagerHalWrapper>();', n)
        for matrix in ['compatibility_matrix.202604.xml', 'compatibility_matrix.202704.xml']:
            text = (PLATFORM / 'hardware/interfaces/compatibility_matrices' / matrix).read_text()
            self.assertRegex(text, r'<name>android.hardware.vibrator</name>\s*<version>1-4</version>\s*'
                                   r'<interface>\s*<name>IVibrator</name>')

    def test_canonical_node_needs_only_existing_stock_label_and_platform_rules(self):
        main = (BOARD / 'vibrator/main.cpp').read_text()
        self.assertIn('"/sys/devices/platform/regulator-vibrator", "vibrator"', main)
        contexts = (BOARD / 'vibrator/sepolicy/file_contexts').read_text()
        self.assertIn(r'/vendor/bin/hw/android\.hardware\.vibrator-service\.gq5012bf1 u:object_r:hal_vibrator_default_exec:s0', contexts)
        if not STOCK.is_dir() or not PLATFORM.is_dir():
            self.skipTest('read-only stock/platform policy evidence unavailable')
        cil = (STOCK / 'etc/selinux/vendor_sepolicy.cil').read_text()
        self.assertIn('(genfscon sysfs "%s" (u object_r sysfs_vibrator ((s0) (s0))))' % NODE, cil)
        hal = (PLATFORM / 'system/sepolicy/private/hal_vibrator.te').read_text()
        self.assertIn('allow hal_vibrator sysfs_vibrator:file rw_file_perms;', hal)
        self.assertIn('allow hal_vibrator sysfs_vibrator:dir search;', hal)
        domain = (PLATFORM / 'system/sepolicy/private/domain.te').read_text()
        self.assertIn('allow domain sysfs:lnk_file { getattr read };', domain)
        self.assertIn('allow domain sysfs:dir search;', domain)
        # Stock ueventd grants no system ownership of the C51C duration_ms node.
        self.assertNotIn('duration_ms', (STOCK / 'etc/ueventd.rc').read_text())

    def test_hal_parser_matches_committed_kernel_timeout_abi(self):
        header = (KERNEL / 'drivers/leds/regulator-vibrator-state.h').read_text()
        self.assertIn('#define REG_VIBR_MAX_MS 5000U', header)
        driver = (KERNEL / 'drivers/leds/regulator-vibrator.c').read_text()
        self.assertIn('return sysfs_emit(buf, "1\\n");', driver)
        self.assertIn('return sysfs_emit(buf, "%u\\n", REG_VIBR_MAX_MS);', driver)
        self.assertIn('ret = kstrtouint(buf, 10, &duration);', driver)
        self.assertIn('static DEVICE_ATTR_RW(duration_ms);', driver)
        timed = (MTK / 'vibrator/DriverTimed.cpp').read_text()
        self.assertIn('if (version != 1)', timed)
        self.assertIn('std::to_string(durationMs) + "\\n"', timed)
        self.assertIn('write("duration_ms", "0\\n")', timed)
        self.assertNotIn('"brightness"', timed)


if __name__ == '__main__':
    unittest.main()
