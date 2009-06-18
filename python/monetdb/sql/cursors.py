# The contents of this file are subject to the MonetDB Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://monetdb.cwi.nl/Legal/MonetDBLicense-1.1.html
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
#
# The Original Code is the MonetDB Database System.
#
# The Initial Developer of the Original Code is CWI.
# Portions created by CWI are Copyright (C) 1997-July 2008 CWI.
# Copyright August 2008-2009 MonetDB B.V.
# All Rights Reserved.

import logging

try:
    from monetdb import mapi
except SyntaxError:
    # python 2.5 support
    from monetdb import mapi25 as mapi

from monetdb.sql import converters
from monetdb.monetdb_exceptions import ProgrammingError, Error


class Cursor:
    """These objects represent a database cursor, which is used to manage
    the context of a fetch operation. Cursors created from the same
    connection are not isolated, i.e., any changes done to the
    database by a cursor are immediately visible by the other
    cursors. Cursors created from different connections can or can not
    be isolated, depending on how the transaction support is
    implemented (see also the connection's .rollback() and .commit()
    methods)."""


    def __init__(self, connection):
        """This read-only attribute return a reference to the Connection
        object on which the cursor was created.

        The attribute simplifies writing polymorph code in
        multi-connection environments."""
        self.connection = connection

        """last executed operation (query)"""
        self.operation = ""

        """This read/write attribute specifies the number of rows to
        fetch at a time with .fetchmany(). It defaults to 1
        meaning to fetch a single row at a time."""
        self.arraysize = 1


        """This read-only attribute specifies the number of rows that
        the last .execute*() produced (for DQL statements like
        'select') or affected (for DML statements like 'update' or
        'insert').

        The attribute is -1 in case no .execute*() has been
        performed on the cursor or the rowcount of the last
        operation is cannot be determined by the interface. [7]

        Note: Future versions of the DB API specification could
        redefine the latter case to have the object return None
        instead of -1."""
        self.rowcount = -1

        """This read-only attribute is a sequence of 7-item
        sequences.

        Each of these sequences contains information describing
        one result column:

          (name,
           type_code,
           display_size,
           internal_size,
           precision,
           scale,
           null_ok)

        The first two items (name and type_code) are mandatory,
        the other five are optional and are set to None if no
        meaningful values can be provided.

        This attribute will be None for operations that
        do not return rows or if the cursor has not had an
        operation invoked via the .execute*() method yet.

        The type_code can be interpreted by comparing it to the
        Type Objects specified in the section below."""
        self.description = None

        """This read-only attribute indicates at which row
        we currently are"""
        self.rownumber = -1

        self.__executed = None

        # the offset of the current resultset in the total resultset
        self.__offset = 0

        # the resultset
        self.__rows = []

        # the type converters
        self.__pythonizer = converters.Pythonizer()
        self.__monetizer = converters.Monetizer()



        """This is a Python list object to which the interface appends
        tuples (exception class, exception value) for all messages
        which the interfaces receives from the underlying database for
        this cursor.

        The list is cleared by all standard cursor methods calls (prior
        to executing the call) except for the .fetch*() calls
        automatically to avoid excessive memory usage and can also be
        cleared by executing "del cursor.messages[:]".

        All error and warning messages generated by the database are
        placed into this list, so checking the list allows the user to
        verify correct operation of the method calls.

        The aim of this attribute is to eliminate the need for a
        Warning exception which often causes problems (some warnings
        really only have informational character)."""
        #TODO: implement
        self.messages = []



        """This read-only attribute provides the rowid of the last
        modified row (most databases return a rowid only when a single
        INSERT operation is performed). If the operation does not set
        a rowid or if the database does not support rowids, this
        attribute should be set to None.

        The semantics of .lastrowid are undefined in case the last
        executed statement modified more than one row, e.g. when
        using INSERT with .executemany()."""
        # TODO: implement
        self.lastrowid = None

    def __check_executed(self):
        if not self.__executed:
            raise ProgrammingError("do a execute() first")


    """
    def callproc(self, procname, parameters=None):
        (This method is optional since not all databases provide
        stored procedures. [3])

        Call a stored database procedure with the given name. The
        sequence of parameters must contain one entry for each
        argument that the procedure expects. The result of the
        call is returned as modified copy of the input
        sequence. Input parameters are left untouched, output and
        input/output parameters replaced with possibly new values.

        The procedure may also provide a result set as
        output. This must then be made available through the
        standard .fetch*() methods.
    """


    def close(self):
        """ Close the cursor now (rather than whenever __del__ is
        called).  The cursor will be unusable from this point
        forward; an Error (or subclass) exception will be raised
        if any operation is attempted with the cursor."""
        self.connection = None


    def execute(self, operation, parameters=None):
        """Prepare and execute a database operation (query or
        command).  Parameters may be provided as sequence or
        mapping and will be bound to variables in the operation.
        Variables are specified in a database-specific notation
        (see the module's paramstyle attribute for details). [5]

        A reference to the operation will be retained by the
        cursor.  If the same operation object is passed in again,
        then the cursor can optimize its behavior.  This is most
        effective for algorithms where the same operation is used,
        but different parameters are bound to it (many times).

        For maximum efficiency when reusing an operation, it is
        best to use the .setinputsizes() method to specify the
        parameter types and sizes ahead of time.  It is legal for
        a parameter to not match the predefined information; the
        implementation should compensate, possibly with a loss of
        efficiency.

        The parameters may also be specified as list of tuples to
        e.g. insert multiple rows in a single operation, but this
        kind of usage is deprecated: .executemany() should be used
        instead.

        Return values are not defined."""


        # TODO: check if this belongs here
        # set the number of rows to fetch
        self.connection.command('Xreply_size %s' % self.arraysize)

        if operation == self.operation:
            #TODO: same operation, reuse?
            pass
        else:
            self.operation = operation

        if parameters:
            #parameters = dict([(k, types.format(v)) for (k,v) in parameters.items()])
            #self.query = operation % converters.escape(parameters)
            self.query = operation % dict([(k, self.__monetizer.convert(v)) for (k,v) in parameters.items()])
        else:
            self.query = operation

        block = self.connection.execute(self.query)
        self.__store_result(block)
        self.rownumber = 0
        self.__executed = operation
        return self.rowcount



    def executemany(self, operation, seq_of_parameters):
        """Prepare a database operation (query or command) and then
        execute it against all parameter sequences or mappings
        found in the sequence seq_of_parameters.

        Modules are free to implement this method using multiple
        calls to the .execute() method or by using array operations
        to have the database process the sequence as a whole in
        one call.

        Use of this method for an operation which produces one or
        more result sets constitutes undefined behavior, and the
        implementation is permitted (but not required) to raise
        an exception when it detects that a result set has been
        created by an invocation of the operation.

        The same comments as for .execute() also apply accordingly
        to this method.

        Return values are not defined."""

        count = 0
        for parameters in seq_of_parameters:
            count += self.execute(operation, parameters)
        return count


    def fetchone(self):
        """Fetch the next row of a query result set, returning a
        single sequence, or None when no more data is available."""
        logging.debug("II executing fetch one")

        self.__check_executed()

        if self.rowcount == -1:
             # TODO: change error exception to something more detailed
            raise Error("query didn't result in a resultset")

        if self.rownumber >= (self.rowcount):
            logging.debug("rownumber >= rowcount")
            return None

        logging.debug("rownumber: %s" % self.rownumber)
        logging.debug("offset: %s" % self.__offset)
        logging.debug("lenrows: %s" % len(self.__rows))


        if self.rownumber >= (self.__offset + len(self.__rows)):
            self.nextset()

        result = self.__rows[self.rownumber - self.__offset]
        self.rownumber += 1
        return result


    def fetchmany(self, size=None):
        """Fetch the next set of rows of a query result, returning a
        sequence of sequences (e.g. a list of tuples). An empty
        sequence is returned when no more rows are available.

        The number of rows to fetch per call is specified by the
        parameter.  If it is not given, the cursor's arraysize
        determines the number of rows to be fetched. The method
        should try to fetch as many rows as indicated by the size
        parameter. If this is not possible due to the specified
        number of rows not being available, fewer rows may be
        returned.

        An Error (or subclass) exception is raised if the previous
        call to .execute*() did not produce any result set or no
        call was issued yet.

        Note there are performance considerations involved with
        the size parameter.  For optimal performance, it is
        usually best to use the arraysize attribute.  If the size
        parameter is used, then it is best for it to retain the
        same value from one .fetchmany() call to the next."""

        logging.debug("II executing fetchmany")
        self.__check_executed()

        if self.rownumber >= (self.rowcount):
            return []

        end = self.rownumber + (size or self.arraysize)
        end = min(end, self.rowcount)

        logging.debug("end: %s" % end)

        result = self.__rows[self.rownumber-self.__offset:end-self.__offset]
        self.rownumber = min(end, len(self.__rows)+self.__offset)

        while (end > self.rownumber) and self.nextset():
                result += self.__rows[self.rownumber-self.__offset:end-self.__offset]
                self.rownumber = min(end, len(self.__rows)+self.__offset)
        return result



    def fetchall(self) :
        """Fetch all (remaining) rows of a query result, returning
        them as a sequence of sequences (e.g. a list of tuples).
        Note that the cursor's arraysize attribute can affect the
        performance of this operation.

        An Error (or subclass) exception is raised if the previous
        call to .execute*() did not produce any result set or no
        call was issued yet."""

        self.__check_executed()

        if self.rowcount == -1:
            raise Error("query didn't result in a resultset")

        result = self.__rows[self.rownumber - self.__offset:]
        self.rownumber = len(self.__rows) + self.__offset

        # slide the window over the resultset
        while self.nextset():
            result += self.__rows
            self.rownumber = len(self.__rows) + self.__offset

        return result



    def nextset(self):
        """This method will make the cursor skip to the next
        available set, discarding any remaining rows from the
        current set.

        If there are no more sets, the method returns
        None. Otherwise, it returns a true value and subsequent
        calls to the fetch methods will return rows from the next
        result set.

        An Error (or subclass) exception is raised if the previous
        call to .execute*() did not produce any result set or no
        call was issued yet."""

        logging.debug("retreiving next set")

        self.__check_executed()

        if self.rownumber >= self.rowcount:
            return False

        self.__offset += len(self.__rows)

        end = min(self.rowcount, self.rownumber + self.arraysize)
        amount = end - self.__offset

        command = 'Xexport %s %s %s' % (self.__query_id, self.__offset, amount)
        block = self.connection.command(command)
        self.__store_result(block)
        return True



    def setinputsizes(self, sizes):
        """This can be used before a call to .execute*() to
        predefine memory areas for the operation's parameters.

        sizes is specified as a sequence -- one item for each
        input parameter.  The item should be a Type Object that
        corresponds to the input that will be used, or it should
        be an integer specifying the maximum length of a string
        parameter.  If the item is None, then no predefined memory
        area will be reserved for that column (this is useful to
        avoid predefined areas for large inputs).

        This method would be used before the .execute*() method
        is invoked.

        Implementations are free to have this method do nothing
        and users are free to not use it."""
        pass


    def setoutputsize(self, size, column=None):
        """Set a column buffer size for fetches of large columns
        (e.g. LONGs, BLOBs, etc.).  The column is specified as an
        index into the result sequence.  Not specifying the column
        will set the default size for all large columns in the
        cursor.

        This method would be used before the .execute*() method
        is invoked.

        Implementations are free to have this method do nothing
        and users are free to not use it."""
        pass

    def __iter__(self):
        return self

    def next(self):
        row = self.fetchone()
        if not row:
            raise StopIteration
        return row

    def __store_result(self, block):
        """ parses the mapi result into a resultset"""

        lines = block.split("\n")
        firstline = lines[0]

        while firstline.startswith(mapi.MSG_INFO):
            logging.info(firstline[1:])
            lines = lines[1:]
            firstline = lines[0]

        if firstline.startswith(mapi.MSG_QTABLE):
            (id, rowcount, columns, tuples) = firstline[2:].split()
            columns = int(columns)   # number of columns in result
            rowcount = int(rowcount) # total number of rows
            tuples = int(tuples)     # number of rows in this set
            rows = []

            # set up fields for description
            empty = [None]*columns
            table_name = empty
            column_name = empty
            type = empty
            display_size = empty
            internal_size = empty
            precision = empty
            scale = empty
            null_ok = empty

            for line in lines[1:]:
                if line.startswith(mapi.MSG_HEADER):
                    (data, identity) = line[1:].split("#")
                    values = [x.strip() for x in data.split(",")]
                    identity = identity.strip()

                    if identity == "table_name":
                        table_name = values   # not used
                    elif identity == "name":
                        column_name = values
                    elif identity == "type":
                        type = values
                    elif identity == "length":
                        internal_size = [int(x) for x in values]
                        display_size = internal_size
                    else:
                        raise InterfaceError("unknown header field")

                    self.description = list(zip(column_name, type, display_size, internal_size, precision, scale, null_ok))

                if line.startswith(mapi.MSG_TUPLE):
                    values = self.__parse_tuple(line)
                    rows.append(values)

                elif line == mapi.MSG_PROMPT:
                    self.__query_id = id
                    self.__rows = rows
                    self.__offset = 0

                    self.rowcount = rowcount
                    logging.debug("II store result finished")
                    return

        elif firstline.startswith(mapi.MSG_QBLOCK):
            rows = []
            for line in lines[1:]:
                if line.startswith(mapi.MSG_TUPLE):
                    values = self.__parse_tuple(line)
                    rows.append(values)
                elif line == mapi.MSG_PROMPT:
                    logging.debug("II store result finished")
                    self.__rows = rows
                    return

        elif firstline.startswith(mapi.MSG_QSCHEMA):
           if lines[1] == mapi.MSG_PROMPT:
                self.__rows = []
                self.__offset = 0
                self.description = None
                self.rowcount = -1
                logging.debug("II schema finished")
                return

        elif firstline.startswith(mapi.MSG_QUPDATE):
           if lines[1] == mapi.MSG_PROMPT:
                self.__rows = []
                self.__offset = 0
                self.description = None
                self.rowcount = -1
                logging.debug("II update finished")
                return

        elif firstline.startswith(mapi.MSG_ERROR):
            raise ProgrammingError(firstline[1:])

        # you are not supposed to be here
        raise InterfaceError("Unknown state, %s" % block)


    def __parse_tuple(self, line):
        """ parses a mapi data tuple, and returns a list of python types"""

        # values are seperated by ,\t. Substrings can contain this also, so
        # if the length of the tuple doesn't match, we do a manual split
        elements = line[1:-1].split(',\t')
        if len(elements) == len(self.description):
            return [self.__pythonizer.convert(element.strip(), description[1]) for
                    (element, description) in zip(elements, self.description)]

        # Ok, that didn't work. Manual split then...
        # TODO: this will FAIL in case of " [ \",\"] " (comma in a substring in a substring)
        elements = []
        sub_str = False
        buff = ""
        for char in line[1:-1]:
            if char == '"':
                sub_str = not sub_str
                buff = buff + char
            elif char == "," and not sub_str:
                elements.append(buff.strip())
                buff = ""
            else:
                buff = buff + char
        elements.append(buff.strip())

        #convert values to python types
        return [self.__pythonizer.convert(element, description[1]) for
                (element, description) in zip(elements, self.description)]


        def scroll(self, value, mode='relative'):
            """Scroll the cursor in the result set to a new position according
            to mode.

            If mode is 'relative' (default), value is taken as offset to
            the current position in the result set, if set to 'absolute',
            value states an absolute target position.

            An IndexError should be raised in case a scroll operation would
            leave the result set. In this case, the cursor position is left
            undefined (ideal would be to not move the cursor at all).

            Note: This method should use native scrollable cursors, if
            available , or revert to an emulation for forward-only
            scrollable cursors. The method may raise NotSupportedErrors to
            signal that a specific operation is not supported by the
            database (e.g. backward scrolling)."""

            self.__check_executed()
            # TODO: finish this, megre with nextset()

            if mode not in ['relative', 'absolute']:
                raise ProgrammingError("unknown mode '%s'" % mode)

            if mode == 'relative':
                value = self.rownumber + value

            if value > self.rowcount:
                raise IndexError("value beyond length of resultset")



