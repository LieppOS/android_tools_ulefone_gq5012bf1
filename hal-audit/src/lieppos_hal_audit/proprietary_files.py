"""Extraction-list metadata only. No blob reads, extraction or executable analysis."""
import re


def parse_proprietary(text, path, diagnostic):
    entries, comments = [], []
    for line, raw in enumerate(text.splitlines(), 1):
        raw = raw.strip()
        if not raw:
            comments = []
            continue
        if raw.startswith('#'):
            comments.append(raw[1:].strip())
            continue
        value = raw.split('#', 1)[0].strip()
        # extract-utils permits -module entries, src:dst, options and |hash pins.
        module = value.startswith('-')
        value = value.lstrip('-')
        value, _, pin = value.partition('|')
        fields = value.split(';')
        src, sep, dst = fields[0].partition(':')
        if not src or any(p == '..' for p in src.split('/')) or src.startswith('/'):
            diagnostic('MALFORMED_EXTRACTION_ENTRY', path, line, 'Invalid extraction path')
            comments = []
            continue
        opts = fields[1:]
        aliases = [o.split('=', 1)[1] for o in opts if o.startswith('SYMLINK=')]
        service = next((m[1] for c in comments if (m := re.search(r'stock init service\s+(\S+)', c))), 'UNKNOWN')
        dependencies = [m[1] for c in comments if (m := re.search(r'DT_NEEDED by\s+(\S+)', c))]
        entries.append(dict(path=dst if sep else src, extraction_source=src, source=path, line=line,
                            options=opts, aliases=aliases, extract_only='EXTRACT_ONLY' in opts,
                            module=module, hash_pin=pin, init_reference=service,
                            dependency_of=dependencies, comments=comments))
        comments = []
    return entries
