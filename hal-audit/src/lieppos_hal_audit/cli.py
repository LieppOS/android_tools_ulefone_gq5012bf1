"""CLI; reads supplied roots, writes reports only to a disjoint output directory."""
import argparse
import json
import sys
from .device import apply_device_coverage, attach_runtime, runtime_properties
from .inventory import audit
from .report import export
from .safety import safe_output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', action='append', required=True, help='Approved text source root; repeat for multiple roots; no symlinks followed')
    parser.add_argument('--output', help='Disjoint report directory; omit for summary-only dry run')
    parser.add_argument('--gq5012bf1', action='store_true', help='Add evidence-gated subsystem coverage (unknown contracts remain unknown)')
    parser.add_argument('--runtime-properties', help='Optional historical getprop file; only init.svc and Android version/boot keys retained')
    parser.add_argument('--fail-on-diagnostics', action='store_true', help='Exit 1 on review/error diagnostics (default exit 0 means scan finished, NOT compatibility PASS)')
    args = parser.parse_args(argv)
    try:
        output = safe_output(args.output, args.root) if args.output else None
        result = audit(args.root)
        if args.gq5012bf1: apply_device_coverage(result)
        if args.runtime_properties: attach_runtime(result, runtime_properties(args.runtime_properties))
        if output: export(result, output)
    except (OSError, ValueError) as exc:
        print('hal-audit: ' + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result['summary'], sort_keys=True))
    return 1 if args.fail_on_diagnostics and result['diagnostics'] else 0


if __name__ == '__main__':
    sys.exit(main())
