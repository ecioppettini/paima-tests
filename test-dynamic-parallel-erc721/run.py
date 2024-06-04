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

    # block 1
    setNextTimestamp(baseTimestamp + 2)

    paima_l2 = deployPaimaContract()
    mineEmptyBlock(baseTimestamp + 1, port=8546)

    print(f"Paima L2 Contract deployed to: {paima_l2}")

    # block 2
    mineEmptyBlock(baseTimestamp + 3)

    setNextTimestamp(baseTimestamp + 2, port=8546)
    dynamicContract = deployDynamicContract(port=8546)

    # block 3
    setNextTimestamp(baseTimestamp + 3, port=8546)

    erc721 = deployMyErc721(port=8546)

    # block 4
    setNextTimestamp(baseTimestamp + 4)
    erc721_2 = deployMyErc721(port=8546)

    print(f"Deployed ERC721: {erc721}")
    print(f"Deployed ERC721: {erc721_2}")

    # block 5
    setAutomine(False, port=8546)

    # setNextTimestamp(baseTimestamp + 5, port=8546)
    triggerDynamicEvent(dynamicContract, erc721, port=8546, user=USER2)
    triggerDynamicEvent(dynamicContract, erc721_2, port=8546, user=USER3)

    transferErc721(erc721, USER, TARGET, 4, isAsync=True, port=8546)

    mineBlock(baseTimestamp + 5, port=8546)

    setAutomine(True, port=8546)

    ###### Impersonate accounts

    impersonateAccount(USER)

    # Start the main chain process

    # block 6
    mineEmptyBlock(baseTimestamp + 7, port=8545)
    mineEmptyBlock(baseTimestamp + 6, port=8546)

    # block 7
    mineEmptyBlock(baseTimestamp + 8, port=8545)
    mineEmptyBlock(baseTimestamp + 7, port=8546)

    # block 8
    mineEmptyBlock(baseTimestamp + 9, port=8545)

    setNextTimestamp(baseTimestamp + 8, port=8546)
    transferErc721(erc721, USER, TARGET, 2, port=8546)

    # block 9
    mineEmptyBlock(baseTimestamp + 10, port=8545)
    mineEmptyBlock(baseTimestamp + 9, port=8546)

    # block 10
    mineEmptyBlock(baseTimestamp + 11)

    setNextTimestamp(baseTimestamp + 10, port=8546)
    transferErc721(erc721, USER, TARGET, 3, port=8546)

    # block 11
    mineEmptyBlock(baseTimestamp + 12, port=8545)
    mineEmptyBlock(baseTimestamp + 13, port=8546)

    NETWORK = "localhost"

    print("Starting Paima Engine")

    tmpfile = tempfile.mktemp()

    os.environ["NETWORK"] = "localhost"

    shutil.copytree(root_path / "packaged", "packaged", dirs_exist_ok=True)

    # subprocess.run([root_path / "paima-engine-linux", "run"])

    def runEngine():
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

    runEngine()

    # Set environment variables for PostgreSQL
    os.environ["PGDATABASE"] = "postgres"
    os.environ["PGUSER"] = "postgres"
    os.environ["PGPASSWORD"] = "postgres"
    os.environ["PGHOST"] = "localhost"
    os.environ["PGPORT"] = "5440"

    subprocess.run(
        "psql -c 'SELECT * FROM cde_erc721_data;'", shell=True
    )

    subprocess.run(
        "psql -c 'SELECT * FROM cde_erc721_burn;'", shell=True
    )

    subprocess.run(
        "psql -c 'SELECT * FROM scheduled_data;'", shell=True
    )

    subprocess.run(
        "psql -c 'SELECT * FROM cde_dynamic_primitive_config;'", shell=True
    )

    subprocess.run(
        "psql -c 'SELECT * FROM chain_data_extensions;'", shell=True
    )

    print("")
    print("                            \033[1;32mSuccess\033[0m")
    print("")

    runEngine()


with Anvil(0), Anvil(0, port=8546), PaimaDb():
    main()
