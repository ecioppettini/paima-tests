#!/usr/bin/python3

import os
import subprocess
import time
import tempfile
import shutil
import sys
import requests
import math
import json
from pathlib import Path
from functools import reduce

directory = Path(__file__).resolve()
sys.path.append(str(directory.parent.parent))

script_path = Path(__file__).resolve()
root_path = script_path.parent.parent
from setup import *

# Set environment variables for PostgreSQL
os.environ["PGDATABASE"] = "postgres"
os.environ["PGUSER"] = "postgres"
os.environ["PGPASSWORD"] = "postgres"
os.environ["PGHOST"] = "localhost"
os.environ["PGPORT"] = "5440"


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
        ["zk", "lightnet", "start", "--sync", "false"],
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
        cwd="zkapp",
    )

    if status.returncode != 0:
        print(status.stdout)
        print(status.stderr)
        raise RuntimeError("failed to setup zkapp")

def isLightnetRunning():
    status = subprocess.run(
        [
            "zk",
            "lightnet",
            "status",
        ],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )

    print(status.returncode)

    return status.returncode == 0



def getEvents(status):
    url = "http://localhost:8282"
    data = {
        "query": """{{
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
        }}""".format(
            status=status
        )
    }

    response = requests.post(url, data=data)

    return response.json()["data"]["events"]


def getActions(status):
    url = "http://localhost:8282"
    data = {
        "query": """{{
        actions(
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
                actionData {{
                    data
                }}
            }}
        }}""".format(
            status=status
        )
    }

    response = requests.post(url, data=data)

    return response.json()["data"]["actions"]


def main():
    shutil.copytree(root_path / "packaged", "packaged", dirs_exist_ok=True)

    if not isLightnetRunning():
        setupLightnet()
        setupApp()

        while True:
            events = getEvents("CANONICAL")

            if len(events) == 4:
                time.sleep(25)
                break

            time.sleep(20)

    events = getEvents("CANONICAL")
    allEvents = getEvents("ALL")

    # print(len(events))

    if len(events) != len(allEvents):
        print(len(events), len(allEvents))
        raise RuntimeError("not all events are canonical yet")

    # print(events)

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
    mineEmptyBlock(tss[1] + 2)

    # block 4
    mineEmptyBlock(tss[1] + 3)
    # mineEmptyBlock(timestamp(61))

    # block 5
    mineEmptyBlock(tss[1] + 4)
    # mineEmptyBlock(timestamp(674))

    # block 6
    mineEmptyBlock(tss[2] + 1)

    # block 7
    mineEmptyBlock(tss[2] + 2)

    runEngine()

    # block 7
    mineEmptyBlock(tss[3] + 1)

    # End of main chain

    NETWORK = "localhost"

    # subprocess.run([root_path / "paima-engine-linux", "run"])

    for i in range(2):
        runEngine()

        e = subprocess.run(
            [
                "psql",
                "-t",
                "-c",
                "SELECT event_data FROM cde_generic_data WHERE cde_id = 0 ORDER BY block_height;",
            ],
            capture_output=True,
            universal_newlines=True,
        )

        a = subprocess.run(
            [
                "psql",
                "-t",
                "-c",
                "SELECT event_data FROM cde_generic_data WHERE cde_id = 1 ORDER BY block_height;",
            ],
            capture_output=True,
            universal_newlines=True,
        )

        eventsFromDb = [
            sorted(json.loads(r.strip())["data"]) for r in e.stdout.split("\n")[0:-2]
        ]
        actionsFromDb = [
            sorted(json.loads(r.strip())["data"]) for r in a.stdout.split("\n")[0:-2]
        ]

        events = list(
            map(
                lambda x: sorted(list(map(lambda y: y["data"], x["eventData"]))),
                getEvents("ALL"),
            )
        )

        actions = list(
            map(
                lambda x: sorted(list(map(lambda y: y["data"], x["actionData"]))),
                getActions("ALL"),
            )
        )

        if events != eventsFromDb:
            raise RuntimeError("events assertion failed")

        if actions != actionsFromDb:
            raise RuntimeError("actions assertion failed")

        # print(eventsFromDb)
        # print(events)

        # print("-------------------------------------------")

        # print(actions)
        # print(actionsFromDb)

    print("")
    print("                            \033[1;32mSuccess\033[0m")
    print("")


def runEngine():
    print("Starting Paima Engine")

    os.environ["NETWORK"] = "localhost"

    tmpfile = tempfile.mktemp()

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

    print("events")

    subprocess.run(
        "psql -c 'SELECT * FROM cde_generic_data WHERE cde_id = 0 ORDER BY block_height;'",
        shell=True,
    )

    print("-" * 80)
    print("actions")
    print("-" * 80)

    subprocess.run(
        "psql -c 'SELECT * FROM cde_generic_data WHERE cde_id = 1 ORDER BY block_height;'",
        shell=True,
    )

    print("-" * 80)
    print("cursors")
    print("-" * 80)

    subprocess.run(
        "psql -c 'SELECT * FROM cde_tracking_cursor_pagination;'",
        shell=True,
    )

    print("-" * 80)
    print("checkpoints")
    print("-" * 80)

    subprocess.run(
        "psql -c 'SELECT * FROM mina_checkpoint;'",
        shell=True,
    )


with Anvil(0), PaimaDb():
    main()
