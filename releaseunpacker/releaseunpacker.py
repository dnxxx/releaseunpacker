from datetime import datetime
import logging
import os

from unipath import Path, DIRS, FILES
from lazy import lazy
import rarfile
from ago import human

log = logging.getLogger(__name__)


class ReleaseUnpackerError(Exception):
    pass


class ReleaseUnpackerRarFileError(Exception):
    pass


class ReleaseUnpacker(object):
    def __init__(self, release_search_dir, tmp_dir, unpack_dir,
                 no_remove=False):
        self.release_search_dir = Path(release_search_dir)
        self.release_search_dir_abs = self.release_search_dir.absolute()
        self.tmp_dir = Path(tmp_dir)
        self.unpack_dir = Path(unpack_dir)
        self.no_remove = no_remove

        if not self.release_search_dir_abs.exists():
            raise ReleaseUnpackerError(
                'Release search dir {} doesn\'t exist'.format(
                    self.release_search_dir))
        elif not self.release_search_dir_abs.isdir():
            raise ReleaseUnpackerError(
                'Release search dir {} is not a dir'.format(
                    self.release_search_dir))
        elif not self.tmp_dir.exists():
            raise ReleaseUnpackerError(
                'Tmp dir {} doesn\'t exist'.format(self.tmp_dir))
        elif not self.tmp_dir.isdir():
            raise ReleaseUnpackerError(
                'Tmp dir {} is not a dir'.format(
                    self.tmp_dir))
        elif not self.unpack_dir.exists():
            raise ReleaseUnpackerError(
                'Unpack dir {} doesn\'t exist'.format(self.unpack_dir))
        elif not self.unpack_dir.isdir():
            raise ReleaseUnpackerError(
                'Unpack dir {} is not a dir'.format(
                    self.unpack_dir))

    def __repr__(self):
        return '<ReleaseUnpacker: {} ({}) ({})>'.format(
            self.release_search_dir_abs, self.tmp_dir, self.unpack_dir)

    def file_exists_size_match(self, unpack_file_path, size_in_rar):
        """Returns True if unpack_file_path exists and size is a match"""
        if (unpack_file_path.exists() and
           unpack_file_path.size() == size_in_rar):
            log.info('{} already exists and size match'.format(
                unpack_file_path))
            return True
        else:
            return False

    def scan_rars(self):
        """Find all folders in release_search_dir and return the first RAR
        file if one is found in a dir.
        """

        rar_files = []
        scan_dirs = [dir for dir in
                     self.release_search_dir_abs.walk(filter=DIRS)]
        scan_dirs.append(self.release_search_dir_abs)
        for dir in scan_dirs:
            rar_files_found = dir.listdir(pattern='*.rar', filter=FILES)
            if rar_files_found:
                rar_files.append(rar_files_found[0])

        return rar_files

    def unpack_release_dir_rars(self):
        """Run the unpacker. Find the first RAR file in dirs found in
        release_search_dir.
        """

        # Scan for RAR files
        self.rar_files = self.scan_rars()
        if not self.rar_files:
            log.debug('No RARs found in {}'.format(
                self.release_search_dir_abs))
            return False

        # Process the RAR files in any were found
        for rar_file_path in self.rar_files:
            log.debug('Found RAR file {}'.format(rar_file_path))

            release_unpacker_rar_file = ReleaseUnpackerRarFile(rar_file_path)
            if release_unpacker_rar_file.subs_dir:
                self.unpack_subs_rar(release_unpacker_rar_file)
            else:
                self.unpack_rar(release_unpacker_rar_file)

        # Remove release dirs when unpack is done
        self.remove_release_dirs()

        return self

    def remove_release_dirs(self):
        """Remove all release dirs from rar_files list"""

        for rar_file_path in self.rar_files:
            release_dir = rar_file_path.parent
            if release_dir.exists():
                if self.no_remove:
                    log.info('No remove active, not removing {}'.format(
                        release_dir))
                else:
                    log.info(
                        'Unpack complete, removing {}'.format(release_dir))
                    release_dir.rmtree()

    def unpack_subs_rar(self, release_unpacker_rar_file):
        """Unpack a RAR in a Subs folder"""

        log.debug('Processing subs RAR file {}'.format(
            release_unpacker_rar_file.rar_file_path_abs))

        for rarfile_file in release_unpacker_rar_file.file_list:
            # File in RAR is not a RAR file, extract
            if rarfile_file['name'].ext != '.rar':
                unpack_filename = '{}{}'.format(release_unpacker_rar_file.name,
                                                rarfile_file['name'].ext)
                unpack_file_path_abs = Path(self.unpack_dir, unpack_filename)

                # File exists and size match
                if self.file_exists_size_match(unpack_file_path_abs,
                                               rarfile_file['size']):
                    continue

                self.unpack_move_rar_file(release_unpacker_rar_file,
                                          rarfile_file['name'],
                                          unpack_file_path_abs)
            # RAR file in RAR, extract to Subs folder and extract RAR
            else:
                log.debug('RAR file {} in {}'.format(
                    rarfile_file['name'],
                    release_unpacker_rar_file.rar_file_path_abs))

                # Extract the RAR to Subs folder
                subs_dir = release_unpacker_rar_file.rar_file_path_abs.parent
                log.debug('Extracting {} to {}'.format(rarfile_file['name'],
                                                       subs_dir))

                extracted_file_path = release_unpacker_rar_file.extract_file(
                    rarfile_file['name'], subs_dir)

                # Extract the extracted Subs RAR file
                self.unpack_subs_rar(ReleaseUnpackerRarFile(
                    extracted_file_path))

                # Remove RAR file in Subs folder
                log.debug('Removing extracted Subs RAR {}'.format(
                    extracted_file_path))
                extracted_file_path.remove()

    def unpack_rar(self, release_unpacker_rar_file):
        """List all files in a RAR and determine if it should be extracted
        or not.
        """

        for rarfile_file in release_unpacker_rar_file.file_list:
            # Check file ext
            if rarfile_file['name'].ext not in ('.avi', '.mkv',
                                                '.img', '.iso'):
                log.info('Skipping {}, unwanted ext'.format(
                    rarfile_file['name']))
                continue

            unpack_filename = '{}{}'.format(release_unpacker_rar_file.name,
                                            rarfile_file['name'].ext)
            unpack_file_path_abs = Path(self.unpack_dir, unpack_filename)

            # File exists and size match
            if self.file_exists_size_match(unpack_file_path_abs,
                                           rarfile_file['size']):
                continue

            # Unpack file in RAR
            self.unpack_move_rar_file(release_unpacker_rar_file,
                                      rarfile_file['name'],
                                      unpack_file_path_abs)

        return True

    def unpack_move_rar_file(self, release_unpacker_rar_file,
                             rarfile_file_name, unpack_file_path):
        """Extract an individual file from release_unpacker_rar_file to
        unpack_file_path
        """

        # Extract file to tmp_dir
        log.debug('Extracting {} to {}'.format(rarfile_file_name,
                                               self.tmp_dir))

        log.info('{} unpack started'.format(unpack_file_path.name))
        unpack_start = datetime.now().replace(microsecond=0)

        extracted_file_path = release_unpacker_rar_file.extract_file(
            rarfile_file_name, self.tmp_dir)

        unpack_end = datetime.now().replace(microsecond=0)
        unpack_time = human(unpack_end - unpack_start, past_tense='{}')

        if not unpack_time:
            log.info('{} unpack done'.format(unpack_file_path.name))
        else:
            log.info('{} unpack done, {}'.format(unpack_file_path.name,
                                                 unpack_time))

        # Move file and rename to unpack_dir
        log.debug('Moving {} to {}'.format(extracted_file_path,
                                           unpack_file_path))

        extracted_file_path.move(unpack_file_path)


class ReleaseUnpackerRarFile(object):
    def __init__(self, rar_file_path):
        self.rar_file_path = Path(rar_file_path)

        if (not self.rar_file_path.exists() or not self.rar_file_path.isfile()
           or not self.rar_file_path.ext == '.rar'):
                raise ReleaseUnpackerRarFileError('Invalid RAR file {}'.format(
                    self. rar_file_path))

        self.rar_file_path_abs = self.rar_file_path.absolute()
        self.rar_file = rarfile.RarFile(self.rar_file_path)

    def __repr__(self):
        return '<ReleaseUnpackerRarFile: {}>'.format(self.rar_file_path_abs)

    @lazy
    def name(self):
        if self.subs_dir:
            name = self.rar_file_path.parent.parent.name
        else:
            name = self.rar_file_path.parent.name

        return str(name)

    @lazy
    def subs_dir(self):
        if self.rar_file_path.parent.name.lower() in ('subs', 'sub'):
            return True
        else:
            return False

    @lazy
    def file_list(self):
        files = []
        for file in self.rar_file.infolist():
            files.append({'name': Path(file.filename), 'size': file.file_size})

        return files

    def set_mtime(self):
        with file(self.extracted_file_path, 'a'):
            os.utime(self.extracted_file_path, None)

    def extract_file(self, file_name, unpack_dir):
        self.rar_file.extract(file_name, path=unpack_dir)
        self.extracted_file_path = Path(unpack_dir, file_name)

        # Set the mtime to current time
        self.set_mtime()

        return self.extracted_file_path
