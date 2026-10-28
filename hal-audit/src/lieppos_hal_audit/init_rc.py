"""Parse service stanzas without interpreting actions, imports or commands."""
import re
import shlex


def parse_init(text, path, diagnostic):
    services, current = [], None
    # Continuations preserve the first physical line for diagnostics.
    lines, pending, start = [], '', 1
    for number, raw in enumerate(text.splitlines(), 1):
        if not pending:
            start = number
        pending += raw.rstrip().removesuffix('\\') if raw.rstrip().endswith('\\') else raw
        if raw.rstrip().endswith('\\'):
            pending += ' '
            continue
        lines.append((start, pending))
        pending = ''
    if pending:
        diagnostic('INIT_CONTINUATION', path, start, 'Unterminated continuation')
    for number, raw in lines:
        try:
            parts = shlex.split(raw, comments=True)
        except ValueError as exc:
            diagnostic('MALFORMED_INIT', path, number, str(exc))
            continue
        if not parts:
            continue
        if not raw[0].isspace():
            current = None
            if parts[0] == 'service':
                if len(parts) < 3:
                    diagnostic('MALFORMED_INIT', path, number, 'Service lacks executable')
                    continue
                current = dict(name=parts[1], executable=parts[2], args=parts[3:], source=path,
                               line=number, interfaces=[], seclabel='UNKNOWN', user='UNKNOWN', groups=[], disabled=False)
                services.append(current)
            elif parts[0] == 'import':
                diagnostic('INIT_IMPORT_UNRESOLVED', path, number, 'Import recorded only; scanned roots determine scope')
        elif current is not None:
            if parts[0] == 'interface':
                if len(parts) == 3 and parts[1] == 'aidl' and '/' in parts[2]:
                    iface, instance = parts[2].split('/', 1)
                    current['interfaces'].append(dict(interface=iface, instance=instance, format='aidl', version='UNKNOWN'))
                elif len(parts) >= 3 and re.fullmatch(r'[^@]+@\d+\.\d+::[^:]+', parts[1]):
                    package, version, iface = re.fullmatch(r'([^@]+)@(\d+\.\d+)::(.+)', parts[1]).groups()
                    for instance in parts[2:]:
                        current['interfaces'].append(dict(interface=package + '.' + iface, instance=instance, format='hidl', version=version))
                else:
                    diagnostic('UNKNOWN_INIT_INTERFACE', path, number, 'Unparsed interface option')
            elif parts[0] == 'seclabel' and len(parts) == 2:
                current['seclabel'] = parts[1]
            elif parts[0] == 'user' and len(parts) == 2:
                current['user'] = parts[1]
            elif parts[0] == 'group':
                current['groups'] = parts[1:]
            elif parts[0] == 'disabled':
                current['disabled'] = True
    return services
