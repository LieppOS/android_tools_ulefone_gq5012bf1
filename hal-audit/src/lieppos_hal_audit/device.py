"""Optional GQ5012BF1 coverage lens. Never invent unavailable fragment contracts."""
import hashlib
import os
import re
from pathlib import Path
from .inventory import COLUMNS, summarize, subsystem
from .safety import checked_path, open_directory, MAX_BYTES, SENSITIVE

# Literal filenames from the authorized integration tree. Absence stays UNKNOWN.
COVERAGE = {
    'Audio': ['android.hardware.audio.service.mediatek'],
    'Camera': ['camerahalserver'],
    'Thermal camera': ['M170infisens'],
    'Graphics composer': ['android.hardware.graphics.composer@3.2-service'],
    'Graphics allocator': ['android.hardware.graphics.allocator-V2-service-mediatek.mt6878'],
    'Radio / telephony': ['mtkfusionrild'],
    'GNSS': ['android.hardware.gnss-service.mediatek'],
    'Wi-Fi': ['android.hardware.wifi-service-lazy', 'hostapd', 'wpa_supplicant'],
    'Bluetooth': ['android.hardware.bluetooth-service-mediatek', 'android.hardware.bluetooth@1.1-service-mediatek'],
    'NFC': ['android.hardware.nfc-service-st'],
    'Fingerprint': ['android.hardware.biometrics.fingerprint-service.example'],
    'Sensors': ['android.hardware.sensors-service.multihal', 'android.hardware.contexthub-service.tinysys'],
    'Lights': ['android.hardware.lights-service.mediatek'],
    'Vibrator/haptics': ['android.hardware.vibrator-service.mediatek'],
    'Power': ['vendor.mediatek.hardware.mtkpower-service.mediatek'],
    'Health': ['android.hardware.health-service.example'],
    'USB': ['android.hardware.usb-aidl-service.mediatekv1.0', 'android.hardware.usb.gadget-aidl-service.mediatekv1.0'],
    'Thermal management': ['android.hardware.thermal-service.mediatek', 'thermal_core'],
    'Security': ['android.hardware.security.keymint@3.0-service.trustkernel', 'android.hardware.gatekeeper-service.trustkernel'],
    'DRM': ['android.hardware.drm-service.clearkey'],
    'Boot control': ['android.hardware.boot-service.mtk'],
    'Battery and charging': ['fuelgauged', 'vendor.lineage.health-service.default'],
    'Auxiliary display': ['vendor.yft.hardware.tinylcd@1.0-service', 'tinydisplay_touch_daemon', 'TinyScreenService'],
    'Ulefone-specific hardware': ['vendor.yft.hardware.changenode@1.0-service', 'vendor.yft.hardware.gesturewake@1.0-service'],
}


def artifact_record(category, b):
    record = {column: 'UNKNOWN' for column in COLUMNS}
    record.update(subsystem=category, executable=b['path'], init_service=b['init_reference'],
        proprietary_dependency=b['path'], implementation_status='UNKNOWN' if b['extract_only'] else 'PROPRIETARY_IMPLEMENTATION',
        validation_status='NEEDS_PLATFORM_VALIDATION', evidence=f"{b['source']}:{b['line']}",
        notes='Extraction reference only; init name (if known) comes from a comment, not parsed rc. Fragment contents unavailable; interface/version/instance not inferred from filename.'
              + (' EXTRACT_ONLY: not an install rule; source replacement intended but not proven.' if b['extract_only'] else ''),
        properties=dict(DECLARED=None, IMPLEMENTED_IN_SOURCE=False, PROPRIETARY_IMPLEMENTATION=None if b['extract_only'] else True,
                        SERVICE_PRESENT=None, SERVICE_STARTED=None, HARDWARE_VERIFIED=None, MISSING=None, UNKNOWN=True),
        proprietary_reference=True, source_availability='PROPRIETARY_REFERENCE_NO_SOURCE_IN_SCAN',
        classification_basis='extraction metadata, not on-disk binary presence or verified interface binding',
        init_reference=b['init_reference'], declarations=[], init_definitions=[], modules=[],
        binary_candidates=[b], selinux=[], permissions=[], kernel_dependencies=[], runtime_evidence=[], registration='UNKNOWN')
    return record


def apply_device_coverage(result):
    coverage = []
    mapped_artifacts = {b['path'] for r in result['inventory'] for b in r['binary_candidates']}
    for category, filenames in COVERAGE.items():
        bs = [b for b in result['proprietary_entries'] if Path(b['path']).name in filenames]
        ms = [m for m in result['modules'] if m['name'] in filenames or m['stem'] in filenames]
        rows = [r for r in result['inventory'] if r['subsystem'] == category]
        coverage.append(dict(subsystem=category, declaration_contracts=len(rows),
                             extraction_references=[f"{b['source']}:{b['line']}" for b in bs],
                             build_references=[f"{m['source']}:{m['line']}" for m in ms],
                             required_by_device='CONFIGURATION_EVIDENCED' if rows or bs or ms else 'UNKNOWN',
                             mandatory_android17='UNKNOWN; depends on shipping FCM, framework matrix and exposed features'))
        # A category match does not prove a process serves that category's declared contract.
        for b in bs:
            if b['path'] not in mapped_artifacts:
                result['inventory'].append(artifact_record(category, b))
                mapped_artifacts.add(b['path'])
        if not rows and not bs and ms:
            for m in ms:
                row = artifact_record(category, dict(path='UNKNOWN', source=m['source'], line=m['line'], extract_only=True, init_reference='UNKNOWN'))
                row.update(executable='UNKNOWN', proprietary_dependency='UNKNOWN', modules=[m], binary_candidates=[],
                    source_path=m['source'], source_repository=next((p['root'] for p in result['provenance'] if p['path'] == m['source']), 'UNKNOWN'), proprietary_reference=False,
                    classification_basis='build module reference, not native HAL implementation source',
                    source_availability='CLIENT_SOURCE_ONLY' if m['source_status'] == 'IMPLEMENTED_IN_SOURCE' else 'PREBUILT_APP_REFERENCE',
                    notes='App/helper build reference only, not a HAL server; native interface/version/instance UNKNOWN.')
                result['inventory'].append(row)
    # Include ancillary hardware processes even if not in the minimum subsystem checklist.
    for b in result['proprietary_entries']:
        if '/bin/hw/' in b['path'] and b['path'] not in mapped_artifacts:
            result['inventory'].append(artifact_record(subsystem(b['path']), b))
            mapped_artifacts.add(b['path'])
    # Source-built auxiliary consumers are not server HAL implementations.
    server_modules = {(m['source'], m['name']) for r in result['inventory'] for m in r['modules']}
    result['source_helpers'] = [m for m in result['modules'] if m['source_status'] == 'IMPLEMENTED_IN_SOURCE' and m['kind'] in {'cc_binary', 'android_app', 'sh_binary'} and (m['source'], m['name']) not in server_modules]
    for row in result['inventory']:
        row.setdefault('proprietary_reference', bool(row['binary_candidates']))
        row.setdefault('source_availability', 'SOURCE_IMPLEMENTATION' if row['properties']['IMPLEMENTED_IN_SOURCE'] else
                       'PROPRIETARY_CANDIDATE' if row['binary_candidates'] else 'UNKNOWN')
        # Exact recorded ABI references; not an audit of kernel drivers.
        deps = list(row['kernel_dependencies'])
        for ref in result['references']:
            if row['subsystem'] in {'Health', 'Battery and charging'} and (
                    (ref['source'].endswith('/lieppos/lieppos.mk') and '/sys/class/power_supply/mtk-master-charger/input_current_limit' in ref['text']) or
                    (ref['source'].endswith('/gq5012bf1/sepolicy/vendor/genfs_contexts') and 'genfscon sysfs' in ref['text'])):
                deps.append(dict(interface=ref['text'], source=ref['source'], line=ref['line'], evidence_kind='configuration/policy reference; hardware untested'))
            if row['subsystem'] == 'Security' and any(s in row['interface'] + row['executable'] for s in ['keymint', 'gatekeeper']) and ref['source'].endswith('/gq5012bf1/sepolicy/vendor/trustkernel.te') and any(s in ref['text'] for s in ['hal_keymint_default tkcore_', 'hal_gatekeeper_default tkcore_']):
                deps.append(dict(interface=ref['text'], source=ref['source'], line=ref['line'], evidence_kind='policy reference; live node unknown'))
        for ref in result['kernel_path_references']:
            if (row['subsystem'] in {'Lights', 'Ulefone-specific hardware'} and '/sys/devices/platform/yft_camplight/' in ref['text']) or (row['subsystem'] in {'Auxiliary display', 'Ulefone-specific hardware'} and '/apps/TinyDisplay/daemon/' in ref['source']):
                deps.append(dict(interface=ref['text'], source=ref['source'], line=ref['line'], evidence_kind='consumer/patch ABI reference only; not verified HAL server dependency'))
        row['kernel_dependencies'] = deps
        row['kernel_dependency'] = '; '.join(d.get('interface', d.get('text', 'UNKNOWN')) + ' [' + d['source'] + ':' + str(d.get('line', 1)) + ']' for d in deps) or 'UNKNOWN'
        row['permissions'] = [dict(path=b['path'], source=b['source'], line=b['line'], relation='subsystem feature reference, not required permission proof')
            for b in result['proprietary_entries'] if '/etc/permissions/' in b['path'] and subsystem(b['path']) == row['subsystem']]
        if row['subsystem'] == 'Thermal camera':
            row['permissions'] += [dict(ref, relation='app permission configuration only') for ref in result['permission_references'] if '/energy_tc2c/' in ref['source']]
        binaries = {p for b in row['binary_candidates'] for p in [b['path'], *b['aliases']]}
        row['runtime_dependency_references'] = [dict(path=b['path'], source=b['source'], line=b['line'], consumers=b['dependency_of'])
            for b in result['proprietary_entries'] if binaries.intersection(b['dependency_of'])]
        if row['runtime_dependency_references']:
            row['proprietary_dependency'] += '; ' + '; '.join(b['path'] for b in row['runtime_dependency_references'])
        if any(m['name'] == 'android.hardware.vibrator-service.gq5012bf1' and m['source_status'] == 'IMPLEMENTED_IN_SOURCE' for m in row['modules']):
            # Old blob filename matches are not dependencies of the new source.
            row['stock_runtime_dependency_references'] = row['runtime_dependency_references']
            row['runtime_dependency_references'] = []
            row['proprietary_dependency'] = 'NONE_IN_SELECTED_HAL_USERSPACE_SOURCE; kernel/regulator hardware boundary remains'
            implementation_modules = row['modules'] + [m for m in result['modules'] if m['name'] == 'libmtk_regulator_vibrator']
            implementation_files = sorted({p for m in implementation_modules for p in m['source_files']})
            row['source_path'] = '; '.join(implementation_files)
            row['source_coverage'] = dict(origin='INDEPENDENT', license='Apache-2.0 (module license metadata)',
                implementation_files=implementation_files,
                canonical_repository='LieppOS/android_hardware_ulefone_gq5012bf1',
                backend_repository='LieppOS/android_hardware_mediatek_mt6878',
                classification='SOURCE_AVAILABLE_HAL_CODE_NOT_WHOLE_STACK',
                build_dependencies=['android.hardware.vibrator-V2-ndk', 'libbinder_ndk', 'libbase', 'libmtk_regulator_vibrator'],
                kernel_timeout_dependency=('Driver-owned timeout ABI v1; effective module, supply and physical cutoff unverified' if any(p.endswith('/vibrator/DriverTimed.cpp') for p in implementation_files) else 'Linux LED oneshot protocol in source; effective config, lifetime and physical cutoff unverified' if any(p.endswith('/vibrator/OneShot.cpp') for p in implementation_files) else 'UNKNOWN'),
                remaining='Target Soong/linking, kernel expiry/lifetime and duration policy, actual sysfs access, stock Manager contract and hardware validation; activation not applied')
            row['validation_properties'] = dict(SOURCE_IMPLEMENTED=True, UNIT_TESTED=None, SOONG_BUILD_PASSED=None,
                VINTF_VALIDATED=None, PLATFORM_INTEGRATED=None, HARDWARE_VERIFIED=None)
            row['notes'] += ' Source candidate, not activated. Static scan cannot certify tests/builds or kernel expiry. See source safety gate and research test receipts. Old stock binary candidates are not source dependencies.'
    result['coverage'] = coverage
    result['inventory'].sort(key=lambda r: (r['subsystem'], r['interface'], r['version'], r['instance'], r['executable']))
    summarize(result)


def runtime_properties(path):
    path = checked_path(path)
    if path.suffix != '.txt' or not any(s in path.name for s in ['getprop', 'properties']) or any(SENSITIVE.search(p) for p in path.parts):
        raise ValueError('runtime input must be a non-sensitive getprop/properties .txt file')
    fd = open_directory(path.parent)
    try:
        file_fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    finally:
        os.close(fd)
    import stat
    with os.fdopen(file_fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode): raise ValueError('runtime evidence must be regular text file')
        data = stream.read(MAX_BYTES + 1)
        after = os.fstat(stream.fileno())
    if len(data) > MAX_BYTES or b'\0' in data: raise ValueError('runtime evidence oversized/binary')
    if (before.st_mtime_ns, before.st_size) != (after.st_mtime_ns, after.st_size): raise ValueError('runtime evidence changed')
    selected = []
    for n, line in enumerate(data.decode('utf-8').splitlines(), 1):
        match = re.fullmatch(r'\[([^\]]+)\]: \[([^\]]*)\]', line)
        if match and (match[1].startswith('init.svc.') or match[1] in {
                'sys.boot_completed', 'ro.build.version.release', 'ro.build.version.sdk', 'ro.lineage.version'}):
            selected.append(dict(property=match[1], value=match[2], line=n))
    return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(),
                scope='historical exact image set only; init state is not service registration/hardware verification', selected_properties=selected)


def attach_runtime(result, evidence):
    result['runtime_snapshot'] = evidence
    states = {p['property'].removeprefix('init.svc.'): p for p in evidence['selected_properties'] if p['property'].startswith('init.svc.')}
    for row in result['inventory']:
        # Only exact parsed init relationships or explicitly documented extraction comments.
        names = [s['name'] for s in row['init_definitions']]
        if row.get('init_reference', 'UNKNOWN') != 'UNKNOWN': names.append(row['init_reference'])
        for b in row['binary_candidates']:
            if b['init_reference'] != 'UNKNOWN': names.append(b['init_reference'])
        for name in sorted(set(names)):
            if name not in states: continue
            p = states[name]
            row['runtime_evidence'].append(dict(service=name, state=p['value'], source=evidence['path'], line=p['line'],
                 relation='parsed init' if name in [s['name'] for s in row['init_definitions']] else 'extraction comment/binary candidate; interface binding unverified'))
        # Do not promote a filename candidate to confirmed service presence for a declared interface.
        if not row['declarations'] and row['runtime_evidence']:
            row['properties']['SERVICE_STARTED'] = any(p['state'] == 'running' for p in row['runtime_evidence'])
            row['notes'] += ' Historical init state applies to referenced process only.'
    summarize(result)
