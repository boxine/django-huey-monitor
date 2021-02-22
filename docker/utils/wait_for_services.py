#!/usr/bin/env python3

import math
import os
import socket
import sys
import time


TIMEOUT = 10


def tcp_test(service_name, host_key, port_key, timeout=TIMEOUT):
    host = os.environ[host_key]
    port = int(os.environ[port_key])
    print(f'\nWait for {service_name} ({host}:{port}) with timeout: {timeout} sec.')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                s.connect((host, port))
            except Exception as err:
                max_wait = math.ceil(timeout - (time.time() - start_time))
                print(f'wait {max_wait} sec. for {service_name}... {err}')
                time.sleep(1)
            else:
                print(f'{service_name} available, ok.')
                return

    print(f'Error {service_name} not available!')
    sys.exit(1)


if __name__ == '__main__':
    tcp_test('postgres', host_key='DB_HOST', port_key='DB_PORT')
    tcp_test('redis', host_key='REDIS_HOST', port_key='REDIS_PORT')
