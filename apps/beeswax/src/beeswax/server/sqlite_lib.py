#!/usr/bin/env python
# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

try:
  try:
    from pysqlite2 import dbapi2 as Database
  except ImportError, e1:
    from sqlite3 import dbapi2 as Database
except ImportError, exc:
  from django.core.exceptions import ImproperlyConfigured
  raise ImproperlyConfigured("Error loading either pysqlite2 or sqlite3 modules (tried in that order): %s" % exc)

from beeswax.server.rdbms_base_lib import BaseRDBMSDataTable, BaseRDBMSResult, BaseRDMSClient


LOG = logging.getLogger(__name__)


class DataTable(BaseRDBMSDataTable): pass


class Result(BaseRDBMSResult): pass


class SQLiteClient(BaseRDMSClient):
  """Same API as Beeswax"""

  data_table_cls = DataTable
  result_cls = Result

  def __init__(self, *args, **kwargs):
    super(SQLiteClient, self).__init__(*args, **kwargs)
    self.connection = Database.connect(**self._conn_params)


  @property
  def _conn_params(self):
    return {
      'database': self.query_server['name'],
      'detect_types': Database.PARSE_DECLTYPES | Database.PARSE_COLNAMES,
    }


  def use(self, database):
    # Do nothing because SQLite has one database per path.
    pass


  def execute_statement(self, statement):
    cursor = self.connection.cursor()
    cursor.execute(statement)
    self.connection.commit()
    if cursor.description:
      columns = [column[0] for column in cursor.description]
    else:
      columns = []
    return self.data_table_cls(cursor, columns)


  def get_databases(self):
    return [self._conn_params['database']]


  def get_tables(self, database, table_names):
    # Doesn't use database and only retrieves tables for database currently in use.
    cursor = self.connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    self.connection.commit()
    return [row[0] for row in cursor.fetchall()]


  def get_columns(self, database, table):
    cursor = self.connection.cursor()
    cursor.execute("PRAGMA table_info(%s)" % table)
    self.connection.commit()
    return [row[1] for row in cursor.fetchall()]
