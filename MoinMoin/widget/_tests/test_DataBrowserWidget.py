# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.widget.browser Tests

    @copyright: 2010 by MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""

import py
from MoinMoin.util.dataset import TupleDataset, Column
from MoinMoin.widget.browser import DataBrowserWidget


class Test_DataBrowserWidget_sort_table(object):
    def setup_class(self):
        # check if state of example changes during tests
        example = [['L1', ('c', 'c'), ('1', '1'),   ('2', '2'),           ('a', 'a'),  ('4', '4'),   ('5', '5')],
                   ['L2', ('b', 'b'), ('10', '10'), ('21', '21'),         ('B', 'B'),  ('40', '40'), ('10', '10')],
                   ['L3', ('b', 'b'), ('2', '2'),   ('3.14', '3.14'),     ('c', 'c'),  ('54', '54'), ('50', '50')],
                   ['L4', ('b', 'b'), ('90', '90'), ('-2.240', '-2.240'), ('D', 'D'),  ('40', '40'), ('5', '5')],
                   ['L5', ('a', 'a'), ('95', '95'), ('20', '20'),         ('e', 'e'),  ('40', '40'), ('10', '10')],
                  ]
        self.example = example
        data = TupleDataset()
        data.columns = []
        data.columns.extend([Column('TEST', label='TEST')])

        for line in self.example:
            data.addRow([line[0]] + line[1:])
            data.columns.extend([Column(line[0], label=line[0])])

        self.data = data
        self.table = DataBrowserWidget(self.request)


    def test_tablecreation(self):
        """
        tests input data not changed
        """
        self.table.setData(self.data)
        result = self.table.data.data
        example = self.example
        assert result == example

    def test_sort_one_column_alphas(self):
        """
        tests one column sorted alphabetically
        """
        self.table.setData(self.data, sort_columns=[4])
        test_run = self.table.data.data
        result = [result[0] for result in test_run]
        assert result == ['L2', 'L4', 'L1', 'L3', 'L5']

    def test_sort_one_column_integers(self):
        """
        tests one column sorted numerical
        """
        self.table.setData(self.data, sort_columns=[2])
        test_run = self.table.data.data
        result = [result[0] for result in test_run]
        assert result == ['L1', 'L3', 'L2', 'L4', 'L5']

    def test_sort_one_column_floats(self):
        """
        tests one column sorted numerical for floating point values
        """
        self.table.setData(self.data, sort_columns=[3])
        test_run = self.table.data.data
        result = [result[0] for result in test_run]
        assert result == ['L4', 'L1', 'L3', 'L5', 'L2']

    def test_n_sort(self):
        """
        tests n_sort
        """
        self.table.setData(self.data, sort_columns=[1, 2])
        test_run = self.table.data.data
        result = [result[0] for result in test_run]
        assert result == ['L5', 'L3', 'L2', 'L4', 'L1']

        self.table.setData(self.data, sort_columns=[5, 6, 3])
        test_run = self.table.data.data
        result = [result[0] for result in test_run]
        assert result == ['L1', 'L4', 'L5', 'L2', 'L3']

    def test_reverse_sort(self):
        """
        tests reverse sort
        """
        self.table.setData(self.data, sort_columns=[0], reverse=True)
        test_run = self.table.data.data
        result = [result[0] for result in test_run]
        assert result == ['L5', 'L4', 'L3', 'L2', 'L1']

    def test_sort_and_reverse_by_a_different_column(self):
        """
        tests reverse sort by a different column as the one to sort
        """
        self.table.setData(self.data, sort_columns=[6], reverse=[0])
        test_run = self.table.data.data
        result = [result[0] for result in test_run]
        assert result == ['L4', 'L1', 'L5', 'L2', 'L3']
