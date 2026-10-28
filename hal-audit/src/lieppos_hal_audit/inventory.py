"""Conservative joins: exact init interfaces or literal Soong fragment relationships."""
import fnmatch
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from .android_bp import parse_bp
from .init_rc import parse_init
from .proprietary_files import parse_proprietary
from .safety import scan_text, checked_path
from .vintf import parse_xml

COLUMNS = ['subsystem', 'interface', 'version', 'instance', 'transport', 'vintf_source',
           'init_service', 'executable', 'source_repository', 'source_path', 'implementation_status',
           'proprietary_dependency', 'kernel_dependency', 'validation_status', 'evidence', 'notes']


def subsystem(value):
    value = value.lower()
    for needle, category in [('tinylcd', 'Auxiliary display'), ('tinyscreen', 'Auxiliary display'),
            ('tinydisplay', 'Auxiliary display'), ('energy_tc2c', 'Thermal camera'),
            ('keymint', 'Security'), ('gatekeeper', 'Security'), ('secureclock', 'Security'),
            ('sharedsecret', 'Security'), ('secure_element', 'Security'), ('drm', 'DRM'),
            ('fingerprint', 'Fingerprint'), ('biometrics.face', 'Face biometrics'),
            ('camera', 'Camera'), ('composer', 'Graphics composer'), ('allocator', 'Graphics allocator'),
            ('mapper', 'Graphics mapper'), ('radio', 'Radio / telephony'), ('fusionrild', 'Radio / telephony'),
            ('gnss', 'GNSS'), ('agps', 'GNSS'), ('wifi', 'Wi-Fi'), ('supplicant', 'Wi-Fi'), ('hostapd', 'Wi-Fi'),
            ('bluetooth', 'Bluetooth'), ('audio', 'Audio'), ('soundtrigger', 'Audio'), ('nfc', 'NFC'),
            ('sensor', 'Sensors'), ('contexthub', 'Sensors'), ('lights', 'Lights'),
            ('vibrator', 'Vibrator/haptics'), ('mtkpower', 'Power'), ('power-service', 'Power'),
            ('health', 'Health'), ('fuelgauged', 'Battery and charging'), ('usb', 'USB'),
            ('thermal', 'Thermal management'), ('boot-service', 'Boot control'), ('bootctrl', 'Boot control'),
            ('changenode', 'Ulefone-specific hardware'), ('gesturewake', 'Ulefone-specific hardware'),
            ('obtainvendor', 'Ulefone-specific hardware')]:
        if needle in value: return category
    return 'Other vendor/platform interfaces'


def key(entry):
    return (entry['interface'], entry['instance'], entry['format'], entry['version'])


def matches(entry, interface):
    return (entry['interface'] == interface['interface'] and entry['instance'] == interface['instance']
            and entry['format'] == interface['format']
            and (interface['version'] == 'UNKNOWN' or entry['version'] == interface['version']))


def binary_matches(package, basename):
    # A filename is only a candidate, never proof of service registration.
    suffix = basename.removeprefix(package)
    return basename.startswith(package) and bool(re.match(r'(?:@\d|[-.]service)', suffix))


def audit(roots):
    diagnostics = []
    def diag(code, path, line, message):
        diagnostics.append(dict(code=code, path=path, line=line, message=message,
                                severity='ERROR' if code.startswith(('MALFORMED', 'XML_DTD', 'READ_ERROR')) else 'REVIEW'))
    roots = sorted(set(str(checked_path(r)) for r in roots))
    files, declarations, requirements, services, modules, blobs = {}, [], [], [], [], []
    root_stats = []
    for root in roots:
        count = 0
        for path, text, digest in scan_text(root, diag):
            count += 1
            if path in files: continue
            files[path] = dict(text=text, sha256=digest, root=root)
        root_stats.append(dict(path=root, text_files=count))
    for path, item in sorted(files.items()):
        text = item['text']
        if path.endswith('.xml'):
            ds, rs = parse_xml(text, path, diag)
            declarations.extend(ds); requirements.extend(rs)
        elif path.endswith('.rc'): services.extend(parse_init(text, path, diag))
        elif Path(path).name == 'Android.bp': modules.extend(parse_bp(text, path, diag))
        elif Path(path).name == 'proprietary-files.txt': blobs.extend(parse_proprietary(text, path, diag))
    # Attach resolved in-scope literal sources; glob matches operate on already-safe reads.
    for module in modules:
        parent = Path(module['source']).parent
        source_patterns = module['properties'].get('srcs', []) + (module['properties'].get('src', []) if module['kind'] == 'sh_binary' else [])
        module['source_files'] = sorted(p for p in files if any(fnmatch.fnmatch(p, os.path.normpath(str(parent / pat))) for pat in source_patterns))
        module['unresolved_source_patterns'] = [pat for pat in source_patterns if not any(fnmatch.fnmatch(p, os.path.normpath(str(parent / pat))) for p in files)]
        if module['unresolved_source_patterns']:
            diag('SOURCE_REFERENCE_UNRESOLVED', module['source'], module['line'], ', '.join(module['unresolved_source_patterns']) + '; missing, filtered, generated or out of scope')
        module['source_status'] = ('IMPLEMENTED_IN_SOURCE' if module['source_files'] and not module['unresolved_source_patterns'] and not set(module['unresolved_properties']) & {'name', 'srcs', 'src', 'stem'} and module['kind'] in {'cc_binary', 'cc_library_shared', 'cc_library', 'cc_library_static', 'android_app', 'sh_binary'}
                                   else 'PREBUILT_REFERENCE' if module['kind'].startswith(('cc_prebuilt_', 'android_app_import')) else
                                   'CONFIGURATION_REFERENCE' if module['kind'] == 'prebuilt_etc' else 'UNKNOWN')
        module['registration_references'] = [dict(source=p, line=n, text=line.strip(), kind='lexical source reference only')
            for p in module['source_files'] for n,line in enumerate(files[p]['text'].splitlines(), 1)
            if any(token in line for token in ['AServiceManager_addService', 'AServiceManager_registerLazyService', 'registerAsService('])]
        module['kernel_references'] = [dict(source=p, line=n, text=line.strip(), kind='lexical kernel ABI reference only')
            for p in module['source_files'] for n,line in enumerate(files[p]['text'].splitlines(), 1)
            if '/dev/' in line or '/sys/' in line]
    groups = defaultdict(list)
    for d in declarations: groups[key(d)].append(d)
    for entries in groups.values():
        if len(entries) > 1:
            override = any(d['override'] for d in entries)
            code = 'OVERRIDE_OVERLAP' if override else 'DUPLICATE_HAL'
            diag(code, entries[-1]['vintf_source'], entries[-1]['line'],
                 entries[0]['interface'] + '/' + entries[0]['instance'] + ('; ordering/partition merge needs libvintf' if override else '; product selection unknown'))
    transports = defaultdict(list)
    for d in declarations: transports[(d['interface'], d['instance'])].append(d)
    for entries in transports.values():
        if len({d['format'] for d in entries}) > 1:
            diag('POTENTIAL_AIDL_HIDL_CONFLICT', entries[-1]['vintf_source'], entries[-1]['line'], entries[0]['interface'] + '/' + entries[0]['instance'] + '; coexistence may be intentional')
        for fmt in {'aidl', 'hidl'}:
            same = [d for d in entries if d['format'] == fmt]
            if len({d['version'] for d in same}) > 1:
                diag('MULTIPLE_HAL_VERSIONS', same[-1]['vintf_source'], same[-1]['line'], 'Inheritance/coexistence requires platform validation')
    inventory = []
    for identity, entries in sorted(groups.items()):
        d = entries[0]
        linked_modules = [m for m in modules if 'vintf_fragments' not in m['unresolved_properties'] and any(os.path.normpath(str(Path(m['source']).parent / frag)) == e['vintf_source'] for frag in m['properties'].get('vintf_fragments', []) for e in entries)]
        linked_services = [s for s in services if any(matches(d, i) for i in s['interfaces']) or any(os.path.normpath(str(Path(m['source']).parent / rc)) == s['source'] for m in linked_modules for rc in m['properties'].get('init_rc', []))]
        candidates = [b for b in blobs if '/bin/' in b['path'] and binary_matches(d['package'], Path(b['path']).name)]
        # Filename candidates do not establish an interface<->process relationship.
        source_modules = [m for m in linked_modules if m['source_status'] == 'IMPLEMENTED_IN_SOURCE']
        policy = []
        for s in linked_services:
            for path, item in files.items():
                if Path(path).name == 'file_contexts':
                    for n, line in enumerate(item['text'].splitlines(), 1):
                        parts = line.split()
                        if len(parts) >= 2 and not line.lstrip().startswith('#'):
                            # Only literal context paths; do not execute arbitrary regexes.
                            if parts[0].replace(r'\.', '.') == s['executable']:
                                policy.append(dict(source=path, line=n, context=parts[-1]))
        props = dict(DECLARED=True, IMPLEMENTED_IN_SOURCE=bool(source_modules),
                     PROPRIETARY_IMPLEMENTATION=None, SERVICE_PRESENT=None, SERVICE_STARTED=None,
                     HARDWARE_VERIFIED=None, MISSING=None, UNKNOWN=not bool(source_modules))
        issues = []
        if not source_modules and not candidates:
            diag('MISSING_IMPLEMENTATION_IN_SCAN', d['vintf_source'], d['line'], d['interface'] + '/' + d['instance'] + ': no exact source link or binary candidate; not proof absent on device')
            issues.append('IMPLEMENTATION_UNKNOWN')
        if d['transport'] != 'passthrough' and not linked_services:
            diag('MISSING_INIT_IN_SCAN', d['vintf_source'], d['line'], d['interface'] + '/' + d['instance'] + ': no exact init relationship; lazy/shared services possible')
            issues.append('INIT_RELATIONSHIP_UNKNOWN')
        ev = [f"{e['vintf_source']}:{e['line']}" for e in entries]
        ev += [f"{b['source']}:{b['line']} (binary candidate only)" for b in candidates]
        record = {c: 'UNKNOWN' for c in COLUMNS}
        record.update(subsystem=subsystem(d['package']), interface=d['interface'], version=d['version'],
                      instance=d['instance'], transport=d['transport'], vintf_source='; '.join(sorted({e['vintf_source'] for e in entries})),
                      init_service='; '.join(s['name'] for s in linked_services) or 'UNKNOWN',
                      executable='; '.join(s['executable'] for s in linked_services) or 'UNKNOWN',
                      source_repository='; '.join(sorted({files[m['source']]['root'] for m in source_modules})) or 'UNKNOWN',
                      source_path='; '.join(m['source'] for m in source_modules) or 'UNKNOWN',
                      implementation_status='IMPLEMENTED_IN_SOURCE' if source_modules else 'UNKNOWN',
                      proprietary_dependency='; '.join(b['path'] for b in candidates) or 'UNKNOWN',
                      kernel_dependency='; '.join(f"{k['source']}:{k['line']} {k['text']}" for m in source_modules for k in m['kernel_references']) or 'UNKNOWN',
                      validation_status='NEEDS_PLATFORM_VALIDATION', evidence='; '.join(ev),
                      notes='; '.join(issues + ['Declaration is not operation evidence. Binary filenames are not exact registration links.']),
                      properties=props, proprietary_reference=bool(candidates),
                      source_availability='SOURCE_IMPLEMENTATION' if source_modules else 'PROPRIETARY_CANDIDATE' if candidates else 'UNKNOWN',
                      declarations=entries, init_definitions=linked_services,
                      modules=linked_modules, binary_candidates=candidates, selinux=policy,
                      permissions=[], kernel_dependencies=[k for m in source_modules for k in m['kernel_references']],
                      runtime_evidence=[], registration='SOURCE_REFERENCE_NOT_RUNTIME' if any(m['registration_references'] for m in source_modules) else 'UNKNOWN')
        inventory.append(record)
    for s in services:
        for i in s['interfaces']:
            if not any(matches(d, i) for d in declarations):
                diag('MISSING_VINTF_IN_SCAN', s['source'], s['line'], str(i) + '; only explicit init HAL registrations checked; manifest could be elsewhere')
        m = [m for m in modules if m['stem'] == Path(s['executable']).name and m['source_status'] == 'IMPLEMENTED_IN_SOURCE']
        b = [b for b in blobs if s['executable'].lstrip('/') in [b['path'], *b['aliases']]]
        if not m and not b:
            diag('MISSING_EXECUTABLE_REFERENCE', s['source'], s['line'], s['executable'] + '; no source module/extraction reference in scan')
    # Generic SELinux and permissions references stay unjoined unless exact evidence exists.
    references, permissions, kernel_paths = [], [], []
    for path, item in sorted(files.items()):
        for n, line in enumerate(item['text'].splitlines(), 1):
            if ('/sys/' in line or '/dev/' in line) and not line.startswith(('--- ', '+++ ')) and '/dev/null' not in line:
                kernel_paths.append(dict(source=path, line=n, text=line.strip(), kind='patch reference, application unverified' if path.endswith('.patch') else 'source/config reference; hardware untested'))
        if path.endswith('.xml') and any(token in path for token in ['permission', 'AndroidManifest']):
            for n, line in enumerate(item['text'].splitlines(), 1):
                if any(token in line for token in ['<permission', '<uses-permission', '<feature']):
                    permissions.append(dict(source=path, line=n, text=line.strip(), kind='configuration reference; not capability proof'))
        for n, line in enumerate(item['text'].splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(('#', '//')): continue
            kind = ('selinux' if Path(path).suffix == '.te' or Path(path).name.endswith('contexts') else
                    'build' if Path(path).suffix in {'.mk', '.bp'} else None)
            if kind and any(t in stripped for t in ['hal_', 'SEPOLICY', 'service', 'sysfs', 'sys/class', 'PRODUCT_PACKAGES', 'vintf', 'permission']):
                references.append(dict(kind=kind, source=path, line=n, text=stripped))
    diagnostics.sort(key=lambda x: (x['path'], x['line'], x['code'], x['message']))
    result = dict(schema_version=1, scope='static source evidence; not Android compatibility certification',
                  roots=root_stats, inventory=inventory, declarations=declarations, matrix_requirements=requirements,
                  init_services=services, modules=modules, proprietary_entries=blobs,
                  references=references, permission_references=permissions, kernel_path_references=kernel_paths, diagnostics=diagnostics,
                  provenance=[dict(path=p, sha256=i['sha256'], root=i['root']) for p,i in sorted(files.items())])
    summarize(result)
    return result


def summarize(result):
    result['summary'] = dict(records=len(result['inventory']), declaration_records=len(result['declarations']),
        unique_declared_contracts=len({key(d) for d in result['declarations']}),
        source_implemented_records=sum(r['properties']['IMPLEMENTED_IN_SOURCE'] is True for r in result['inventory']),
        proprietary_reference_records=sum(r.get('proprietary_reference', False) for r in result['inventory']),
        proprietary_classified_artifact_records=sum(r['properties']['PROPRIETARY_IMPLEMENTATION'] is True for r in result['inventory']),
        unresolved_records=sum(r['implementation_status'] == 'UNKNOWN' for r in result['inventory']),
        source_helper_modules=len(result.get('source_helpers', [])),
        historical_started_process_records=sum(r['properties']['SERVICE_STARTED'] is True for r in result['inventory']),
        hardware_verified_records=sum(r['properties']['HARDWARE_VERIFIED'] is True for r in result['inventory']),
        diagnostic_counts=dict(sorted(Counter(d['code'] for d in result['diagnostics']).items())))
