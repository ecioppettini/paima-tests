#!/usr/bin/python3

import os
import subprocess
import time
import tempfile
import shutil
import sys
from pathlib import Path

directory = Path(__file__).resolve()
sys.path.append(str(directory.parent.parent))
from setup import (
    setNextTimestamp,
    mineEmptyBlock,
    impersonateAccount,
    deployErc20,
    Anvil,
    PaimaDb,
    USER,
    TARGET,
    TARGET2,
    deployPaimaContract,
    transferErc20,
    lastBlock,
)

script_path = Path(__file__).resolve()
root_path = script_path.parent.parent


def main():
    delay = 5
    baseTimestamp = 10
    chain1BaseTimestamp = baseTimestamp + delay

    setNextTimestamp(baseTimestamp + 1, port=8545)

    # block 1
    paima_l2 = deployPaimaContract()

    # block 2
    mineEmptyBlock(chain1BaseTimestamp + 2, port=8545)
    # block 3
    mineEmptyBlock(chain1BaseTimestamp + 3, port=8545)
    # block 4
    mineEmptyBlock(chain1BaseTimestamp + 4, port=8545)
    # block 5
    mineEmptyBlock(chain1BaseTimestamp + 5, port=8545)
    # block 6
    mineEmptyBlock(chain1BaseTimestamp + 6, port=8545)
    # block 7
    mineEmptyBlock(chain1BaseTimestamp + 7, port=8545)

    print(f"Paima L2 Contract deployed to: {paima_l2}")

    # chain 2
    baseTimestamp = baseTimestamp
    setNextTimestamp(baseTimestamp + 1 + 1, port=8546)

    # Impersonate accounts

    impersonateAccount(USER, port=8546)

    # block 1
    token = deployErc20(port=8546)

    print(f"Deployed ERC20: {token}")

    # block 3
    mineEmptyBlock(baseTimestamp + 2 + 1, port=8546)

    # block 3
    mineEmptyBlock(baseTimestamp + 3 + 1, port=8546)

    # block 4 (merged to 5)
    setNextTimestamp(baseTimestamp + 4 + 1, port=8546)
    transferErc20(token, TARGET, 3, port=8546)

    # block 5 (merged to 6)
    mineEmptyBlock(baseTimestamp + 5 + 1, port=8546)

    # block 6 (merged to 7)
    setNextTimestamp(baseTimestamp + 6 + 1 + 1, port=8546)
    transferErc20(token, TARGET2, 100, port=8546)

    # block 7
    mineEmptyBlock(baseTimestamp + 7 + 1 + 1, port=8546)

    # setNextTimestamp(baseTimestamp + 5)

    # burnErc721(token, 0)

    # setNextTimestamp(baseTimestamp + 6)

    # burnErc721(token, 1)

    # setNextTimestamp(baseTimestamp + 7)

    # transferErc721(token, USER, TARGET, 2)

    # # block 5
    # mineEmptyBlock(baseTimestamp + 8)

    NETWORK = "localhost"

    print("Starting Paima Engine")

    tmpfile = tempfile.mktemp()

    os.environ["NETWORK"] = "localhost"

    shutil.copytree(root_path / "packaged", "packaged", dirs_exist_ok=True)

    # exit(0)

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
    os.environ["PGPORT"] = "5440"

    subprocess.run("psql -c 'SELECT * FROM cde_erc20_data;'", shell=True)

    subprocess.run("psql -c 'SELECT * FROM scheduled_data;'", shell=True)

    print("")
    print("                            \033[1;32mSuccess\033[0m")
    print("")


with Anvil(0, port=8545, chainId=31337), Anvil(0, port=8546, chainId=31338):
    with PaimaDb():
        main()
