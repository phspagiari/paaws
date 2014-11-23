# -*- coding: utf-8 -*-
from prettytable import PrettyTable


def to_table(data):
    table = PrettyTable()
    for column_name, values in data.iteritems():
        table.add_column(column_name, values)
    return table
