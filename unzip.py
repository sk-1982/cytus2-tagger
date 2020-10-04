import zipfile
import concurrent.futures


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
