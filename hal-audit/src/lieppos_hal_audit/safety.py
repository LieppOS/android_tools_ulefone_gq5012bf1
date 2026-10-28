"""No-follow, bounded text-only input; never opens binaries or secret material."""
import hashlib
import os
import re
import stat
from pathlib import Path

FORBIDDEN = '/home/armol/androido_dalykai'
SKIP_DIRS = {'.git', '.repo', '__pycache__', 'node_modules', 'out', 'prebuilt',
             'firmware', 'nvram', 'calibration', 'keys', 'private', '.venv', 'kernel', 'androido_dalykai'}
TEXT_SUFFIXES = {'.xml', '.rc', '.bp', '.mk', '.te', '.cpp', '.cc', '.c', '.h',
                 '.java', '.aidl', '.hal', '.md', '.csv', '.patch', '.sh'}
TEXT_NAMES = {'LICENSE', 'proprietary-files.txt', 'file_contexts', 'genfs_contexts',
              'service_contexts', 'hwservice_contexts', 'property_contexts',
              'hals.conf', 'recovery.fstab'}
SENSITIVE = re.compile(r'(private.?key|calibrat|(^|[._-])(secret|nvram|keybox)([._-]|$))', re.I)
MAX_BYTES = 2 * 1024 * 1024


def checked_path(path):
    # Check raw components before normalization, and never resolve symlinks.
    raw = os.fspath(path)
    if raw.startswith(FORBIDDEN) or 'androido_dalykai' in Path(raw).parts:
        raise ValueError('forbidden input path')
    return Path(os.path.abspath(raw))


def open_directory(path):
    path = checked_path(path)
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            nxt = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        return fd
    except BaseException:
        os.close(fd)
        raise


def allowed(name):
    return not SENSITIVE.search(name) and (Path(name).suffix in TEXT_SUFFIXES or name in TEXT_NAMES)


def scan_text(root, diagnostic):
    root = checked_path(root)
    try:
        fd = open_directory(root)
    except (OSError, ValueError) as exc:
        diagnostic('ROOT_UNAVAILABLE', str(root), 1, str(exc))
        return
    def descend(directory_fd, relative):
        try:
            names = sorted(os.listdir(directory_fd))
        except OSError as exc:
            diagnostic('READ_ERROR', str(root / relative), 1, str(exc))
            return
        if len(relative.parts) > 64:
            diagnostic('DEPTH_LIMIT', str(root / relative), 1, 'Directory depth exceeds 64')
            return
        for name in names:
            rel = relative / name
            path = str(root / rel)
            if name in SKIP_DIRS or SENSITIVE.search(name):
                continue
            try:
                st = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if stat.S_ISLNK(st.st_mode):
                    diagnostic('SYMLINK_SKIPPED', path, 1, 'Symlinks are never followed')
                elif stat.S_ISDIR(st.st_mode):
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
                    try:
                        yield from descend(child, rel)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(st.st_mode) and allowed(name):
                    child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
                    with os.fdopen(child, 'rb') as stream:
                        before = os.fstat(stream.fileno())
                        if not stat.S_ISREG(before.st_mode):
                            continue
                        data = stream.read(MAX_BYTES + 1)
                        after = os.fstat(stream.fileno())
                    if len(data) > MAX_BYTES:
                        diagnostic('FILE_TOO_LARGE', path, 1, 'Text exceeds 2 MiB cap')
                        continue
                    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                        diagnostic('INPUT_CHANGED', path, 1, 'Changed during read; omitted')
                        continue
                    if b'\0' in data:
                        diagnostic('BINARY_SKIPPED', path, 1, 'NUL in text candidate')
                        continue
                    try:
                        text = data.decode('utf-8')
                    except UnicodeError:
                        diagnostic('ENCODING_UNKNOWN', path, 1, 'Not UTF-8; omitted')
                        continue
                    yield path, text, hashlib.sha256(data).hexdigest()
            except OSError as exc:
                diagnostic('READ_ERROR', path, 1, str(exc))
    try:
        yield from descend(fd, Path())
    finally:
        os.close(fd)


def safe_output(path, roots):
    path = checked_path(path)
    for root in roots:
        root = checked_path(root)
        if path == root or root in path.parents or path in root.parents:
            raise ValueError('output and input roots must be disjoint')
    # Walk from / using directory fds: even existence checks must not follow links.
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for name in path.parts[1:]:
            try:
                nxt = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except FileNotFoundError:
                os.mkdir(name, dir_fd=fd)
                nxt = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
    finally:
        os.close(fd)
    return path


def write_output(directory, name, text):
    # Refuse symlinked output files, too. Caller supplies fixed basenames.
    fd = open_directory(directory)
    try:
        out = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o644, dir_fd=fd)
        with os.fdopen(out, 'w', encoding='utf-8', newline='') as stream:
            st = os.fstat(stream.fileno())
            if st.st_nlink != 1 or not stat.S_ISREG(st.st_mode):
                raise ValueError('output must be a single-link regular file')
            stream.truncate(0)
            stream.write(text)
    finally:
        os.close(fd)
