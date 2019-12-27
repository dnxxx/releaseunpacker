"""Test ReleaseUnpacker."""
import distutils.dir_util
import os
import shutil
import unittest
from tempfile import mkdtemp

from unipath import Path

from releaseunpacker.releaseunpacker import (
    ReleaseUnpacker,
    ReleaseUnpackerError,
    ReleaseUnpackerRarFile,
    ReleaseUnpackerRarFileError,
)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class TestReleaseUnpacker(unittest.TestCase):
    """ReleaseUnpacker test case."""

    def setUp(self):
        """Test setup."""
        self.tmp_dir = mkdtemp()
        self.unpack_dir = mkdtemp()

    def tearDown(self):
        """Test cleanup."""
        shutil.rmtree(self.tmp_dir)
        shutil.rmtree(self.unpack_dir)

    def test_repr(self):
        """Test object string representation."""
        release_search_dir = Path(TEST_DIR, "files/")
        ru = ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)
        self.assertEqual(
            ru.__repr__(),
            "<ReleaseUnpacker: {} ({}) ({})>".format(
                release_search_dir.absolute(), self.tmp_dir, self.unpack_dir
            ),
        )

    def test_release_search_dir_does_not_exist(self):
        """Test non existing search dir raises exception."""
        release_search_dir = Path("/non_existing_release_search_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)

        self.assertEqual(
            str(cm.exception),
            "Release search dir {} doesn't exist".format(release_search_dir),
        )

    def test_release_search_dir_not_a_dir(self):
        """Test release search dir is not a directory raises exception."""
        release_search_dir = Path(TEST_DIR, "files/file_not_a_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)

        self.assertEqual(
            str(cm.exception),
            "Release search dir {} is not a dir".format(release_search_dir),
        )

    def test_tmp_dir_does_not_exist(self):
        """Test non existing tmp dir raises exception."""
        release_search_dir = Path(TEST_DIR, "files/")
        tmp_dir = Path("/non_existing_tmp_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(release_search_dir, tmp_dir, self.unpack_dir)

        self.assertEqual(
            str(cm.exception), "Tmp dir {} doesn't exist".format(tmp_dir)
        )

    def test_tmp_dir_not_a_dir(self):
        """Test tmp dir is not a directory raises exception."""
        release_search_dir = Path(TEST_DIR, "files/")
        tmp_dir = Path(TEST_DIR, "files/file_not_a_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(release_search_dir, tmp_dir, self.unpack_dir)

        self.assertEqual(
            str(cm.exception), "Tmp dir {} is not a dir".format(tmp_dir)
        )

    def test_unpack_dir_does_not_exist(self):
        """Test non existing unpack dir raises exception."""
        release_search_dir = Path(TEST_DIR, "files/")
        unpack_dir = Path("/non_existing_unpack_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(release_search_dir, self.tmp_dir, unpack_dir)

        self.assertEqual(
            str(cm.exception), "Unpack dir {} doesn't exist".format(unpack_dir)
        )

    def test_unpack_dir_not_a_dir(self):
        """Test unpack dir is not a directory raises exception."""
        release_search_dir = Path(TEST_DIR, "files/")
        unpack_dir = Path(TEST_DIR, "files/file_not_a_dir")

        with self.assertRaises(ReleaseUnpackerError) as cm:
            ReleaseUnpacker(release_search_dir, self.tmp_dir, unpack_dir)

        self.assertEqual(
            str(cm.exception), "Unpack dir {} is not a dir".format(unpack_dir)
        )

    def test_scan_rars(self):
        """Test scanning of RAR files."""
        release_search_dir = Path(TEST_DIR, "files/")
        ru = ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)
        self.assertEqual(
            ru.scan_rars(),
            [
                Path(TEST_DIR, "files/Release-Group/rar_file.rar"),
                Path(
                    TEST_DIR,
                    (
                        "files/Release.with.subs-Group/"
                        "release.with.subs-group.rar"
                    ),
                ),
                Path(
                    TEST_DIR,
                    ("files/Release.with.subs-Group/Subs" "/subs.rar"),
                ),
            ],
        )

        release_search_dir = Path(TEST_DIR, "files/Release-Group")
        ru = ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)
        self.assertEqual(
            ru.scan_rars(),
            [Path(TEST_DIR, "files/Release-Group/rar_file.rar")],
        )

    def test_unpack_release_dir_rars_no_rars_found(self):
        """Test unpack release dir without RAR files."""
        tmp_release_search_dir = Path(TEST_DIR, "tmp")
        tmp_release_search_dir.mkdir()

        ru = ReleaseUnpacker(
            tmp_release_search_dir, self.tmp_dir, self.unpack_dir
        )

        self.assertFalse(ru.unpack_release_dir_rars())

        # Remove tmp_release_dir
        shutil.rmtree(tmp_release_search_dir)

    def test_unpack_release_dir_rars(self):
        """Test unpack of release."""
        tmp_release_search_dir = Path(TEST_DIR, "tmp")

        # Setup tmp_release_search_dir
        for dir in ("Release-Group", "Release.with.subs-Group"):
            distutils.dir_util.copy_tree(
                Path(TEST_DIR, "files", dir), Path(tmp_release_search_dir, dir)
            )

        ru = ReleaseUnpacker(
            tmp_release_search_dir, self.tmp_dir, self.unpack_dir
        )
        ru.unpack_release_dir_rars()

        # Validate extract of release and subs
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
                tmp_release_search_dir,
                ("Release.with.subs-Group/Subs/" "subs_inside_rar.rar"),
            ).exists()
        )

        # Make sure the relese dirs are removed
        self.assertFalse(
            Path(tmp_release_search_dir, "Release-Group").exists()
        )
        self.assertFalse(
            Path(tmp_release_search_dir, "Release.with.subs-Group").exists()
        )

        # Remove tmp_release_dir
        shutil.rmtree(tmp_release_search_dir)


class TestReleaseUnpackerRarFile(unittest.TestCase):
    """ReleaseUnpackerRarFile test case."""

    def test_repr(self):
        """Test object string representation."""
        rar_file_path = Path(TEST_DIR, "files/Release-Group/rar_file.rar")
        rurf = ReleaseUnpackerRarFile(rar_file_path)
        self.assertEqual(
            rurf.__repr__(),
            (
                "<ReleaseUnpackerRarFile: {}/files/"
                "Release-Group/rar_file.rar>".format(TEST_DIR)
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
        rar_file_path = Path(TEST_DIR, "files/Release-Group/rar_file.rar")
        rurf = ReleaseUnpackerRarFile(rar_file_path)
        self.assertFalse(rurf.subs_dir)

        rar_file_path = Path(
            TEST_DIR, ("files/Release.with.subs-Group/Subs/" "subs.rar")
        )
        rurf = ReleaseUnpackerRarFile(rar_file_path)
        self.assertTrue(rurf.subs_dir)
