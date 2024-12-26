# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.logfile Tests

    @copyright: 2011 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import os
import tempfile
import shutil
from io import StringIO

from MoinMoin.logfile import LogFile


class TestLogFile(object):
    """ testing logfile reading/writing """
    # mtime rev action pagename host hostname user_id extra comment
    LOG = [
           ['1292630945000000', '00000001', 'SAVENEW', 'foo', '0.0.0.0', 'example.org', '111.111.111', '', ''],
           ['1292630957849084', '99999999', 'ATTNEW', 'foo', '0.0.0.0', 'example.org', '222.222.222', 'file.txt', ''],
           ['1292680177309091', '99999999', 'ATTDEL', 'foo', '0.0.0.0', 'example.org', '333.333.333', 'file.txt', ''],
           ['1292680233866579', '99999999', 'ATTNEW', 'foo', '0.0.0.0', 'example.org', '444.444.444', 'new.tgz', ''],
           ['1303073723000000', '00000002', 'SAVE', 'foo', '0.0.0.0', 'example.org', '555.555.555', '', ''],
          ]

    def make_line(self, linedata):
        line = '\t'.join(linedata) + '\n'
        return line.encode('utf-8')

    def write_log(self, fname, data):
        f = open(fname, "wb")
        for linedata in data:
            f.write(self.make_line(linedata))
        f.close()

    def setup_method(self, method):
        self.fname = tempfile.mktemp()
        self.write_log(self.fname, self.LOG)

    def teardown_method(self, method):
        os.remove(self.fname)

    def test_add(self):
        fname_log = tempfile.mktemp()
        lf = LogFile(fname_log)
        for linedata in self.LOG:
            lf.add(*linedata)
        expected_contents = open(self.fname, 'rb').read()
        real_contents = open(fname_log, 'rb').read()
        print(repr(expected_contents))
        print(repr(real_contents))
        assert real_contents == expected_contents

    def test_iter_forward(self):
        lf = LogFile(self.fname)
        for result, expected in zip(lf, self.LOG):
            print(expected)
            print(result)
            assert result == expected

    def test_iter_reverse(self):
        lf = LogFile(self.fname)
        for result, expected in zip(lf.reverse(), self.LOG[::-1]):
            print(expected)
            print(result)
            assert result == expected

    def test_position(self):
        lf = LogFile(self.fname)
        expected_pos = 0
        for data in lf:
            expected_pos += len(self.make_line(data))
            real_pos = lf.position()
            print(expected_pos, real_pos)
            assert real_pos == expected_pos

    def test_seek(self):
        lf = LogFile(self.fname)
        for data in lf:
            print(repr(data))
        # now we are at the current end, remember position
        pos = lf.position()
        # add new data
        newdata = ['1303333333000000', '00000003', 'SAVE', 'foo', '0.0.0.0', 'example.org', '666.666.666', '', 'comment']
        lf.add(*newdata)
        # go to position before new data
        lf.seek(pos)
        assert lf.position() == pos
        for data in lf:
            # reads the one new line we added
            print('new:', repr(data))
            assert data == newdata
        lf.seek(0)
        assert lf.position() == 0
        assert list(lf) == self.LOG + [newdata]

coverage_modules = ['MoinMoin.logfile']

