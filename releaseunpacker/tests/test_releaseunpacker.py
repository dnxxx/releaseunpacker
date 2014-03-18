import os
from tempfile import mkdtemp
import shutil
import distutils.dir_util

from nose.tools import (assert_raises, assert_equal, assert_false, assert_true)

from unipath import Path

from releaseunpacker.releaseunpacker import (ReleaseUnpacker,
                                             ReleaseUnpackerError,
                                             ReleaseUnpackerRarFile,
                                             ReleaseUnpackerRarFileError)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class TestReleaseUnpacker(object):
    def setUp(self):
        self.tmp_dir = mkdtemp()
        self.unpack_dir = mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
        shutil.rmtree(self.unpack_dir)

    def test_repr(self):
        release_search_dir = Path(TEST_DIR, 'files/')
        ru = ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)
        assert_equal(ru.__repr__(), '<ReleaseUnpacker: {} ({}) ({})>'.format(
            release_search_dir.absolute(), self.tmp_dir, self.unpack_dir))

    def test_release_search_dir_does_not_exist(self):
        release_search_dir = Path('/non_existing_release_search_dir')
        assert_raises(ReleaseUnpackerError, ReleaseUnpacker,
                      release_search_dir, self.tmp_dir, self.unpack_dir)

        try:
            ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)
        except ReleaseUnpackerError, e:
            assert_equal(e.message,
                         'Release search dir {} doesn\'t exist'.format(
                             release_search_dir))

    def test_release_search_dir_not_a_dir(self):
        release_search_dir = Path(TEST_DIR, 'files/file_not_a_dir')
        assert_raises(ReleaseUnpackerError, ReleaseUnpacker,
                      release_search_dir, self.tmp_dir, self.unpack_dir)

        try:
            ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)
        except ReleaseUnpackerError, e:
            assert_equal(e.message,
                         'Release search dir {} is not a dir'.format(
                             release_search_dir))

    def test_tmp_dir_does_not_exist(self):
        release_search_dir = Path(TEST_DIR, 'files/')
        tmp_dir = Path('/non_existing_tmp_dir')
        assert_raises(ReleaseUnpackerError, ReleaseUnpacker,
                      release_search_dir, tmp_dir, self.unpack_dir)

        try:
            ReleaseUnpacker(release_search_dir, tmp_dir, self.unpack_dir)
        except ReleaseUnpackerError, e:
            assert_equal(e.message,
                         'Tmp dir {} doesn\'t exist'.format(tmp_dir))

    def test_tmp_dir_not_a_dir(self):
        release_search_dir = Path(TEST_DIR, 'files/')
        tmp_dir = Path(TEST_DIR, 'files/file_not_a_dir')
        assert_raises(ReleaseUnpackerError, ReleaseUnpacker,
                      release_search_dir, tmp_dir, self.unpack_dir)

        try:
            ReleaseUnpacker(release_search_dir, tmp_dir, self.unpack_dir)
        except ReleaseUnpackerError, e:
            assert_equal(e.message,
                         'Tmp dir {} is not a dir'.format(
                             tmp_dir))

    def test_unpack_dir_does_not_exist(self):
        release_search_dir = Path(TEST_DIR, 'files/')
        unpack_dir = Path('/non_existing_unpack_dir')
        assert_raises(ReleaseUnpackerError, ReleaseUnpacker,
                      release_search_dir, self.tmp_dir, unpack_dir)

        try:
            ReleaseUnpacker(release_search_dir, self.tmp_dir, unpack_dir)
        except ReleaseUnpackerError, e:
            assert_equal(e.message,
                         'Unpack dir {} doesn\'t exist'.format(unpack_dir))

    def test_unpack_dir_not_a_dir(self):
        release_search_dir = Path(TEST_DIR, 'files/')
        unpack_dir = Path(TEST_DIR, 'files/file_not_a_dir')
        assert_raises(ReleaseUnpackerError, ReleaseUnpacker,
                      release_search_dir, self.tmp_dir, unpack_dir)

        try:
            ReleaseUnpacker(release_search_dir, self.tmp_dir, unpack_dir)
        except ReleaseUnpackerError, e:
            assert_equal(e.message,
                         'Unpack dir {} is not a dir'.format(
                             unpack_dir))

    def test_scan_rars(self):
        release_search_dir = Path(TEST_DIR, 'files/')
        ru = ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)
        assert_equal(ru.scan_rars(),
                     [Path(TEST_DIR, 'files/Release-Group/rar_file.rar'),
                      Path(TEST_DIR, ('files/Release.with.subs-Group/'
                                      'release.with.subs-group.rar')),
                      Path(TEST_DIR, ('files/Release.with.subs-Group/Subs'
                                      '/subs.rar'))])

        release_search_dir = Path(TEST_DIR, 'files/Release-Group')
        ru = ReleaseUnpacker(release_search_dir, self.tmp_dir, self.unpack_dir)
        assert_equal(ru.scan_rars(),
                     [Path(TEST_DIR, 'files/Release-Group/rar_file.rar')])

    def test_unpack_release_dir_rars_no_rars_found(self):
        tmp_release_search_dir = Path(TEST_DIR, 'tmp')
        tmp_release_search_dir.mkdir()

        ru = ReleaseUnpacker(tmp_release_search_dir, self.tmp_dir,
                             self.unpack_dir)
        assert_false(ru.unpack_release_dir_rars())

        # Remove tmp_release_dir
        shutil.rmtree(tmp_release_search_dir)

    def test_unpack_release_dir_rars(self):
        tmp_release_search_dir = Path(TEST_DIR, 'tmp')

        # Setup tmp_release_search_dir
        for dir in ('Release-Group', 'Release.with.subs-Group'):
            distutils.dir_util.copy_tree(Path(TEST_DIR, 'files', dir),
                                         Path(tmp_release_search_dir, dir))

        ru = ReleaseUnpacker(tmp_release_search_dir, self.tmp_dir,
                             self.unpack_dir)
        ru.unpack_release_dir_rars()

        # Validate extract of release and subs
        assert_equal(Path(self.unpack_dir).listdir(),
                     [Path(self.unpack_dir, 'Release-Group.mkv'),
                      Path(self.unpack_dir, 'Release.with.subs-Group.idx'),
                      Path(self.unpack_dir, 'Release.with.subs-Group.mkv'),
                      Path(self.unpack_dir, 'Release.with.subs-Group.sub')])

        # Make sure the unpacked subs rar file is removed
        assert_false(Path(tmp_release_search_dir,
                          ('Release.with.subs-Group/Subs/'
                           'subs_inside_rar.rar')).exists())

        # Make sure the relese dirs are removed
        assert_false(Path(tmp_release_search_dir, 'Release-Group').exists())
        assert_false(Path(tmp_release_search_dir,
                          'Release.with.subs-Group').exists())

        # Remove tmp_release_dir
        shutil.rmtree(tmp_release_search_dir)


class TestReleaseUnpackerRarFile(object):
    def test_repr(self):
        rar_file_path = Path(TEST_DIR, 'files/Release-Group/rar_file.rar')
        rurf = ReleaseUnpackerRarFile(rar_file_path)
        assert_equal(rurf.__repr__(),
                    ('<ReleaseUnpackerRarFile: {}/files/'
                     'Release-Group/rar_file.rar>'.format(TEST_DIR)))

    def test_invalid_rar_file(self):
        rar_file_path = 'invalid_rar_file'
        assert_raises(ReleaseUnpackerRarFileError, ReleaseUnpackerRarFile,
                      rar_file_path)

        try:
            ReleaseUnpackerRarFile(rar_file_path)
        except ReleaseUnpackerRarFileError, e:
            assert_equal(e.message,
                         'Invalid RAR file {}'.format(rar_file_path))

    def test_subs_dir(self):
        rar_file_path = Path(TEST_DIR, 'files/Release-Group/rar_file.rar')
        rurf = ReleaseUnpackerRarFile(rar_file_path)
        assert_false(rurf.subs_dir)

        rar_file_path = Path(TEST_DIR, ('files/Release.with.subs-Group/Subs/'
                                        'subs.rar'))
        rurf = ReleaseUnpackerRarFile(rar_file_path)
        assert_true(rurf.subs_dir)
