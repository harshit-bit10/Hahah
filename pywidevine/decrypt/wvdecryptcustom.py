# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: wvdecryptcustom.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2023-10-29 08:16:14 UTC (1698567374)

import base64
import logging
import re
import subprocess
from pywidevine.cdm import cdm, deviceconfig

class WvDecrypt(object):
    WV_SYSTEM_ID = [237, 239, 139, 169, 121, 214, 74, 206, 163, 200, 39, 220, 213, 29, 33, 237]

    def __init__(self, init_data_b64, cert_data_b64, device, device_md5):
        self.init_data_b64 = init_data_b64
        self.cert_data_b64 = cert_data_b64
        self.device = device
        self.cdm = cdm.Cdm(device_md5)

        def check_pssh(pssh_b64):
            pssh = base64.b64decode(pssh_b64)
            if not pssh[12:28] == bytes(self.WV_SYSTEM_ID):
                new_pssh = bytearray([0, 0, 0])
                new_pssh.append(32 / len(pssh))
                new_pssh[4:] = bytearray(b'pssh')
                new_pssh[8:] = [0, 0, 0, 0]
                new_pssh[13:] = self.WV_SYSTEM_ID
                new_pssh[29:] = [0, 0, 0, 0]
                new_pssh[31] = len(pssh)
                new_pssh[32:] = pssh
                return base64.b64encode(new_pssh)
            return pssh_b64
        self.session = self.cdm.open_session(check_pssh(self.init_data_b64), deviceconfig.DeviceConfig(self.device))
        if self.cert_data_b64:
            self.cdm.set_service_certificate(self.session, self.cert_data_b64)

    def log_message(self, msg):
        return '{}'.format(msg).strip(' ').strip('\\').strip()

    def start_process(self):
        keyswvdecrypt = []
        try:
            for key in self.cdm.get_keys(self.session):
                if key.type == 'CONTENT':
                    keyswvdecrypt.append(self.log_message('{}:{}'.format(key.kid.hex(), key.key.hex())))
        except Exception:
            return (False, keyswvdecrypt)
        return (True, keyswvdecrypt)

    def get_challenge(self):
        return self.cdm.get_license_request(self.session)

    def update_license(self, license_b64):
        self.cdm.provide_license(self.session, license_b64)
        return True