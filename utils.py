import os
import magic
import re
import psutil
import signal

FILE_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif'
}


def file_type(path: str):
    filename, ext = os.path.splitext(path)

    if ext in FILE_TYPES:
        return FILE_TYPES[ext]

    return magic.Magic(mime=True).from_file(path)


DEPTHS = {'1': 1, 'L': 8, 'P': 8, 'RGB': 24, 'RGBA': 32, 'CMYK': 32, 'YCbCr': 24, 'I': 32, 'F': 32}


def mode_to_depth(mode: str):
    return DEPTHS[mode]


def split_newline(string):
    return re.compile('\\r?\\n').split(string)


def kill_child_processes(parent_pid, sig=signal.SIGTERM):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(sig)

    parent.send_signal(sig)


def special_file_filterer(special_file, file_base_name, base_dir_name):
    special_file_filename, special_file_dir_name = special_file
    invert = special_file_dir_name and special_file_dir_name[0] == '!'

    if file_base_name != special_file_filename:
        return False

    if special_file_dir_name and invert and base_dir_name == special_file_dir_name[1:]:
        return False

    if special_file_dir_name and not invert and base_dir_name != special_file_dir_name:
        return False

    return True


def find(iterable, predicate):
    for item in iterable:
        if predicate(item):
            return item


def parse_format(format: dict, local_dict: dict):
    return {
        key: re.sub(r'{(.+?)}', lambda m: str(eval(m.group(1), globals(), local_dict)), value)
        if type(value) == str else value
        for key, value in format.items()
    }
