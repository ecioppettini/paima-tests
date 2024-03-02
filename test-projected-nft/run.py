#!/usr/bin/python3

import os
import subprocess
import time
import tempfile
import shutil
import threading
import sys
from pathlib import Path

# TODO: rename file
from carp_data import output as output

directory = Path(__file__).resolve()
sys.path.append(str(directory.parent.parent))
from setup import *
from carp_mock import carp_mock

script_path = Path(__file__).resolve()
root_path = script_path.parent.parent


def timestampForEvent(index):
    ts = output[index]["payload"][0]["actionSlot"] + 1666656000 + 200

    return ts



def main():
    baseTimestamp = timestampForEvent(1) - 100

    setNextTimestamp(baseTimestamp + 1)

    # block 1
    paima_l2 = deployPaimaContract()

    print(f"Paima L2 Contract deployed to: {paima_l2}")

    setNextTimestamp(baseTimestamp + 2)

    # block 2
    token = deployMyErc20()

    print(f"Deployed ERC20: {token}")

    ###### Impersonate accounts

    impersonateAccount(USER)

    # Start the main chain process

    # block 3
    mineEmptyBlock(timestampForEvent(1) + 1)

    # block 4

    mineEmptyBlock(timestampForEvent(2) + 2)

    # block 5
    mineEmptyBlock(timestampForEvent(2) + 3)

    # block 6
    mineEmptyBlock(timestampForEvent(2) + 4)

    # block 7
    mineEmptyBlock(timestampForEvent(2) + 5)

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
    os.environ["PGPORT"] = "5432"

    subprocess.run(
        "psql -c 'SELECT * FROM cde_cardano_projected_nft;'", shell=True
    )

    print("")
    print("                            \033[1;32mSuccess\033[0m")
    print("")


def server():
    return carp_mock(
        3000,
        output,
        "/projected-nft/range",
        getSlot=lambda x: x["payload"][0]["actionSlot"],
        getTxHash=lambda x: x["txId"],
        mapResult=lambda x: x,
    )


# local carp
# with Anvil(0), PaimaDb():
with server(), Anvil(0), PaimaDb():
    main()
