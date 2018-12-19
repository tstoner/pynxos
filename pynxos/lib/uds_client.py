import os
import json
import socket
import http.client

from builtins import range
from pynxos.errors import NXOSError

class UDSClient(http.client.HTTPConnection):

    """Subclass of Python library HTTPConnection that uses a unix-domain socket.
    """

    def __init__(self, path, username, url='/ins_local'):
        if not os.path.exists(path):
            raise NXOSError("\'%s\' does not exist." % path)

        if not username:
            raise NXOSError('\'username\' must not be None.')

        http.client.HTTPConnection.__init__(self, 'localhost')

        self.path = path
        self.headers = {'Cookie': 'nxapi_auth=' + username + ':local',
                        'content-type': 'application/json-rpc'}
        self.url = url

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock

    def _build_payload(self, commands, method, rpc_version=u'2.0'):
        payload_list = []

        id_num = 1
        for command in commands:
            payload = dict(jsonrpc=rpc_version,
                           method=method,
                           params=dict(cmd=command, version=1),
                           id=id_num)

            payload_list.append(payload)
            id_num += 1

        return payload_list

    def send_request(self, commands, method=u'cli', timeout=30):
        self.timeout = timeout
        payload_list = self._build_payload(commands, method)
        self.request('POST',
                     self.url,
                     json.dumps(payload_list),
                     self.headers)

        response = self.getresponse()

        try:
            response_list = json.loads(response.read())

            if isinstance(response_list, dict):
                response_list = [response_list]

            for i in range(len(commands)):
                response_list[i][u'command'] = commands[i]

        except http.client.IncompleteRead as e:
            response_list = []

        return response_list
