import argparse
import glob
import os
import random
import shutil
import string
import sys
from subprocess import check_output, Popen, PIPE

import yaml

from utils import split_newline
from unzip import unzip

args = None

ADB_PATH = 'adb'


def adb(*a, split=True, print=False):
    global args
    command_line = [ADB_PATH]
    if 'device_serial' in args:
        command_line += ['-s', args.device_serial]

    if not print:
        output = check_output([*command_line, *a]).decode()

        return split_newline(output) if split else output

    process = Popen([*command_line, *a], stdout=PIPE, stderr=PIPE)
    for c in iter(lambda: process.stdout.read(1), b''):
        sys.stdout.buffer.write(c)


def pull_files(tmp):
    try:
        check_output([ADB_PATH, '--version'])
    except FileNotFoundError:
        print('Error: adb binary not found. Please add it to the path or modify the file location in config.yml')
        sys.exit(1)

    devices_output = check_output(['adb', 'devices']).decode()
    devices = [i[:i.index('\t')] for i in split_newline(devices_output) if '\t' in i]

    if not len(devices):
        print(
            'Error: no devices attached. Make sure your device is plugged in and has USB debugging enabled. Make sure '
            'to allow access if your device prompts for it.')
        sys.exit(1)

    if len(devices) > 1 and ('device_serial' not in args or args.device_serial not in devices):
        print(f'Error: more than one device connected (serials: {", ".join(devices)})')
        print(f'Please use -s SERIAL to specify a device (e.g. pull-files.py -s {devices[0]})')
        sys.exit(1)

    apk = None
    obb = None
    obb_filename = None
    asset_bundles = None

    for package in adb('shell', 'pm', 'list', 'packages', '-f'):
        if package.startswith('package:/data/app/com.rayark.cytus2'):
            apk = package[8:-18]
            print('Found apk at', apk)
            break
    else:
        print('Error: unable to locate apk file. Do you have Cytus 2 installed?')
        sys.exit(1)

    for file in adb('shell', 'ls', '-x', '-1', '/storage/emulated/0/Android/obb/com.rayark.cytus2'):
        if file.endswith('.obb'):
            obb = '/storage/emulated/0/Android/obb/com.rayark.cytus2/' + file
            obb_filename = file
            print('Found obb at', obb)
            break
    else:
        print('Error: unable to locate obb file. Do you have Cytus 2 installed?')
        sys.exit(1)

    if 'AssetBundles' in adb('shell', 'ls', '-x', '-1', '/storage/emulated/0/Android/data/com.rayark.cytus2/files'):
        asset_bundles = '/storage/emulated/0/Android/data/com.rayark.cytus2/files/AssetBundles'
        print('Found asset bundles at', asset_bundles)
    else:
        print('Unable to locate asset bundles. Black market song packs will not be pulled.')

    os.makedirs(f'./{tmp}', exist_ok=True)

    print('Pulling apk...')
    adb('pull', apk, f'./{tmp}/base.apk', print=True)

    print('Pulling asset bundles...')
    adb('pull', asset_bundles, f'./{tmp}/AssetBundles', print=True)

    print('Pulling obb...')
    adb('pull', obb, f'./{tmp}/{obb_filename}', print=True)

    return obb_filename, asset_bundles


def extract_files(input_dir, obb_filename, asset_bundles):
    unzip(f'./{input_dir}/base.apk', args.output_dir)
    unzip(f'./{input_dir}/{obb_filename}', args.output_dir)

    if asset_bundles:
        bundles = glob.glob(f'./{input_dir}/AssetBundles/*.ab/*.ab')
        for index, bundle in enumerate(bundles):
            actual_filename = os.path.basename(os.path.dirname(bundle))
            output = f'{args.output_dir}/assets/AssetBundles/{actual_filename}'
            print('Copying', bundle, 'to', output, f'({index + 1}/{len(bundles)})')
            shutil.copyfile(bundle, output)

    if not args.skip_cleanup and not args.extract_only:
        print('Cleaning up...')
        shutil.rmtree(f'./{input_dir}')

    print(f'Extracted files to {args.output_dir}. Use uTinyRipper to extract assets')


if __name__ == '__main__':
    with open('./config.yml', 'r', encoding='utf8') as f:
        ADB_PATH = yaml.load(f, yaml.Loader)['adb_path']

    parser = argparse.ArgumentParser(description='Pull and extract Cytus 2 apk and obb files from an android device')
    parser.add_argument('-s', '--serial', dest='device_serial', type=str, default=argparse.SUPPRESS,
                        help='Device serial to use if more than one device connected')
    parser.add_argument('-o', '--output-dir', dest='output_dir', type=str, default='data',
                        help='Directory to output extracted files to (default: data)')
    parser.add_argument('--skip-cleanup', dest='skip_cleanup', action='store_true',
                        help='Don\'t remove obb and apk files after running')
    parser.add_argument('--pull-only', dest='pull_only', action='store_true',
                        help='Skip extraction; pull apk, obb, and asset bundles from device only')
    parser.add_argument('--extract-only', dest='extract_only', action='store_true',
                        help='Skip pulling; extract data from assets only (requires --input-dir)')
    parser.add_argument('-i', '--input-dir', dest='input_dir', type=str, default=None,
                        help='Input directory if using --extract-only')

    args = parser.parse_args()

    if args.extract_only:
        if args.input_dir is None:
            print('Error: --extract-only used without --input-dir')
            sys.exit(1)

        try:
            next(glob.iglob(f'{args.input_dir}/base.apk'))
            extract_files(args.input_dir, os.path.basename(next(glob.iglob(f'{args.input_dir}/*.obb'))), True)
            sys.exit(0)
        except StopIteration:
            print("Error: obb or apk not found in input directory")
            sys.exit(1)

    tmp = args.output_dir if args.pull_only else 'tmp' + ''.join(random.choices(string.digits + string.ascii_letters, k=16))

    data = pull_files(tmp)

    if args.pull_only:
        sys.exit(0)

    extract_files(tmp, *data)
