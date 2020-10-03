import argparse
import concurrent.futures
import glob
import os
import random
import re
import shutil
import string
import sys
import zipfile
from subprocess import check_output, Popen, PIPE

args = None


def split_newline(string):
    return re.compile('\\r?\\n').split(string)


def adb(*a, split=True, print=False):
    global args
    command_line = ['adb']
    if 'device_serial' in args:
        command_line += ['-s', args.device_serial]

    if not print:
        output = check_output([*command_line, *a]).decode()

        return split_newline(output) if split else output

    process = Popen([*command_line, *a], stdout=PIPE, stderr=PIPE)
    for c in iter(lambda: process.stdout.read(1), b''):
        sys.stdout.buffer.write(c)


def unzip_member(zip_filepath, filename, dest, file_index, total_files):
    print('Extracting', filename, 'from', zip_filepath, 'to', dest, f'({file_index + 1}/{total_files})')
    with open(zip_filepath, 'rb') as f:
        try:
            zf = zipfile.ZipFile(f)
            zf.extract(filename, dest)
        except FileExistsError:
            print('Skipped extracting', filename, '(already exists)')


def unzip(zip_filepath, dest):
    print('Extracting', zip_filepath, 'to', dest)
    with open(zip_filepath, 'rb') as f:
        zf = zipfile.ZipFile(f)
        futures = []
        with concurrent.futures.ProcessPoolExecutor() as executor:
            infolist = zf.infolist()
            for index, member in enumerate(infolist):
                futures.append(
                    executor.submit(
                        unzip_member,
                        zip_filepath,
                        member.filename,
                        dest,
                        index,
                        len(infolist)
                    )
                )
            for future in concurrent.futures.as_completed(futures):
                exception = future.exception()
                if exception:
                    raise exception


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pull and extract Cytus 2 apk and obb files from an android device')
    parser.add_argument('-s', '--serial', dest='device_serial', type=str, default=argparse.SUPPRESS,
                        help='Device serial to use if more than one device connected')
    parser.add_argument('-o', '--output-dir', dest='output_dir', type=str, default='data',
                        help='Directory to output extracted files to (default: data)')
    parser.add_argument('--skip-cleanup', dest='skip_cleanup', action='store_true',
                        help='Don\'t remove obb and apk files after running')

    args = parser.parse_args()

    try:
        check_output(['adb', '--version'])
    except FileNotFoundError:
        print('Error: adb binary not found')
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

    tmp = 'tmp' + ''.join(random.choices(string.digits + string.ascii_letters, k=16))

    os.mkdir(f'./{tmp}')

    print('Pulling apk...')
    adb('pull', apk, f'./{tmp}/base.apk', print=True)

    print('Pulling asset bundles...')
    adb('pull', asset_bundles, f'./{tmp}/AssetBundles', print=True)

    print('Pulling obb...')
    adb('pull', obb, f'./{tmp}/{obb_filename}', print=True)

    unzip(f'./{tmp}/base.apk', args.output_dir)
    unzip(f'./{tmp}/{obb_filename}', args.output_dir)

    if asset_bundles:
        bundles = glob.glob(f'./{tmp}/AssetBundles/*.ab/*.ab')
        for index, bundle in enumerate(bundles):
            actual_filename = os.path.basename(os.path.dirname(bundle))
            output = f'{args.output_dir}/assets/AssetBundles/{actual_filename}'
            print('Copying', bundle, 'to', output, f'({index + 1}/{len(bundles)})')
            shutil.copyfile(bundle, output)

    if not args.skip_cleanup:
        print('Cleaning up...')
        shutil.rmtree(f'./{tmp}')

    print(f'Extracted files to {args.output_dir}. Use uTinyRipper to extract assets')
