"""ReleaseUnpacker."""
import logging
import os
from datetime import datetime

import rarfile
from ago import human
from lazy import lazy
from unipath import DIRS, FILES, Path

log = logging.getLogger(__name__)


class ReleaseUnpackerError(Exception):
    """ReleaseUnpacker unpack error."""

    pass


class ReleaseUnpackerRarFileError(Exception):
    """ReleaseUnpacker RAR file error."""

    pass


class ReleaseUnpacker(object):
    """ReleaseUnpacker."""

    def __init__(
        self, release_search_dir, tmp_dir, unpack_dir, no_remove=False
    ):
        """Initialize and validate ReleaseUnpacker."""
        self.release_search_dir = Path(release_search_dir)
        self.release_search_dir_abs = self.release_search_dir.absolute()
        self.tmp_dir = Path(tmp_dir)
        self.unpack_dir = Path(unpack_dir)
        self.no_remove = no_remove

        if not self.release_search_dir_abs.exists():
            raise ReleaseUnpackerError(
                "Release search dir {} doesn't exist".format(
                    self.release_search_dir
                )
            )
        elif not self.release_search_dir_abs.isdir():
            raise ReleaseUnpackerError(
                "Release search dir {} is not a dir".format(
                    self.release_search_dir
                )
            )
        elif not self.tmp_dir.exists():
            raise ReleaseUnpackerError(
                "Tmp dir {} doesn't exist".format(self.tmp_dir)
            )
        elif not self.tmp_dir.isdir():
            raise ReleaseUnpackerError(
                "Tmp dir {} is not a dir".format(self.tmp_dir)
            )
        elif not self.unpack_dir.exists():
            raise ReleaseUnpackerError(
                "Unpack dir {} doesn't exist".format(self.unpack_dir)
            )
        elif not self.unpack_dir.isdir():
            raise ReleaseUnpackerError(
                "Unpack dir {} is not a dir".format(self.unpack_dir)
            )

    def __repr__(self):
        """Return object string representation."""
        return "<ReleaseUnpacker: {} ({}) ({})>".format(
            self.release_search_dir_abs, self.tmp_dir, self.unpack_dir
        )

    def file_exists_size_match(self, unpack_file_path, size_in_rar):
        """Return True if unpack_file_path exists already and size matches."""
        if (
            unpack_file_path.exists()
            and unpack_file_path.size() == size_in_rar
        ):
            log.info("%s already exists and size match", unpack_file_path)
            return True
        else:
            return False

    def unpack_release_dir_rars(self):
        """Run unpacker.

        Unpack all whitelisted file extensions found in RAR files.
        """
        # Scan for RAR files
        self.rar_files = self.scan_rars()
        if not self.rar_files:
            log.debug("No RARs found in %s", self.release_search_dir_abs)
            return False

        # Process the RAR files in any were found
        for rar_file_path in self.rar_files:
            log.debug("Found RAR file %s", rar_file_path)

            release_unpacker_rar_file = ReleaseUnpackerRarFile(rar_file_path)
            if release_unpacker_rar_file.subs_dir:
                self.unpack_subs_rar(release_unpacker_rar_file)
            else:
                self.unpack_rar(release_unpacker_rar_file)

        # Remove release dirs when unpack is done
        self.remove_release_dirs()

        return self

    def scan_rars(self):
        """Scan release_search_dir for .rar files.

        Find all sub folders and return a list of the first .rar file in
        each folder if any is found.
        """
        scan_dirs = [
            dir for dir in self.release_search_dir_abs.walk(filter=DIRS)
        ]
        scan_dirs.append(self.release_search_dir_abs)

        rar_files = []
        for dir in scan_dirs:
            rar_files_found = dir.listdir(pattern="*.rar", filter=FILES)
            if rar_files_found:
                rar_files.append(rar_files_found[0])

        return rar_files

    def remove_release_dirs(self):
        """Remove all release dirs from rar_files list."""
        for rar_file_path in self.rar_files:
            release_dir = rar_file_path.parent
            if release_dir.exists():
                if self.no_remove:
                    log.info("No remove active, not removing %s", release_dir)
                else:
                    log.info("Unpack complete, removing %s", release_dir)
                    release_dir.rmtree()

    def unpack_subs_rar(self, release_unpacker_rar_file):
        """Unpack a RAR in a Subs folder."""
        log.debug(
            "Processing subs RAR file %s",
            release_unpacker_rar_file.rar_file_path_abs,
        )

        for rarfile_file in release_unpacker_rar_file.file_list:
            # File in RAR is not a RAR file, extract
            if rarfile_file["name"].ext != ".rar":
                unpack_filename = "{}{}".format(
                    release_unpacker_rar_file.name, rarfile_file["name"].ext
                )
                unpack_file_path_abs = Path(self.unpack_dir, unpack_filename)

                # File exists and size match
                if self.file_exists_size_match(
                    unpack_file_path_abs, rarfile_file["size"]
                ):
                    continue

                self.unpack_move_rar_file(
                    release_unpacker_rar_file,
                    rarfile_file["name"],
                    unpack_file_path_abs,
                )
            # RAR file in RAR, extract to Subs folder and extract RAR
            else:
                log.debug(
                    "RAR file %s in %s",
                    rarfile_file["name"],
                    release_unpacker_rar_file.rar_file_path_abs,
                )

                # Extract the RAR to Subs folder
                subs_dir = release_unpacker_rar_file.rar_file_path_abs.parent
                log.debug(
                    "Extracting %s to %s", rarfile_file["name"], subs_dir
                )

                extracted_file_path = release_unpacker_rar_file.extract_file(
                    rarfile_file["name"], subs_dir
                )

                # Extract the extracted Subs RAR file
                self.unpack_subs_rar(
                    ReleaseUnpackerRarFile(extracted_file_path)
                )

                # Remove RAR file in Subs folder
                log.debug(
                    "Removing extracted Subs RAR %s", extracted_file_path
                )
                extracted_file_path.remove()

    def unpack_rar(self, release_unpacker_rar_file):
        """Unpack RAR files. Only process whitelisted file extensions."""
        for rarfile_file in release_unpacker_rar_file.file_list:
            # Check file extension
            if rarfile_file["name"].ext not in (
                ".avi",
                ".mkv",
                ".img",
                ".iso",
                ".mp4",
            ):
                log.info("Skipping %s, unwanted ext", rarfile_file["name"])
                continue

            unpack_filename = "{}{}".format(
                release_unpacker_rar_file.name, rarfile_file["name"].ext
            )
            unpack_file_path_abs = Path(self.unpack_dir, unpack_filename)

            # File exists and size match
            if self.file_exists_size_match(
                unpack_file_path_abs, rarfile_file["size"]
            ):
                continue

            # Unpack file in RAR
            self.unpack_move_rar_file(
                release_unpacker_rar_file,
                rarfile_file["name"],
                unpack_file_path_abs,
            )

        return True

    def unpack_move_rar_file(
        self, release_unpacker_rar_file, rarfile_file_name, unpack_file_path
    ):
        """Unpack and move RAR file.

        Extract an individual file from release_unpacker_rar_file to
        unpack_file_path.
        """
        # Extract file to tmp_dir
        log.debug("Extracting %s to %s", rarfile_file_name, self.tmp_dir)

        log.info("%s unpack started", unpack_file_path.name)
        unpack_start = datetime.now().replace(microsecond=0)

        extracted_file_path = release_unpacker_rar_file.extract_file(
            rarfile_file_name, self.tmp_dir
        )

        unpack_end = datetime.now().replace(microsecond=0)
        unpack_time = human(unpack_end - unpack_start, past_tense="{}")

        if not unpack_time:
            log.info("%s unpack done", unpack_file_path.name)
        else:
            log.info("%s unpack done, %s", unpack_file_path.name, unpack_time)

        # Move file and rename to unpack_dir
        log.debug("Moving %s to %s", extracted_file_path, unpack_file_path)

        extracted_file_path.move(unpack_file_path)


class ReleaseUnpackerRarFile(object):
    """Release unpacker RAR file."""

    def __init__(self, rar_file_path):
        """Initialize and validate rar file path."""
        self.rar_file_path = Path(rar_file_path)

        if (
            not self.rar_file_path.exists()
            or not self.rar_file_path.isfile()
            or not self.rar_file_path.ext == ".rar"
        ):
            raise ReleaseUnpackerRarFileError(
                "Invalid RAR file {}".format(self.rar_file_path)
            )

        self.rar_file_path_abs = self.rar_file_path.absolute()
        self.rar_file = rarfile.RarFile(self.rar_file_path)

    def __repr__(self):
        """Return object string representation."""
        return "<ReleaseUnpackerRarFile: {}>".format(self.rar_file_path_abs)

    @lazy
    def name(self):
        """Return name of release folder."""
        if self.subs_dir:
            name = self.rar_file_path.parent.parent.name
        else:
            name = self.rar_file_path.parent.name

        return str(name)

    @lazy
    def subs_dir(self):
        """Return True if RAR file is located in a Subs folder."""
        if self.rar_file_path.parent.name.lower() in ("subs", "sub"):
            return True
        else:
            return False

    @lazy
    def file_list(self):
        """Return file list of RAR file."""
        files = []
        for file in self.rar_file.infolist():
            files.append({"name": Path(file.filename), "size": file.file_size})

        return files

    def extract_file(self, file_name, unpack_dir):
        """Extract file_name and return extracted file path."""
        self.rar_file.extract(file_name, path=unpack_dir)
        self.extracted_file_path = Path(unpack_dir, file_name)

        # Set the mtime to current time
        self.set_mtime()

        return self.extracted_file_path

    def set_mtime(self):
        """Set mtime of extracted file path to current time."""
        os.utime(self.extracted_file_path, None)
