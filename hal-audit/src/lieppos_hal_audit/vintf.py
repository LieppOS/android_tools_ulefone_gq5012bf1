"""VINTF declaration discovery only. No matrix merging or compatibility verdicts."""
import re
import xml.etree.ElementTree as ET


def parse_xml(text, path, diagnostic):
    if re.search(r'<!\s*(DOCTYPE|ENTITY)', text, re.I):
        diagnostic('XML_DTD_REJECTED', path, 1, 'DTD/entities prohibited')
        return [], []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        diagnostic('MALFORMED_XML', path, exc.position[0], str(exc))
        return [], []
    if root.tag not in {'manifest', 'compatibility-matrix'}:
        return [], []
    # Line locations are lexical anchors, ElementTree does not expose sourceline.
    anchors = list(re.finditer(r'<hal(?:\s|>)', re.sub(r'<!--[\s\S]*?-->', lambda m: re.sub(r'[^\n]', ' ', m[0]), text)))
    declarations, requirements = [], []
    for index, hal in enumerate(root.findall('hal')):
        line = text.count('\n', 0, anchors[index].start()) + 1 if index < len(anchors) else 1
        package = hal.findtext('name', '').strip()
        fmt = hal.get('format', 'hidl')
        if not package or fmt not in {'aidl', 'hidl', 'native'}:
            diagnostic('UNKNOWN_HAL_HEADER', path, line, 'Missing package or unsupported format')
            continue
        transport = hal.findtext('transport', '').strip() or ('binder' if fmt == 'aidl' else 'UNKNOWN')
        versions = [(v.text or '').strip() for v in hal.findall('version')]
        if not versions:
            versions = ['1'] if fmt == 'aidl' else ['UNKNOWN']
        valid = r'\d+' if fmt == 'aidl' else r'\d+\.\d+'
        if any(not re.fullmatch(valid, v) for v in versions) and not (fmt == 'hidl' and not hal.findall('version') and hal.findall('fqname')):
            diagnostic('UNKNOWN_VERSION', path, line, 'Version/range requires platform interpretation: ' + ','.join(versions))
            versions = [v if re.fullmatch(valid, v) else 'UNKNOWN' for v in versions]
        pairs = []
        for item in hal.findall('fqname'):
            fq = (item.text or '').strip()
            pattern = r'@(?P<ver>\d+\.\d+)::(?P<iface>[^/\s]+)/(?P<inst>[^\s]+)' if fmt == 'hidl' else r'(?P<iface>[^/\s]+)/(?P<inst>[^\s]+)'
            match = re.fullmatch(pattern, fq)
            if not match:
                diagnostic('UNKNOWN_FQNAME', path, line, 'Unparsed fqname: ' + fq)
                continue
            for ver in ([match['ver']] if fmt == 'hidl' else versions):
                pairs.append((ver, match['iface'], match['inst']))
        for iface in hal.findall('interface'):
            for instance in iface.findall('instance'):
                pairs.extend((v, iface.findtext('name', 'UNKNOWN').strip(), (instance.text or 'UNKNOWN').strip()) for v in versions)
            if iface.findall('regex-instance'):
                diagnostic('REGEX_INSTANCE', path, line, 'Regex requirement is not a concrete service instance')
        if not pairs:
            diagnostic('UNRESOLVED_HAL', path, line, 'No concrete interface/instance; may be disabling override or matrix range')
        for ver, iface, instance in sorted(set(pairs)):
            entry = dict(package=package, interface=package + '.' + iface, interface_short=iface,
                         version=ver, instance=instance, format=fmt, transport=transport,
                         vintf_source=path, line=line, override=hal.get('override') == 'true',
                         manifest_type=root.get('type', 'UNKNOWN'), target_level=root.get('target-level', 'UNKNOWN'),
                         version_origin='explicit' if hal.findall('version') or fmt == 'hidl' else 'aidl-default-1')
            (requirements if root.tag == 'compatibility-matrix' else declarations).append(entry)
    return declarations, requirements


def review_declarations(declarations):
    """Explain lexical overlap intent; NEVER simulate a libvintf partition merge."""
    from collections import defaultdict
    exact, identities = defaultdict(list), defaultdict(list)
    for d in declarations:
        exact[(d['interface'], d['instance'], d['format'], d['version'])].append(d)
        identities[(d['interface'], d['instance'])].append(d)
    overlaps, coexistence = [], []
    for contract, entries in sorted(exact.items()):
        if len(entries) < 2: continue
        classification = 'INTENTIONAL_OVERRIDE' if any(e['override'] for e in entries) and any(not e['override'] for e in entries) else 'DUPLICATE_DECLARATION_REVIEW'
        overlaps.append(dict(interface=contract[0], instance=contract[1], format=contract[2], version=contract[3],
            classification=classification,
            evidence=[dict(source=e['vintf_source'], line=e['line'], override=e['override']) for e in entries],
            validation='NEEDS_PLATFORM_VALIDATION',
            reason='Exact contract with explicit override attribute; declaration intent is not assembled-product validation' if classification == 'INTENTIONAL_OVERRIDE' else 'Product selection/merge order unavailable'))
    for identity, entries in sorted(identities.items()):
        if len({e['format'] for e in entries}) > 1:
            coexistence.append(dict(interface=identity[0], instance=identity[1],
                classification='DISTINCT_PROTOCOL_IDENTITIES_REVIEWED',
                evidence=[dict(source=e['vintf_source'], line=e['line'], format=e['format'], version=e['version']) for e in entries],
                reason='HIDL and AIDL contracts are not the same wire identity; text similarity alone proves no conflict',
                validation='NEEDS_PLATFORM_VALIDATION'))
    return dict(overlaps=overlaps, mixed_transport=coexistence,
                platform_validation='NOT_RUN', confirmed_platform_conflicts=None,
                scope='Source-level intent review; no framework/SKU/APEX/partition merge or compatibility PASS')
