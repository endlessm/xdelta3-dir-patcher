#!/usr/bin/env python3

import argparse
import tarfile

from os import chmod, chown, geteuid, makedirs, mkdir, path, sep, stat, walk, readlink, symlink
from shutil import copymode, copystat, rmtree
from subprocess import check_output, STDOUT
from stat import *
from sys import stderr
from tempfile import mkdtemp

VERSION='0.1'

# Allows for invoking attributes as methods/functions
class AttributeDict(dict):
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value

class XDelta3Impl(object):
    # TODO: Test me
    @staticmethod
    def run_command(args, exec_method = check_output):
        exec_method(args, stderr=STDOUT)

    # TODO: Test me
    @staticmethod
    def diff(old_file, new_file, target_file, debug = False):
        command = ['xdelta3', '-f', '-e']
        if old_file:
            command.append('-s')
            command.append(old_file)

        command.append(new_file)
        command.append(target_file)

        if debug: print("Generating xdelta: %s" % command)
        XDelta3Impl.run_command(command)

    # TODO: Test me
    @staticmethod
    def apply(old_file, patch_file, target_file, debug = False):
        command = ['xdelta3', '-f', '-d']
        if old_file:
            command.append('-s')
            command.append(old_file)

        command.append(patch_file)
        command.append(target_file)

        if debug: print("Applying xdelta: %s" % command)
        XDelta3Impl.run_command(command)

class XDelta3DirPatcher(object):
    PATCH_FOLDER = 'xdelta'

    def __init__(self, args, delta_impl = XDelta3Impl):
        self.args = args
        self.delta_impl = delta_impl

    # TODO: Test me
    def copy_attributes(self, src_file, dest_file):
        if args.debug: print("Copying mode data")
        copymode(src_file, dest_file)

        if args.debug: print("Copying stat data (sans UID/GID")
        copystat(src_file, dest_file)

        if args.debug: print("Copying UID & GID")
        uid = stat(src_file).st_uid
        gid = stat(src_file).st_gid

        chown(dest_file,uid,gid)

    def _find_file_delta(self, rel_path, new_file, old_root, new_root, target_root):
        print("Processing %s" % new_file)

        target_path = path.join(target_root, rel_path)
        if not path.exists(target_path):
            makedirs(target_path)

        old_path = path.join(old_root, rel_path, new_file)
        new_path = path.join(new_root, rel_path, new_file)
        target_path = path.join(target_path, new_file)

        if args.debug: print([old_path, new_path, target_path])

        if path.islink(new_path):
            new_dst = readlink(new_path)
            symlink(new_dst, target_path)
            if args.debug: print("symlink: ", [target_path, new_dst])
            return

        if not path.isfile(old_path):
            old_path = None
            if args.debug: print("Old file not present. Ignoring source in XDelta")

        self.delta_impl.diff(old_path, new_path, target_path, self.args.debug)

        self.copy_attributes(new_path, target_path)

    def _apply_file_delta(self, rel_path, patch_file, old_root, patch_root, target_root):
        print("Processing %s" % patch_file)

        target_path = path.join(target_root, rel_path)
        if not path.exists(target_path):
            makedirs(target_path)

        old_path = path.join(old_root, rel_path, patch_file)
        patch_path = path.join(patch_root, rel_path, patch_file)
        target_path = path.join(target_path, patch_file)

        if args.debug: print([old_path, patch_path, target_path])

        if path.islink(patch_path):
            patch_dst = readlink(patch_path)
            symlink(patch_dst, target_path)
            if args.debug: print("symlink: ", [target_path, patch_dst])
            return

        if not path.isfile(old_path):
            old_path = None
            if args.debug: print("Old file not present. Ignoring source in XDelta")

        self.delta_impl.apply(old_path, patch_path, target_path, self.args.debug)

        self.copy_attributes(patch_path, target_path)

    # TODO: Test me
    def diff(self, old_dir, new_dir, patch_bundle):
        # Cretate a temp dir
        target_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        print("Using %s as staging area" % target_dir)

        delta_target_dir = path.join(target_dir, self.PATCH_FOLDER)
        mkdir(delta_target_dir)

        for root, dirs, new_files in walk(new_dir):
            rel_path = path.relpath(root, new_dir)

            print('-'*10, root, '-'*10)
            if self.args.debug: print(new_files)
            for new_file in new_files:
                self._find_file_delta(rel_path, new_file, old_dir, new_dir, delta_target_dir)

        print("\nWriting archive...")
        with tarfile.open(patch_bundle, 'w:gz', format=tarfile.GNU_FORMAT) as patch_archive:
            patch_archive.add(delta_target_dir, arcname=self.PATCH_FOLDER)

        print("Cleaning up...")
        rmtree(target_dir)

        print("Done")

    # TODO: Test me
    def apply(self, old_dir, patch_bundle, target_dir):
        # Cretate a temp dir
        patch_dir = mkdtemp(prefix="%s_" % self.__class__.__name__)
        print("Using %s as staging area" % patch_dir)

        print("Extracting archive...")
        with tarfile.open(patch_bundle) as patch_archive:
            patch_archive.extractall(patch_dir)

        delta_patch_dir = path.join(patch_dir, self.PATCH_FOLDER)

        print("Applying patches")
        for root, dirs, patch_files in walk(delta_patch_dir):
            rel_path = path.relpath(root, delta_patch_dir)

            print('-'*10, rel_path, '-'*10)
            if self.args.debug: print(patch_files)
            for patch_file in patch_files:
                self._apply_file_delta(rel_path, patch_file, old_dir, delta_patch_dir, target_dir)

        print("Cleaning up...")
        rmtree(patch_dir)

        print("Done")

    @staticmethod
    def check_euid(ignore_euid, get_euid_method = geteuid):
        if (not ignore_euid) and get_euid_method() != 0:
            stderr.write("ERROR: You must be root to apply the delta! Exiting.\n")
            raise Exception()

    def run(self):
        print("Running directory patcher...")

        if self.args.action == 'diff':
            print("Generating delta pack")
            self.diff(self.args.old_dir, self.args.new_dir, self.args.patch_bundle)
        else:
            # If we're not the root user, bail since we can't ensure that the
            # user and group permissions are retained
            self.check_euid(self.args.ignore_euid)

            print("Applying delta pack")
            self.apply(self.args.old_dir, self.args.patch_bundle, self.args.target_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates and applies XDelta3-based directory diff tgz files')

    subparsers = parser.add_subparsers(dest='action')
    parser_apply = subparsers.add_parser('apply',
            help='Apply a diff from a directory. See "apply -help" for more options')

    parser_diff = subparsers.add_parser('diff',
            help='Generate a diff from a directory. See "diff -help" for more options')

    # Arguments to apply a diff
    parser_apply.add_argument('old_dir',
            help='Folder containing the old version of the files')

    parser_apply.add_argument('patch_bundle',
            help='File containing the patches')

    parser_apply.add_argument('target_dir',
            help='Destination folder for the new versions of files')

    parser_apply.add_argument('--ignore-euid',
            help='Disable checking of EUID on applying the patch',
            default=False,
            action='store_true')

    # Arguments to create a diff
    parser_diff.add_argument('old_dir',
            help='Folder containing the old version of the files')

    parser_diff.add_argument('new_dir',
            help='Folder containing the new version of the files')

    parser_diff.add_argument('patch_bundle',
            help='Destination folder for the generated patch diff')

    # Generic arguments
    parser.add_argument('--debug',
            help='Enable debugging output',
            action='store_true')

    parser.add_argument('--version',
            action='version',
            version='%(prog)s v' + VERSION)

    args = AttributeDict(vars(parser.parse_args()))

    if args.action:
        XDelta3DirPatcher(args).run()
    else:
        parser.print_help()
