import asyncio
import os
import subprocess
import time
import logging
from termcolor import cprint
import config

from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

logging.getLogger("meross_iot").setLevel(logging.ERROR)

async def async_switch_plug(device_uuid, on: True):
    http_api_client = await MerossHttpClient.async_from_user_password(email=config.email, password=config.password)
    manager = MerossManager(http_client=http_api_client)
    await manager.async_init()
    await manager.async_device_discovery()
    plugs = manager.find_devices(device_uuids=[device_uuid])

    if len(plugs) < 1:
        print("Plug not found")
        return

    plug = plugs[0]
    await plug.async_update()

    if plug.online_status == 'OFFLINE':
        print("Plug offline")

    if on:
        print("Turning on")
        await plug.async_turn_on()
    else:
        print("Turning off")
        await plug.async_turn_off()

    manager.close()
    await http_api_client.async_logout()


def shell(command):
    return subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')

def is_in_meeting():
    n_udp_connections = int(shell('/usr/sbin/lsof -i 4UDP | grep zoom.us | wc -l').strip())
    return n_udp_connections > 1


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    previously_in_meeting = None

    while True:
        if is_in_meeting():
            if previously_in_meeting == True:
                print("Still in meeting, leaving on")
            else:
                print("Meeting started! turning on")
                loop.run_until_complete(async_switch_plug(config.device_uuid, on=True))
                previously_in_meeting = True
        else:
            if previously_in_meeting == False:
                print("Still not in meeting, leaving off")
            else:
                print("Meeting ended, turning off")
                loop.run_until_complete(async_switch_plug(config.device_uuid, on=False))
                previously_in_meeting = False

        time.sleep(10)

    