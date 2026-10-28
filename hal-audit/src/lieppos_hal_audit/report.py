"""Deterministic serialization and internal report-shape checks, not JSON Schema."""
import csv
import io
import json
from .inventory import COLUMNS
from .safety import write_output


def validate_report(result):
    if result.get('schema_version') != 1:
        raise ValueError('unsupported schema_version')
    for field in ['inventory', 'declarations', 'diagnostics', 'provenance', 'roots', 'modules', 'init_services']:
        if not isinstance(result.get(field), list): raise ValueError('expected list: ' + field)
    for row in result['inventory']:
        if any(not isinstance(row.get(column), str) for column in COLUMNS):
            raise ValueError('inventory must contain all string CSV fields')
        for prop in ['DECLARED', 'IMPLEMENTED_IN_SOURCE', 'PROPRIETARY_IMPLEMENTATION', 'SERVICE_PRESENT', 'SERVICE_STARTED', 'HARDWARE_VERIFIED', 'MISSING', 'UNKNOWN']:
            if row.get('properties', {}).get(prop) not in (True, False, None): raise ValueError('invalid evidence property')
            if prop not in row['properties']: raise ValueError('missing evidence property')
    for item in result['provenance']:
        if len(item.get('sha256', '')) != 64: raise ValueError('invalid provenance digest')
    return True


def csv_text(result):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    writer.writerows(result['inventory'])
    return stream.getvalue()


def markdown(result):
    counts = result['summary']
    out = ['# HAL/VINTF static scan', '', '> Not a Soong build, libvintf check, SELinux compile, or hardware test.', '',
           '## Totals', '', *[f'- {k}: {v}' for k,v in counts.items() if k != 'diagnostic_counts'], '',
           '## Input scope', '', *[f"- `{r['path']}`: {r['text_files']} eligible text files" for r in result['roots']], '',
           '## Diagnostics', '', '| Code | Count |', '|---|---:|',
           *[f'| {k} | {v} |' for k,v in counts['diagnostic_counts'].items()], '',
           'All missing diagnostics mean **not resolved in supplied roots**, not proven absent from a running device.',
           'OVERRIDE_OVERLAP is an ODM/vendor merge review, not a confirmed duplicate error.', '', '## Contracts', '',
           '| Subsystem | Interface | Version | Instance | Implementation |', '|---|---|---|---|---|']
    def escape(value): return value.replace('|', '\\|').replace('\n', ' ')
    out += ['| ' + ' | '.join(escape(row[x]) for x in ['subsystem', 'interface', 'version', 'instance', 'implementation_status']) + ' |' for row in result['inventory']]
    out += ['', 'See HAL-INVENTORY.json for file hashes, line diagnostics, init/module/extraction relationships and uncertainty.']
    return '\n'.join(out) + '\n'


def export(result, output):
    validate_report(result)
    write_output(output, 'HAL-INVENTORY.json', json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + '\n')
    write_output(output, 'HAL-INVENTORY.csv', csv_text(result))
    write_output(output, 'SCAN-SUMMARY.md', markdown(result))
