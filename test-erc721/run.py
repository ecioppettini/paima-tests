#!/usr/bin/python3

import os
import subprocess
import time
import tempfile
import shutil
import threading
import sys
from pathlib import Path

directory = Path(__file__).resolve()
sys.path.append(str(directory.parent.parent))
from setup import *

script_path = Path(__file__).resolve()
root_path = script_path.parent.parent

def main():
    baseTimestamp = 1

    setNextTimestamp(baseTimestamp + 1)

    # block 1
    paima_l2 = deployPaimaContract()

    print(f"Paima L2 Contract deployed to: {paima_l2}")

    setNextTimestamp(baseTimestamp + 2)

    # block 2
    token = deployMyErc721()

    print(f"Deployed ERC721: {token}")

    ###### Impersonate accounts

    impersonateAccount(USER)

    # Start the main chain process

    # block 3
    mineEmptyBlock(baseTimestamp + 3)

    # block 4

    mineEmptyBlock(baseTimestamp + 4)

    setNextTimestamp(baseTimestamp + 5)

    burnErc721(token, 0)

    setNextTimestamp(baseTimestamp + 6)

    burnErc721(token, 1)

    setNextTimestamp(baseTimestamp + 7)

    transferErc721(token, USER, TARGET, 2)

    # block 5
    mineEmptyBlock(baseTimestamp + 8)

    # # block 6
    # mineEmptyBlock(baseTimestamp + 6)

    # # block 7
    # mineEmptyBlock(baseTimestamp + 7)

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

    time.sleep(15)

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
        "psql -c 'SELECT * FROM cde_erc721_data;'", shell=True
    )

    subprocess.run(
        "psql -c 'SELECT * FROM cde_erc721_burn;'", shell=True
    )

    print("")
    print("                            \033[1;32mSuccess\033[0m")
    print("")


# local carp
# with Anvil(0), PaimaDb():
with Anvil(0), PaimaDb():
    main()
