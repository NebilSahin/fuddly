################################################################################
#
#  Copyright 2014-2016 Eric Lacombe <eric.lacombe@security-labs.org>
#
################################################################################
#
#  This file is part of fuddly.
#
#  fuddly is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  fuddly is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with fuddly. If not, see <http://www.gnu.org/licenses/>
#
################################################################################

from __future__ import print_function

import os
import sys
import subprocess
import re
import inspect
import uuid


class Term(object):

    def __init__(self, name=None, keepterm=False, xterm_args=None, xterm_prg_name='x-terminal-emulator'):
        self.name = name
        self.keepterm = keepterm
        self.xterm_args = xterm_args
        self.xterm_prg_name = xterm_prg_name

    def start(self):
        self.pipe_path = os.sep + os.path.join('tmp', 'fuddly_term_'+str(uuid.uuid4()))
        if not os.path.exists(self.pipe_path):
            os.mkfifo(self.pipe_path)
        self.cmd = [self.xterm_prg_name]
        if self.name is not None:
            self.cmd.extend(['-title',self.name])
        if self.xterm_args:
            self.cmd.extend(self.xterm_args)
        if self.keepterm:
            self.cmd.append('--hold')
        self.cmd.extend(['-e', 'tail -f {:s}'.format(self.pipe_path)])
        self._p = None

    def _launch_term(self):
        self._p = subprocess.Popen(self.cmd)

    def stop(self):
        if not self.keepterm and self._p is not None and self._p.poll() is None:
            self._p.kill()
        self._p = None
        try:
            os.remove(self.pipe_path)
        except FileNotFoundError:
            pass

    def print(self, s, newline=False):
        s += '\n' if newline else ''
        if self._p is None or self._p.poll() is not None:
            self._launch_term()
        with open(self.pipe_path, "w") as input_desc:
            input_desc.write(s)

    def print_nl(self, s):
        self.print(s, newline=True)


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def ensure_file(f):
    if not os.path.isfile(f):
        open(f, 'a').close()

def chunk_lines(string, length):
    l = string.split(' ')
    chk_list = []
    full_line = ''
    for wd in l:
        full_line += wd + ' '
        if len(full_line) > (length - 1):
            chk_list.append(full_line)
            full_line = ''
    if full_line:
        chk_list.append(full_line)
    # remove last space char
    if chk_list:
        chk_list[-1] = (chk_list[-1])[:-1]
    return chk_list

def find_file(filename, root_path):
    for (dirpath, dirnames, filenames) in os.walk(root_path):
        if filename in filenames:
            return dirpath + os.sep + filename
    else:
        return None

def retrieve_app_handler(filename):
    mimetype = subprocess.check_output(['xdg-mime', 'query', 'filetype', filename])[:-1]
    desktop_file = subprocess.check_output(['xdg-mime', 'query', 'default', mimetype])[:-1]

    file_path = find_file(desktop_file.decode(), root_path='~/.local/share/applications/')
    if file_path is None:
        file_path = find_file(desktop_file.decode(), root_path='/usr/share/applications/')

    if file_path is None:
        return None

    with open(file_path, 'r') as f:
        buff = f.read()
        result = re.search("Exec=(.*)", buff)
        app_name = result.group(1).split()[0]
    return app_name


if sys.version_info[0] > 2:
    def get_caller_object(stack_frame=2):
        caller_frame_record = inspect.stack()[stack_frame]
        return caller_frame_record.frame.f_locals['self']
else:
    def get_caller_object(stack_frame=2):
        caller_frame_record = inspect.stack()[stack_frame]
        return caller_frame_record[0].f_locals['self']
