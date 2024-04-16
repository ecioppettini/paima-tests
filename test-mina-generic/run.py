#!/usr/bin/python3

import os
import subprocess
import time
import tempfile
import shutil
import sys
import requests
import math
from pathlib import Path

directory = Path(__file__).resolve()
sys.path.append(str(directory.parent.parent))

script_path = Path(__file__).resolve()
root_path = script_path.parent.parent
from setup import *


def setupLightnet():
    # status = subprocess.run(
    #     [
    #         "zk",
    #         "lightnet",
    #         "stop",
    #     ],
    #     stdout=subprocess.DEVNULL,
    #     stderr=subprocess.STDOUT,
    # )

    status = subprocess.run(
        [
            "zk",
            "lightnet",
            "start",
            "--sync",
            "false"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    if status.returncode != 0:
        raise RuntimeError("failed to setup lightnet")

    while True:
        status = subprocess.run(
            [
                "zk",
                "lightnet",
                "status",
            ],
            stdout=subprocess.PIPE,
            cwd=root_path / "contracts" / "evm-contracts",
            universal_newlines=True,
        )

        if status.returncode != 0:
            raise RuntimeError("failed to get lightnet status")

        for line in status.stdout.split("\n"):
            if "SYNCED" in line:
                print("setup lightnet")
                return

        time.sleep(5)


def setupApp():
    status = subprocess.run(
        [
            "npm",
            "run",
            "main",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        cwd="zkapp"
    )

    if status.returncode != 0:
        print(status.stdout)
        print(status.stderr)
        raise RuntimeError("failed to setup zkapp")


def getEvents(status):
    url = 'http://localhost:8282'
    data = {'query': """{{
        events(
            input: {{
                address:"B62qoP3xe9zZJmBDacZPL8roBivpVKhAiDNtpAM9RCAW579JnJo1ZL2",
                status: {status}
            }}
        )
            {{
                blockInfo  {{
                    stateHash
                    timestamp
                }}
                eventData {{
                    data
                }}
            }}
        }}""".format(status=status)}

    response = requests.post(url, data=data)

    return response.json()['data']['events']


def main():
    # setupLightnet()

    # setupApp()

    events = getEvents("CANONICAL")
    allEvents = getEvents("ALL")

    if len(events) != len(allEvents):
        print(len(events), len(allEvents))
        raise RuntimeError("not all events are canonical yet")

    print(events)

    # print(events)

    def getTs(x):
        return x["blockInfo"]["timestamp"]

    tss = [math.trunc(int(ts) / 1000 + 30 * 20) for ts in map(getTs, events)]

    print(tss)
    print(len(tss))
    
    baseTimestamp = tss[0]

    setNextTimestamp(baseTimestamp + 1)

    # block 1
    paima_l2 = deployPaimaContract()

    # raise RuntimeError("please exit")
    

    print(f"Paima L2 Contract deployed to: {paima_l2}")

    # block 2
    mineEmptyBlock(baseTimestamp + 2)

    ###### Impersonate accounts

    impersonateAccount(USER)

    # Start the main chain process

    # block 3
    mineEmptyBlock(tss[1] + 1)

    # block 4

    mineEmptyBlock(tss[1] + 2)
    # mineEmptyBlock(timestamp(61))

    # block 5
    mineEmptyBlock(tss[1] + 3)
    # mineEmptyBlock(timestamp(674))

    # block 6
    mineEmptyBlock(tss[2] + 1)

    # block 7
    mineEmptyBlock(tss[2] + 2)

    # block 7
    mineEmptyBlock(tss[3] + 1)

    # End of main chain

    NETWORK = "localhost"

    print("Starting Paima Engine")

    tmpfile = tempfile.mktemp()

    os.environ["NETWORK"] = "localhost"

    shutil.copytree(root_path / "packaged", "packaged", dirs_exist_ok=True)

    # subprocess.run([root_path / "paima-engine-linux", "run"])

    paima_process = subprocess.Popen(
        [root_path / "paima-engine-linux", "run"],
        stdout=open(tmpfile, "w"),
        stderr=subprocess.STDOUT,
    )

    time.sleep(5)

    paima_process.send_signal(subprocess.signal.SIGKILL)
    paima_process.wait()

    print("Logs")

    with open(tmpfile, "r") as file:
        print(file.read())

    # Set environment variables for PostgreSQL
    os.environ["PGDATABASE"] = "postgres"
    os.environ["PGUSER"] = "postgres"
    os.environ["PGPASSWORD"] = "postgres"
    os.environ["PGHOST"] = "localhost"
    os.environ["PGPORT"] = "5440"

    subprocess.run(
        "psql -c 'SELECT * FROM cde_generic_data ORDER BY block_height;'", shell=True
    )

    print("")
    print("                            \033[1;32mSuccess\033[0m")
    print("")



with Anvil(0), PaimaDb():
    main()
