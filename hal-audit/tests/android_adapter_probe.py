"""Manual real-platform AIDL/arm64 object probe. NOT Soong, linking, IPC or deployment.

Run with the existing authorized platform root as the only argument. All outputs
are disposable under hal-audit/.tmp; platform/source trees are read-only.
No generated header is supplied by this project: the SDK37 platform aidl emits
it from the exact frozen V2 source and hash.
"""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

PROJECT = Path(__file__).absolute().parents[1]
WORKSPACE = PROJECT.parents[3]
MTK = WORKSPACE / 'android/hardware/mediatek/mt6878'
BOARD = WORKSPACE / 'android/hardware/ulefone/gq5012bf1'


def run(platform):
    # Reject unresolved/symlink input roots before reading them, including the
    # protected location. This is an ordinary build-input guard, not AI policy tooling.
    from lieppos_hal_audit.safety import checked_path, open_directory
    platform = checked_path(platform)
    os.close(open_directory(platform))
    frozen = platform / 'hardware/interfaces/vibrator/aidl/aidl_api/android.hardware.vibrator/2'
    api = frozen / 'android/hardware/vibrator/IVibrator.aidl'
    digest = hashlib.sha256(api.read_bytes()).hexdigest()
    if digest != '51161792eba95aee28a92723a1430b235e57e75751c24db04d84f7d83cca318e':
        raise RuntimeError('Frozen V2 source differs from recorded authentic API')
    aidl = platform / 'out/host/linux-x86/bin/aidl'
    config = (platform / 'build/soong/cc/config/global.go').read_text()
    version = re.search(r'ClangDefaultVersion\s*=\s*"(clang-[\w]+)"', config)
    if not version:
        raise RuntimeError('Cannot identify source-defined ClangDefaultVersion')
    toolchain = platform / 'prebuilts/clang/host/linux-x86' / version[1]
    clang = toolchain / 'bin/clang++'
    api_hash = (frozen / '.hash').read_text().splitlines()[-1]
    if not re.fullmatch('[a-f0-9]{40}', api_hash):
        raise RuntimeError('Invalid authentic AIDL hash')
    print('FROZEN_API_SHA256', digest)
    print('FROZEN_INTERFACE_HASH', api_hash)
    print('AIDL_COMPILER_SHA256', hashlib.sha256(aidl.read_bytes()).hexdigest())
    print('CLANG', clang)
    parent = PROJECT / '.tmp'
    parent.mkdir(exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            out = Path(tmp)
            env = dict(os.environ, TMPDIR=tmp)
            command = [str(aidl), '--lang=ndk', '--structured', '--stability=vintf', '--version=2', '--hash=' + api_hash,
                       '--out=' + str(out / 'gen'), '--header_out=' + str(out / 'include'), '-I' + str(frozen),
                       *map(str, sorted(frozen.rglob('*.aidl')))]
            generated = subprocess.run(command, cwd=platform, env=env, capture_output=True, text=True, timeout=60)
            print('AIDL_GENERATE_EXIT', generated.returncode, generated.stdout, generated.stderr)
            if generated.returncode:
                return 1
            header = out / 'include/aidl/android/hardware/vibrator/BnVibrator.h'
            print('GENERATED_BNVIBRATOR_SHA256', hashlib.sha256(header.read_bytes()).hexdigest())
            resource = subprocess.check_output([str(clang), '--print-resource-dir'], env=env, text=True).strip()
            includes = [out / 'include', toolchain / 'include/c++/v1', Path(resource) / 'include',
                        platform / 'bionic/libc/include', platform / 'bionic/libc/kernel/uapi/asm-arm64',
                        platform / 'bionic/libc/kernel/uapi', platform / 'bionic/libc/kernel/android/uapi',
                        platform / 'bionic/libc/arch-arm64/include', platform / 'system/libbase/include',
                        platform / 'frameworks/native/libs/binder/ndk/include_cpp',
                        platform / 'frameworks/native/libs/binder/ndk/include_ndk',
                        platform / 'frameworks/native/libs/binder/ndk/include_platform', MTK / 'vibrator/include']
            flags = ['--target=aarch64-linux-android10000', '-std=c++17', '-fPIC', '-fno-exceptions', '-fno-rtti',
                     '-Wall', '-Wextra', '-Werror', '-nostdinc', '-D__ANDROID_VENDOR__', '-D__ANDROID_VNDK__']
            for path in includes:
                flags += ['-isystem', str(path)]
            print('OBJECT_FLAGS', ' '.join(flags))
            sources = [MTK / 'vibrator' / n for n in ['Controller.cpp', 'LedSwitch.cpp', 'OneShot.cpp']]
            sources += [BOARD / 'vibrator' / n for n in ['Vibrator.cpp', 'main.cpp']]
            for n, source in enumerate(sources):
                result = subprocess.run([str(clang), *flags, '-c', str(source), '-o', str(out / f'{n}.o')],
                                        cwd=platform, env=env, capture_output=True, text=True, timeout=60)
                print('ARM64_OBJECT', source.name, 'exit', result.returncode, result.stdout, result.stderr)
                if result.returncode:
                    return 1
                elf = (out / f'{n}.o').read_bytes()
                if elf[:6] != b'\x7fELF\x02\x01' or int.from_bytes(elf[16:18], 'little') != 1 or int.from_bytes(elf[18:20], 'little') != 183:
                    raise RuntimeError('Not a little-endian ELF64 AArch64 relocatable object')
                print('VERIFIED_ELF64_AARCH64_REL', source.name)
            print('ARM64_OBJECTS_COMPILED 5/5; NOT_SOONG NOT_LINKED NOT_RUNTIME_TESTED')
            return 0
    finally:
        try:
            parent.rmdir()
        except OSError:
            pass


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: PYTHONPATH=src python3 -B tests/android_adapter_probe.py /approved/platform')
    raise SystemExit(run(Path(sys.argv[1]).absolute()))
