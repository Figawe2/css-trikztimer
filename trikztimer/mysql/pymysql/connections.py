# Python implementation of the MySQL client-server protocol
#   http://forge.mysql.com/wiki/MySQL_Internals_ClientServer_Protocol

import re
import sha
import socket
import struct
import sys

from charset import MBLENGTH
from cursor import Cursor
from constants import FIELD_TYPE
from constants import SERVER_STATUS
from constants.CLIENT_FLAG import *
from constants.COMMAND import *
from converters import escape_item, encoders, decoders
from exceptions import raise_mysql_exception, Warning, Error, \
     InterfaceError, DataError, DatabaseError, OperationalError, \
     IntegrityError, InternalError, NotSupportedError, ProgrammingError

DEBUG = False

NULL_COLUMN = 251
UNSIGNED_CHAR_COLUMN = 251
UNSIGNED_SHORT_COLUMN = 252
UNSIGNED_INT24_COLUMN = 253
UNSIGNED_INT64_COLUMN = 254
UNSIGNED_CHAR_LENGTH = 1
UNSIGNED_SHORT_LENGTH = 2
UNSIGNED_INT24_LENGTH = 3
UNSIGNED_INT64_LENGTH = 8

DEFAULT_CHARSET = 'latin1'
BUFFER_SIZE = 256*256*256-1

def dump_packet(data):
    
    def is_ascii(data):
        if data.isalnum():
            return data
        return '.'
    print "packet length %d" % len(data)
    print "method call[1]: %s" % sys._getframe(1).f_code.co_name
    print "method call[2]: %s" % sys._getframe(2).f_code.co_name
    print "method call[3]: %s" % sys._getframe(3).f_code.co_name
    print "method call[4]: %s" % sys._getframe(4).f_code.co_name
    print "method call[5]: %s" % sys._getframe(5).f_code.co_name
    print "-" * 88
    dump_data = [data[i:i+16] for i in xrange(len(data)) if i%16 == 0]
    for d in dump_data:
        print ' '.join(map(lambda x:"%02X" % ord(x), d)) + \
                '   ' * (16 - len(d)) + ' ' * 2 + ' '.join(map(lambda x:"%s" % is_ascii(x), d))
    print "-" * 88
    print ""

def _scramble(password, message):
    if password == None or len(password) == 0:
        return '\0'
    if DEBUG: print 'password=' + password
    stage1 = sha.new(password).digest()
    stage2 = sha.new(stage1).digest()
    s = sha.new()
    s.update(message)
    s.update(stage2)
    result = s.digest()
    return _my_crypt(result, stage1)

def _my_crypt(message1, message2):
    length = len(message1)
    result = struct.pack('B', length)
    for i in xrange(length):
        x = (struct.unpack('B', message1[i:i+1])[0] ^ struct.unpack('B', message2[i:i+1])[0])
        result += struct.pack('B', x)
    return result

def pack_int24(n):
    return struct.pack('BBB', n&0xFF, (n>>8)&0xFF, (n>>16)&0xFF)

def unpack_uint16(n):
  return struct.unpack('<H', n[0:2])[0]


# TODO: stop using bit-shifting in these functions...
# TODO: rename to "uint" to make it clear they're unsigned...
def unpack_int24(n):
    return struct.unpack('B',n[0])[0] + (struct.unpack('B', n[1])[0] << 8) +\
        (struct.unpack('B',n[2])[0] << 16)

def unpack_int32(n):
    return struct.unpack('B',n[0])[0] + (struct.unpack('B', n[1])[0] << 8) +\
        (struct.unpack('B',n[2])[0] << 16) + (struct.unpack('B', n[3])[0] << 24)

def unpack_int64(n):
    return struct.unpack('B',n[0])[0] + (struct.unpack('B', n[1])[0]<<8) +\
    (struct.unpack('B',n[2])[0] << 16) + (struct.unpack('B',n[3])[0]<<24)+\
    (struct.unpack('B',n[4])[0] << 32) + (struct.unpack('B',n[5])[0]<<40)+\
    (struct.unpack('B',n[6])[0] << 48) + (struct.unpack('B',n[7])[0]<<56)

def defaulterrorhandler(connection, cursor, errorclass, errorvalue):
    err = errorclass, errorvalue
    
    if cursor:
        cursor.messages.append(err)
    else:
        connection.messages.append(err)
    del cursor
    del connection
    raise errorclass, errorvalue


class MysqlPacket(object):
  """Representation of a MySQL response packet.  Reads in the packet
  from the network socket, removes packet header and provides an interface
  for reading/parsing the packet results."""

  def __init__(self, socket):
    self.__position = 0
    self.__recv_packet(socket)
    del socket

  def __recv_packet(self, socket):
    """Parse the packet header and read entire packet payload into buffer."""
    packet_header = socket.recv(4)
    if DEBUG: dump_packet(packet_header)
    packet_length_bin = packet_header[:3]
    self.__packet_number = ord(packet_header[3])
    # TODO: check packet_num is correct (+1 from last packet)

    bin_length = packet_length_bin + '\000'  # pad little-endian number
    bytes_to_read = struct.unpack('<I', bin_length)[0]

    payload_buff = []  # TODO: look if cStringIO is markedly better
    while bytes_to_read > 0:
      recv_data = socket.recv(bytes_to_read)
      if DEBUG: dump_packet(recv_data)
      payload_buff.append(recv_data)
      bytes_to_read -= len(recv_data)
    self.__data = ''.join(payload_buff)

  def packet_number(self): return self.__packet_number

  def read(self, size):
    """Read the first 'size' bytes in packet and advance cursor past them."""
    result = self.peek(size)
    self.advance(size)
    return result

  def read_all(self):
    """Read all remaining data in the packet.

    (Subsequent read() or peek() will return errors.)
    """
    result = self.__data[self.__position:]
    self.__position = None  # ensure no subsequent read() or peek()
    return result

  def advance(self, length):
    """Advance the cursor in data buffer 'length' bytes."""
    new_position = self.__position + length
    if new_position < 0 or new_position > len(self.__data):
      raise Exception('Invalid advance amount (%s) for cursor.  '
                      'Position=%s' % (length, new_position))
    self.__position = new_position

  def rewind(self, position=0):
    """Set the position of the data buffer cursor to 'position'."""
    if position < 0 or position > len(self.__data):
      raise Exception("Invalid position to rewind cursor to: %s." % position)
    self.__position = position

  def peek(self, size):
    """Look at the first 'size' bytes in packet without moving cursor."""
    result = self.__data[self.__position:(self.__position+size)]
    if len(result) != size:
      error = ('Result length not requested length:\n'
               'Expected=%s.  Actual=%s.  Position: %s.  Data Length: %s'
               % (size, len(result), self.__position, len(self.__data)))
      if DEBUG:
        print error
        self.dump()
      raise AssertionError(error)
    return result

  def get_bytes(self, position, length=1):
    """Get 'length' bytes starting at 'position'.

    Position is start of payload (first four packet header bytes are not
    included) starting at index '0'.

    No error checking is done.  If requesting outside end of buffer
    an empty string (or string shorter than 'length') may be returned!
    """
    return self.__data[position:(position+length)]

  def read_coded_length(self):
    """Read a 'Length Coded' number from the data buffer.

    Length coded numbers can be anywhere from 1 to 9 bytes depending
    on the value of the first byte.
    """
    c = ord(self.read(1))
    if c == NULL_COLUMN:
      return None
    if c < UNSIGNED_CHAR_COLUMN:
      return c
    elif c == UNSIGNED_SHORT_COLUMN:
      return unpack_uint16(self.read(UNSIGNED_SHORT_LENGTH))
    elif c == UNSIGNED_INT24_COLUMN:
      return unpack_int24(self.read(UNSIGNED_INT24_LENGTH))
    elif c == UNSIGNED_INT64_COLUMN:
      # TODO: what was 'longlong'?  confirm it wasn't used?
      return unpack_int64(self.read(UNSIGNED_INT64_LENGTH))

  def read_length_coded_binary(self):
    """Read a 'Length Coded Binary' from the data buffer.

    A 'Length Coded Binary' consists first of a length coded
    (unsigned, positive) integer represented in 1-9 bytes followed by
    that many bytes of binary data.  (For example "cat" would be "3cat".)
    """
    length = self.read_coded_length()
    if length:
      return self.read(length)

  def is_ok_packet(self):
    return ord(self.get_bytes(0)) == 0

  def is_eof_packet(self):
    return ord(self.get_bytes(0)) == 254  # 'fe'

  def is_resultset_packet(self):
    field_count = ord(self.get_bytes(0))
    return field_count >= 1 and field_count <= 250

  def is_error_packet(self):
    return ord(self.get_bytes(0)) == 255

  def check_error(self):
    if self.is_error_packet():
      self.rewind()
      self.advance(1)  # field_count == error (we already know that)
      errno = unpack_uint16(self.read(2))
      if DEBUG: print "errno = %d" % errno
      raise_mysql_exception(self.__data)

  def dump(self):
    dump_packet(self.__data)


class FieldDescriptorPacket(MysqlPacket):
  """A MysqlPacket that represents a specific column's metadata in the result.

  Parsing is automatically done and the results are exported via public
  attributes on the class such as: db, table_name, name, length, type_code.
  """

  def __init__(self, *args):
    MysqlPacket.__init__(self, *args)
    self.__parse_field_descriptor()

  def __parse_field_descriptor(self):
    """Parse the 'Field Descriptor' (Metadata) packet.

    This is compatible with MySQL 4.1+ (not compatible with MySQL 4.0).
    """
    self.catalog = self.read_length_coded_binary()
    self.db = self.read_length_coded_binary()
    self.table_name = self.read_length_coded_binary()
    self.org_table = self.read_length_coded_binary()
    self.name = self.read_length_coded_binary()
    self.org_name = self.read_length_coded_binary()
    self.advance(1)  # non-null filler
    self.charsetnr = struct.unpack('<h', self.read(2))[0]
    self.length = struct.unpack('<i', self.read(4))[0]
    self.type_code = ord(self.read(1))
    flags = struct.unpack('<h', self.read(2))
    # TODO: what is going on here with this flag parsing???
    self.flags = int(("%02X" % flags)[1:], 16)
    self.scale = ord(self.read(1))  # "decimals"
    self.advance(2)  # filler (always 0x00)

    # 'default' is a length coded binary and is still in the buffer?
    # not used for normal result sets...

  def description(self):
    """Provides a 7-item tuple compatible with the Python PEP249 DB Spec."""
    desc = []
    desc.append(self.name)
    desc.append(self.type_code)
    desc.append(None)  # 'display size'
    desc.append(self.get_column_length()) # 'internal_size'
    desc.append(self.get_column_length()) # 'precision'  # TODO: why!?!?
    desc.append(self.scale)

    # 'null_ok' -- can this be True/False rather than 1/0?
    #              if so just do:  desc.append(bool(self.flags % 2 == 0))
    if self.flags % 2 == 0:
      desc.append(1)
    else:
      desc.append(0)
    return tuple(desc)

  def get_column_length(self):
    if self.type_code == FIELD_TYPE.VAR_STRING:
      mblen = MBLENGTH.get(self.charsetnr, 1)
      return self.length / mblen
    return self.length

  def __str__(self):
    return ('%s %s.%s.%s, type=%s'
            % (self.__class__, self.db, self.table_name, self.name,
               self.type_code))


class Connection(object):
    """Representation of a socket with a mysql server."""
    errorhandler = defaulterrorhandler

    def __init__(self, *args, **kwargs):
        self.host = kwargs['host']
        self.port = kwargs.get('port', 3306)
        self.user = kwargs['user']
        self.password = kwargs['passwd']
        self.db = kwargs.get('db', None)
        self.unix_socket = kwargs.get('unix_socket', None)
        self.charset = DEFAULT_CHARSET
        
        client_flag = CLIENT_CAPABILITIES
        #client_flag = kwargs.get('client_flag', None)
        client_flag |= CLIENT_MULTI_STATEMENTS
        if self.db:
            client_flag |= CLIENT_CONNECT_WITH_DB
        self.client_flag = client_flag
        
        self._connect()
        
        charset = kwargs.get('charset', None)
        self.set_chatset_set(charset)
        self.messages = []
        self.encoders = encoders
        self.decoders = decoders
        
        self.autocommit(False)
        

    def close(self):
        send_data = struct.pack('<i',1) + COM_QUIT
        sock = self.socket
        sock.send(send_data)
        sock.close()
    
    def autocommit(self, value):
        self._execute_command(COM_QUERY, "SET AUTOCOMMIT = %s" % \
                self.escape(value))
        self.read_packet()

    def commit(self):
        self._execute_command(COM_QUERY, "COMMIT")
        self.read_packet()

    def rollback(self):
        self._execute_command(COM_QUERY, "ROLLBACK")
        self.read_packet()

    def escape(self, obj):
        return escape_item(obj)

    def cursor(self):
        return Cursor(self)
    
    def __enter__(self):
        return self.cursor()

    def __exit__(self, exc, value, traceback):
        if exc:
            self.rollback()
        else:
            self.commit()

    def query(self, sql):
        self._execute_command(COM_QUERY, sql)
        return self._read_query_result()
    
    def next_result(self):
        return self._read_query_result()

    def set_chatset_set(self, charset):
        sock = self.socket
        if charset and self.charset != charset:
            self._execute_command(COM_QUERY, "SET NAMES %s" % charset)
            self.read_packet()
            self.charset = charset     

    def _connect(self):
        if self.unix_socket and (self.host == 'localhost' or self.host == '127.0.0.1'):
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.unix_socket)
            if DEBUG: print 'connected using unix_socket'
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            if DEBUG: print 'connected using socket'
        self.socket = sock
        self._get_server_information()
        self._request_authentication()
    
    def read_packet(self, packet_type=MysqlPacket):
      """Read an entire "mysql packet" in its entirety from the network
      and return a MysqlPacket type that represents the results."""

      # TODO: is socket.recv(small_number) significantly slower than
      #       socket.recv(large_number)?  if so, maybe we should buffer
      #       the socket.recv() (though that obviously makes memory management
      #       more complicated.
      packet = packet_type(self.socket)
      packet.check_error()
      return packet

    def _read_query_result(self):
        result = MySQLResult(self)
        result.read()
        self._result = result
        return result.affected_rows

    def _send_command(self, command, sql):
        send_data = struct.pack('<i', len(sql) + 1) + command + sql
        sock = self.socket
        sock.send(send_data)
        if DEBUG: dump_packet(send_data)

    def _execute_command(self, command, sql):
        self._send_command(command, sql)
        
    def _request_authentication(self):
        sock = self.socket
        self._send_authentication()

    def _send_authentication(self):
        sock = self.socket
        self.client_flag |= CLIENT_CAPABILITIES
        if self.server_version.startswith('5'):
            self.client_flag |= CLIENT_MULTI_RESULTS
    
        data = (struct.pack('i', self.client_flag)) + "\0\0\0\x01" + \
                '\x08' + '\0'*23 + \
                self.user+"\0" + _scramble(self.password, self.salt)
        
        if self.db:
            data += self.db + "\0"
        
        data = pack_int24(len(data)) + "\x01" + data
        
        if DEBUG: dump_packet(data)
        
        sock.send(data)

        auth_packet = MysqlPacket(sock)
        auth_packet.check_error()
        if DEBUG: auth_packet.dump()
        
    def _get_server_information(self):
        sock = self.socket
        i = 0
        data = sock.recv(BUFFER_SIZE)
        if DEBUG: dump_packet(data)
        packet_len = ord(data[i:i+1])
        i += 4
        self.protocol_version = ord(data[i:i+1])
        
        i += 1
        server_end = data.find("\0", i)
        self.server_version = data[i:server_end]
        
        i = server_end + 1
        self.server_thread_id = struct.unpack('h', data[i:i+2])
        self.thread_id = self.server_thread_id  # MySQLdb compatibility

        i += 4
        self.salt = data[i:i+8]
        
        i += 9
        if len(data) >= i + 1:
            i += 1
       
        self.sever_capabilities = struct.unpack('h', data[i:i+2])
        
        i += 1
        self.sever_language = ord(data[i:i+1])
        
        i += 16 
        if len(data) >= i+12-1:
            rest_salt = data[i:i+12]
            self.salt += rest_salt

    def get_server_info(self):
        return self.server_version

    Warning = Warning
    Error = Error
    InterfaceError = InterfaceError
    DatabaseError = DatabaseError
    DataError = DataError
    OperationalError = OperationalError
    IntegrityError = IntegrityError
    InternalError = InternalError
    ProgrammingError = ProgrammingError
    NotSupportedError = NotSupportedError

# TODO: move OK and EOF packet parsing/logic into a proper subclass
#       of MysqlPacket like has been done with FieldDescriptorPacket.
class MySQLResult(object):

    def __init__(self, connection):
        from weakref import proxy
        self.connection = proxy(connection)
        self.affected_rows = None
        self.insert_id = None
        self.server_status = 0
        self.warning_count = 0
        self.message = None
        self.field_count = 0
        self.description = None
        self.rows = None
        self.has_next = None

    def read(self):
        self.first_packet = self.connection.read_packet()

        # TODO: use classes for different packet types?
        if self.first_packet.is_ok_packet():
            self._read_ok_packet()
        else:
            self._read_result_packet()

    def _read_ok_packet(self):
        self.first_packet.advance(1)  # field_count (always '0')
        self.affected_rows = self.first_packet.read_coded_length()
        self.insert_id = self.first_packet.read_coded_length()
        self.server_status = struct.unpack('H', self.first_packet.read(2))[0]
        self.warning_count = struct.unpack('H', self.first_packet.read(2))[0]
        self.message = self.first_packet.read_all()

    def _read_result_packet(self):
        self.field_count = ord(self.first_packet.read(1))
        self._get_descriptions()
        self._read_rowdata_packet()

    # TODO: implement this as an iteratable so that it is more
    #       memory efficient and lower-latency to client...
    def _read_rowdata_packet(self):
      """Read a rowdata packet for each data row in the result set."""
      rows = []
      while True:
        packet = self.connection.read_packet()
        if packet.is_eof_packet():
            self.warning_count = packet.read(2)
            server_status = struct.unpack('h', packet.read(2))[0]
            self.has_next = (server_status
                             & SERVER_STATUS.SERVER_MORE_RESULTS_EXISTS)
            break

        row = []
        for field in self.fields:
            converter = self.connection.decoders[field.type_code]
            if DEBUG: print "DEBUG: field=%s, converter=%s" % (field, converter)
            data = packet.read_length_coded_binary()
            converted = None
            if data != None:
              converted = converter(data)
            row.append(converted)

        rows.append(tuple(row))

      self.affected_rows = len(rows)
      self.rows = tuple(rows)
      if DEBUG: self.rows

    def _get_descriptions(self):
        """Read a column descriptor packet for each column in the result."""
        self.fields = []
        description = []
        for i in xrange(self.field_count):
            field = self.connection.read_packet(FieldDescriptorPacket)
            self.fields.append(field)
            description.append(field.description())

        eof_packet = self.connection.read_packet()
        assert eof_packet.is_eof_packet(), 'Protocol error, expecting EOF'
        self.description = tuple(description)
