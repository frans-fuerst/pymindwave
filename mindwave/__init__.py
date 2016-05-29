import enum
import serial
import time
import threading
import logging

LOG = logging.getLogger('pymindwave')

class device_error(Exception):
    pass

class request_denied(Exception):
    pass

class checksum_mismatch(Exception):
    pass

class wrong_token_error(Exception):
    pass

class _token(enum.Enum):
    POOR_SIGNAL          = b'\x02'
    ATTENTION            = b'\x04'
    MEDITATION           = b'\x05'
    BLINK                = b'\x16'
    EXCODE               = b'\x55'

    RAW_VALUE            = b'\x80'
    NOT_KNOWN            = b'\x83'

    SYNC                 = b'\xaa'
    CONNECT              = b'\xc0'
    DISCONNECT           = b'\xc1'
    AUTOCONNECT          = b'\xc2'
    HEADSET_CONNECTED    = b'\xd0'
    HEADSET_NOT_FOUND    = b'\xd1'
    HEADSET_DISCONNECTED = b'\xd2'
    REQUEST_DENIED       = b'\xd3'
    STANDBY_SCAN         = b'\xd4'

class _status(enum.Enum):
    INVALID       = 0
    CONNECTED     = 1
    SCANNING      = 2
    STANDBY       = 3

class connection:
    def __init__(self, *, device: str, handler, speed: int=115200) -> None:
        ''' todo: doc '''
        self._conn = None
        self._handler_thread = None
        self._handler = handler
        self._current_state = { 'raw':       0,
                                'meditation': 0,
                                'attention': 0,
                                }

        for _ in range(3):
            try:
                self._setup_connection(device, speed)
                break
            except wrong_token_error:
                pass

    @staticmethod
    def _read_byte(serial_connection) -> int:
        ''' todo: doc '''
        return ord(serial_connection.read())

    @staticmethod
    def _read(serial_connection) -> bytes:
        ''' todo: doc '''
        _length = connection._read_byte(serial_connection)
        _data = serial_connection.read(_length)
        _checksum_exp = ~(sum(_data) & 0xff) & 0xff
        _checksum = ord(serial_connection.read())
        if not _checksum_exp == _checksum:
            LOG.warning('checksum mismatch!')
            for b in _data:
                LOG.debug('  0x%x (%s)', b, connection._to_name(b))
        return _data

    @staticmethod
    def _to_name(token_value: int) -> str:
        ''' todo: doc '''
        try:
            return _token(bytes([token_value])).name
        except ValueError:
            return 'unknown'

    @staticmethod
    def _to_hex(data: bytes) -> str:
        if data is None:
            return ''
        return ' '.join('{:02x}'.format(b) for b in data)

    @staticmethod
    def _assert_token(data: int, expected_token):
        ''' todo: doc '''
        if not data == ord(expected_token.value):
            _name = connection._to_name(data)
            if data == ord(_token.REQUEST_DENIED.value):
                raise request_denied()

            raise wrong_token_error(
                'expected token 0x%x (%s) but was 0x%x (%s)'
                % (ord(expected_token.value), expected_token.name, data, _name))

    def _setup_connection(self, device: str, speed: int):
        ''' todo: doc '''
        try:
            self._conn = serial.Serial(device, speed)
        except serial.SerialException as ex:
            if ex.errno == 2:
                raise device_error("there's no device '%s'" % device)
            raise

        self.disconnect()
        self._conn.flush()

        # todo: refactor
        _conn_settings = self._conn.getSettingsDict()
        for _ in range(2):
            _conn_settings['rtscts'] = not _conn_settings['rtscts']
            self._conn.applySettingsDict(_conn_settings)

        connection._assert_token(connection._read_byte(self._conn), _token.SYNC)
        self._handler_thread = threading.Thread(target=self._handler_thread_fn, daemon=True)
        self._handler_thread.start()
        LOG.debug('ready')

    def _handler_thread_fn(self):
        ''' todo: doc '''

        def _check_sync() -> bool:
            ''' check for two SYNC tokens '''
            for _ in range(2):
                if connection._read_byte(self._conn) != ord(_token.SYNC.value):
                    return False
            return True

        self._handler.on_setup()

        while True:
            if not _check_sync():
                LOG.debug('out of sync')
                continue

            self._handle_data(connection._read(self._conn))

    def _handle_data(self, data: bytes):
        # LOG.debug('got data: %d [%s]', len(data), connection._to_hex(data))
        while len(data) > 0:
            try:
                _opcode = _token(bytes([data[0]]))
            except ValueError:
                LOG.warning('got unknown opcode (%x)! dismiss %d bytes of data',
                            data[0], len(data))
                return

            if _opcode in (_token.SYNC, _token.EXCODE, _token.REQUEST_DENIED):
                data = data[1:]
                continue

            if ord(_opcode.value) < 0x80:
                _extra, data = data[1:2], data[2:]
            else:
                _l = data[1]
                _extra, data = data[2:2 + _l], data[2 + _l:]

            self._handle_opcode(_opcode, _extra)

    def _update(self, name: str, value) -> None:
        self._current_state[name] = value
        self._current_state['time'] = time.time()
        self._handler.on_update(self._current_state)

    def _handle_opcode(self, opcode, data: bytes):
        if opcode == _token.RAW_VALUE:
            if len(data) != 2:
                return
            _raw = (data[0] << 8) + data[1]
            if _raw >= 32768:
                _raw -= 65536
            _raw /= 32768.
            self._update('raw', _raw)

            #LOG.debug("RAW_VALUE %s", connection._to_hex(data))
        elif opcode == _token.ATTENTION:
            self._update('attention', data[0])

        elif opcode == _token.MEDITATION:
            self._update('meditation', data[0])

        elif opcode == _token.STANDBY_SCAN:
            LOG.debug("STANDBY_SCAN %s", connection._to_hex(data))
        else:
            LOG.debug("%s: %s", opcode.name, connection._to_hex(data))

    def connect(self, headset_id: int):
        ''' todo: doc '''
        assert False, 'not implemented'
        LOG.debug('send connect')
        res = self._conn.write(''.join([_token.AUTOCONNECT.value, headset_id]))
        LOG.debug('connect() : write returned %s', str(res))
        return res

    def autoconnect(self):
        ''' todo: doc '''
        LOG.debug('send auto-connect')
        self._conn.write(_token.AUTOCONNECT.value)

    def disconnect(self):
        ''' todo: doc '''
        LOG.debug('send disconnect')
        self._conn.write(_token.DISCONNECT.value)


