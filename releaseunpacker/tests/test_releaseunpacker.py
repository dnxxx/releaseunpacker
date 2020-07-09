"""Test ReleaseUnpacker."""
import distutils.dir_util
import os
import shutil
import unittest
from tempfile import mkdtemp
from unittest import mock

from unipath import Path

from releaseunpacker.releaseunpacker import (
    ReleaseUnpacker,
    ReleaseUnpackerError,
    ReleaseUnpackerRarFile,
    ReleaseUnpackerRarFileError,
)

TEST_FILES = Path(os.path.dirname(os.path.abspath(__file__)), "files")


class ReleaseUnpackerTestCase:
    """ReleaseUnpacker test case base class."""

    def setUp(self):
        """Test setup."""
        self.search_dir = mkdtemp()
        self.tmp_dir = mkdtemp()
        self.unpack_dir = mkdtemp()

    def tearDown(self):
        """Test cleanup."""
        shutil.rmtree(self.search_dir)
        shutil.rmtree(self.tmp_dir)
        shutil.rmtree(self.unpack_dir)

    def copy_test_file_to_search_dir(self, file_name):
        """Copy test file to search dir."""
        return TEST_FILES.child(file_name).copy(
            Path(self.search_dir, file_name)
        )

    def copy_test_directory_to_search_dir(self, source):
        """Copy test directory to search dir."""
        return distutils.dir_util.copy_tree(
            Path(TEST_FILES, source), Path(self.search_dir, source)
        )

    def copy_test_file_to_tmp_dir(self, file_name):
        """Copy test file to tmp dir."""
        return TEST_FILES.child(file_name).copy(Path(self.tmp_dir, file_name))

    def copy_test_file_to_unpack_dir(self, file_name):
        """Copy test file to unpack dir."""
        return TEST_FILES.child(file_name).copy(
            Path(self.unpack_dir, file_name)
        )


class TestReleaseUnpacker(ReleaseUnpackerTestCase, unittest.TestCase):
    """ReleaseUnpacker test case."""

    LOGGER_NAME = "releaseunpacker.releaseunpacker"

    def test_repr(self):
        """Test object string representation."""
        release_unpacker = ReleaseUnpacker(
            self.search_dir, self.tmp_dir, self.unpack_dir
        )

        self.assertEqual(
            release_unpacker.__repr__(),
            "<ReleaseUnpacker: {} ({}) ({})>".format(
                self.search_dir, self.tmp_dir, self.unpack_dir
            ),
        )

    def test_release_search_dir_does_not_exist(self):
        """Test non existing search dir raises exception."""
        search_dir = Path("/non_existing_release_search_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(search_dir, self.tmp_dir, self.unpack_dir)

        self.assertEqual(
            str(cm.exception),
            "Release search dir {} doesn't exist".format(search_dir),
        )

    def test_release_search_dir_not_a_dir(self):
        """Test release search dir is not a directory raises exception."""
        self.copy_test_file_to_search_dir("file_not_a_dir")
        search_dir = Path(self.search_dir, "file_not_a_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(search_dir, self.tmp_dir, self.unpack_dir)

        self.assertEqual(
            str(cm.exception),
            "Release search dir {} is not a dir".format(search_dir),
        )

    def test_tmp_dir_does_not_exist(self):
        """Test non existing tmp dir raises exception."""
        tmp_dir = Path("/non_existing_tmp_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(self.search_dir, tmp_dir, self.unpack_dir)

        self.assertEqual(
            str(cm.exception), "Tmp dir {} doesn't exist".format(tmp_dir)
        )

    def test_tmp_dir_not_a_dir(self):
        """Test tmp dir is not a directory raises exception."""
        self.copy_test_file_to_tmp_dir("file_not_a_dir")
        tmp_dir = Path(self.tmp_dir, "file_not_a_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(self.search_dir, tmp_dir, self.unpack_dir)

        self.assertEqual(
            str(cm.exception), "Tmp dir {} is not a dir".format(tmp_dir)
        )

    def test_unpack_dir_does_not_exist(self):
        """Test non existing unpack dir raises exception."""
        unpack_dir = Path("/non_existing_unpack_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(self.search_dir, self.tmp_dir, unpack_dir)

        self.assertEqual(
            str(cm.exception), "Unpack dir {} doesn't exist".format(unpack_dir)
        )

    def test_unpack_dir_not_a_dir(self):
        """Test unpack dir is not a directory raises exception."""
        self.copy_test_file_to_unpack_dir("file_not_a_dir")
        unpack_dir = Path(self.unpack_dir, "file_not_a_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(self.search_dir, self.tmp_dir, unpack_dir)

        self.assertEqual(
            str(cm.exception), "Unpack dir {} is not a dir".format(unpack_dir)
        )

    def test_scan_rars_single_release(self):
        """Test scanning of RAR files for a single release."""
        self.copy_test_directory_to_search_dir("Release-Group")
        release_unpacker = ReleaseUnpacker(
            self.search_dir, self.tmp_dir, self.unpack_dir
        )

        self.assertEqual(
            release_unpacker.scan_rars(),
            [Path(self.search_dir, "Release-Group/rar_file.rar"),],
        )

    def test_scan_rars_multiple_releases(self):
        """Test scanning of RAR files with multiple releases in search dir."""
        for release in ("Release-Group", "Release.with.subs-Group"):
            self.copy_test_directory_to_search_dir(release)

        release_unpacker = ReleaseUnpacker(
            self.search_dir, self.tmp_dir, self.unpack_dir
        )

        self.assertEqual(
            release_unpacker.scan_rars(),
            [
                Path(self.search_dir, "Release-Group/rar_file.rar"),
                Path(
                    self.search_dir,
                    "Release.with.subs-Group/release.with.subs-group.rar",
                ),
                Path(
                    self.search_dir, "Release.with.subs-Group/Subs/subs.rar",
                ),
            ],
        )

    def test_unpack_release_dir_rars_no_rars_found(self):
        """Test unpack release dir without RAR files."""
        release_unpacker = ReleaseUnpacker(
            self.search_dir, self.tmp_dir, self.unpack_dir
        )

        self.assertFalse(release_unpacker.unpack_release_dir_rars())

    def test_unpack_releaseses(self):
        """Test unpack of releases."""
        for release in ("Release-Group", "Release.with.subs-Group"):
            self.copy_test_directory_to_search_dir(release)

        release_unpacker = ReleaseUnpacker(
            self.search_dir, self.tmp_dir, self.unpack_dir
        )
        release_unpacker.unpack_release_dir_rars()

        # Validate extract of releases and subs
        self.assertEqual(
            Path(self.unpack_dir).listdir(),
            [
                Path(self.unpack_dir, "Release-Group.mkv"),
                Path(self.unpack_dir, "Release.with.subs-Group.idx"),
                Path(self.unpack_dir, "Release.with.subs-Group.mkv"),
                Path(self.unpack_dir, "Release.with.subs-Group.sub"),
            ],
        )

        # Make sure the unpacked subs rar file is removed
        self.assertFalse(
            Path(
                self.search_dir,
                "Release.with.subs-Group/Subs/subs_inside_rar.rar",
            ).exists()
        )

        # Make sure the release dirs are removed
        self.assertFalse(Path(self.search_dir, "Release-Group").exists())
        self.assertFalse(
            Path(self.search_dir, "Release.with.subs-Group").exists()
        )

    def test_unpack_release_with_unpack_time(self):
        """Test unpack of releases with unpack time mocked for logging."""
        self.copy_test_directory_to_search_dir("Release-Group")

        release_unpacker = ReleaseUnpacker(
            self.search_dir, self.tmp_dir, self.unpack_dir
        )

        with self.assertLogs(self.LOGGER_NAME, level="INFO") as cm:
            # Mock ago.human() to set a static unpack time
            with mock.patch(
                "releaseunpacker.releaseunpacker.human", return_value="1 min"
            ):
                release_unpacker.unpack_release_dir_rars()

        self.assertIn(
            "INFO:releaseunpacker.releaseunpacker:Release-Group.mkv "
            "unpack done, 1 min",
            cm.output,
        )

    def test_unpack_release_with_no_removal(self):
        """Test unpack of release with no remove activated."""
        # Unpack releases in search dir without removal
        for release in ("Release-Group", "Release.with.subs-Group"):
            self.copy_test_directory_to_search_dir(release)

        release_unpacker = ReleaseUnpacker(
            self.search_dir, self.tmp_dir, self.unpack_dir, no_remove=True
        )
        release_unpacker.unpack_release_dir_rars()

        # Validate extract of releases and subs
        self.assertEqual(
            Path(self.unpack_dir).listdir(),
            [
                Path(self.unpack_dir, "Release-Group.mkv"),
                Path(self.unpack_dir, "Release.with.subs-Group.idx"),
                Path(self.unpack_dir, "Release.with.subs-Group.mkv"),
                Path(self.unpack_dir, "Release.with.subs-Group.sub"),
            ],
        )

        # Make sure the unpacked subs rar file is removed
        self.assertFalse(
            Path(
                self.search_dir,
                "Release.with.subs-Group/Subs/subs_inside_rar.rar",
            ).exists()
        )

        # Make sure the release dirs are not removed
        self.assertTrue(Path(self.search_dir, "Release-Group").exists())
        self.assertTrue(
            Path(self.search_dir, "Release.with.subs-Group").exists()
        )

    def test_unpack_release_with_already_existing_unpack(self):
        """Test unpack of release with an existing unpack already."""
        # Unpack releases in search dir without removal
        for release in ("Release-Group", "Release.with.subs-Group"):
            self.copy_test_directory_to_search_dir(release)

        release_unpacker = ReleaseUnpacker(
            self.search_dir, self.tmp_dir, self.unpack_dir, no_remove=True
        )
        release_unpacker.unpack_release_dir_rars()

        # Unpack releases in search dir second time with removal
        release_unpacker = ReleaseUnpacker(
            self.search_dir, self.tmp_dir, self.unpack_dir
        )
        release_unpacker.unpack_release_dir_rars()

        # Validate extract of releases and subs
        self.assertEqual(
            Path(self.unpack_dir).listdir(),
            [
                Path(self.unpack_dir, "Release-Group.mkv"),
                Path(self.unpack_dir, "Release.with.subs-Group.idx"),
                Path(self.unpack_dir, "Release.with.subs-Group.mkv"),
                Path(self.unpack_dir, "Release.with.subs-Group.sub"),
            ],
        )

        # Make sure the unpacked subs rar file is removed
        self.assertFalse(
            Path(
                self.search_dir,
                "Release.with.subs-Group/Subs/subs_inside_rar.rar",
            ).exists()
        )

        # Make sure the release dirs are removed
        self.assertFalse(Path(self.search_dir, "Release-Group").exists())
        self.assertFalse(
            Path(self.search_dir, "Release.with.subs-Group").exists()
        )


class TestReleaseUnpackerRarFile(ReleaseUnpackerTestCase, unittest.TestCase):
    """ReleaseUnpackerRarFile test case."""

    def test_repr(self):
        """Test object string representation."""
        self.copy_test_directory_to_search_dir("Release-Group")

        rar_file = ReleaseUnpackerRarFile(
            Path(self.search_dir, "Release-Group", "rar_file.rar")
        )
        self.assertEqual(
            rar_file.__repr__(),
            "<ReleaseUnpackerRarFile: {}>".format(
                Path(self.search_dir, "Release-Group", "rar_file.rar")
            ),
        )

    def test_invalid_rar_file(self):
        """Test invalid RAR file."""
        rar_file_path = "invalid_rar_file"

        with self.assertRaises(ReleaseUnpackerRarFileError) as cm:
            ReleaseUnpackerRarFile(rar_file_path)

        self.assertEqual(
            str(cm.exception), "Invalid RAR file {}".format(rar_file_path)
        )

    def test_subs_dir(self):
        """Test RAR in Subs dir detected correctly."""
        for release in ("Release-Group", "Release.with.subs-Group"):
            self.copy_test_directory_to_search_dir(release)

        rar_file_path = Path(self.search_dir, "Release-Group", "rar_file.rar")
        rar_file = ReleaseUnpackerRarFile(rar_file_path)
        self.assertFalse(rar_file.subs_dir)

        rar_file_path = Path(
            self.search_dir, "Release.with.subs-Group", "Subs", "subs.rar"
        )
        rar_file = ReleaseUnpackerRarFile(rar_file_path)
        self.assertTrue(rar_file.subs_dir)
