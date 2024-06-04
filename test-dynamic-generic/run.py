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

# Set environment variables for PostgreSQL
os.environ["PGDATABASE"] = "postgres"
os.environ["PGUSER"] = "postgres"
os.environ["PGPASSWORD"] = "postgres"
os.environ["PGHOST"] = "localhost"
os.environ["PGPORT"] = "5440"

def main():
    baseTimestamp = 1

    setNextTimestamp(baseTimestamp + 1)

    # block 1
    paima_l2 = deployPaimaContract()

    print(f"Paima L2 Contract deployed to: {paima_l2}")

    # block 2
    setNextTimestamp(baseTimestamp + 2)
    dynamicContract = deployDynamicContract()

    # block 3
    setNextTimestamp(baseTimestamp + 3)
    erc721 = deployMyErc721()

    setNextTimestamp(baseTimestamp + 4)
    erc20 = deployErc20();

    print(f"Deployed ERC721: {erc721}")

    # block 4
    setAutomine(False)

    triggerDynamicEvent(dynamicContract, erc721, user=USER3)

    transferErc721(erc721, USER, TARGET, 4, isAsync=True)

    # use a different user to a void nonce issues
    triggerDynamicEvent(dynamicContract, erc20, user=USER2)

    # setNextTimestamp(baseTimestamp + 4)
    mineBlock(baseTimestamp + 5)

    setAutomine(True)

    ###### Impersonate accounts

    impersonateAccount(USER)

    # Start the main chain process

    # block 5
    mineEmptyBlock(baseTimestamp + 6)

    # block 5
    mineEmptyBlock(baseTimestamp + 7)

    # print(getLogs(erc721))

    # block 7
    setNextTimestamp(baseTimestamp + 8)
    transferErc721(erc721, USER, TARGET, 2)

    # print(getLogs(erc721))

    # block 8
    setNextTimestamp(baseTimestamp + 9)
    burnErc721(erc721, 1)


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

    # block 9
    setNextTimestamp(baseTimestamp + 10)
    transferErc721(erc721, USER, TARGET, 3)

    # print(getLogs(erc721))

    # block 10
    mineEmptyBlock(baseTimestamp + 11)

    print("cde_erc721_data")
    subprocess.run("psql -c 'SELECT * FROM cde_erc721_data;'", shell=True)

    print("cde_erc721_burn")
    subprocess.run("psql -c 'SELECT * FROM cde_erc721_burn;'", shell=True)

    print("scheduled_data")
    subprocess.run("psql -c 'SELECT * FROM scheduled_data;'", shell=True)

    print("cde_dynamic_primitive_config")
    subprocess.run("psql -c 'SELECT * FROM cde_dynamic_primitive_config;'", shell=True)

    print("chain_data_extensions")
    subprocess.run("psql -c 'SELECT * FROM chain_data_extensions;'", shell=True)

    subprocess.run("npm run main", cwd="./db-client", shell=True);

    print("")
    print("                            \033[1;32mSuccess\033[0m")
    print("")

    runEngine()


with Anvil(0), PaimaDb():
    main()
