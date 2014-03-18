## Release unpacker
Scan release dir(s) for releases to unpack. If a rar file is found inside a
folder it'll be extracted to tmp dir then moved to unpack dir. If a subs
folder exists inside the release this too will be extracted. This includs subs
rar inside a subs rar. When extracted the files will be renamed to the same
name as the release folder and the release folder will be removed.

## Example
This:

    Release-Group/rar01.rar (group-release.mkv)
    Release-Group/rar02.rar
    Release-Group/rar03.rar
    Release-Group/Subs/rar01.rar (subs.idx, subs.rar (subs.sub))
    Release-Group/Subs/rar02.rar

Will be turned into:

    Release-Group.mkv
    Release-Group.idx
    Release-Group.sub


## Environment variables
If you set these you don't need -t or -u every time.

    RELEASEUNPACKER_TMP_DIR - Tmp dir to unpack to
    RELEASEUNPACKER_UNPACK_DIR - Final dir to move unpacked files to

## Usage
    releaseunpacker /path/to/dir
    releaseunpacker /path/to/dir1 /path/to/dir2 /path/to/dir3

## Help
    usage: releaseunpacker [-h] [-t TMP_DIR] [-u UNPACK_DIR] [-d] [-n] [-s]
                           [-l LOG]
                           [release_dir [release_dir ...]]

    Unpacks all movie releases in release_dir. Supports mkv, avi and img/iso
    releases. Also extracts subs if a subs folder is found. Renames all unpacked
    files to the same name as relase dir. ENV vars: RELEASEUNPACKER_TMP_DIR tmp
    dir to unpack release to, same as -t. RELEASEUNPACKER_UNPACK_DIR dir to move
    unpacked release to, same as -u.

    positional arguments:
      release_dir

    optional arguments:
      -h, --help            show this help message and exit
      -t TMP_DIR, --tmp-dir TMP_DIR
                            Tmp dir to unpack release to (default: None)
      -u UNPACK_DIR, --unpack-dir UNPACK_DIR
                            Dir to move unpacked releases to (default: None)
      -d, --debug           Output debug info (default: False)
      -n, --no-remove       Don't remove anything after unpack (default: False)
      -s, --silent          Disable console output (default: False)
      -l LOG, --log LOG     Log to file (default: None)

## Crontab example
    releaseunpacker --silent --log /path/to/log/dir/releaseunpacker.log /path/to/dir

## Install
    pip install git+https://github.com/dnxxx/releaseunpacker

## Warning
This hasn't been really battle tested yet, there will probably be bugs.

No checks are currently made to make sure the unpack was successfull. If an
unpack fails without an exception the release dir will still be removed.

Don't run this on folders with rar files who isn't releases. If you run this
on a dir without releases they'll be processed, not unpacked (wrong file exts)
and then removed.

You've been warned!

## Todo
- Validate unpack before removal of release dir
