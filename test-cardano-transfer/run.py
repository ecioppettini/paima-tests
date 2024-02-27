#!/usr/bin/python3

import os
import subprocess
import time
import tempfile
import shutil
import threading
from pathlib import Path
from run_server import main as run_server

script_path = Path(__file__).resolve()
root_path = script_path.parent.parent

# Set initial timestamp
BASE_TIMESTAMP = 1679128974

USER = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
TARGET = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"

ANVIL = None


def startAnvil():
    anvil = subprocess.Popen(
        ["anvil", "--port", "8545", "--chain-id", "31337", "--timestamp", timestamp(1)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )

    time.sleep(2)

    if anvil.poll() is not None:
        raise RuntimeError("Couldn't start anvil")
    else:
        print("Network deployed")

    return anvil


def timestamp(offset):
    return str(BASE_TIMESTAMP + offset)


def setNextTimestamp(ts):
    status = subprocess.run(
        [
            "cast",
            "rpc",
            "evm_setNextBlockTimestamp",
            ts,
            "--rpc-url",
            "http://localhost:8545",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    if status.returncode != 0:
        raise RuntimeError("failed to set next block timestamp")


def mineBlockWithErcTransfer(ts, token):
    setNextTimestamp(ts)

    status = subprocess.run(
        [
            "cast",
            "send",
            token,
            "--unlocked",
            "--from",
            USER,
            "transfer(address,uint256)",
            TARGET,
            "1",
            "--rpc-url",
            "http://localhost:8545",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    if status.returncode != 0:
        raise RuntimeError("failed to make erc20 transfer")


def impersonateAccount(user):
    subprocess.run(
        [
            "cast",
            "rpc",
            "anvil_impersonateAccount",
            user,
            "--rpc-url",
            "http://localhost:8545",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def mineEmptyBlock(ts):
    setNextTimestamp(ts)

    subprocess.run(
        ["cast", "rpc", "evm_mine", "--rpc-url", "http://localhost:8545"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def deployPaimaContract():
    print("Deploying Paima L2 Contract")

    subprocess.run(
        [
            "forge",
            "install",
            "openzeppelin/openzeppelin-contracts@v4.9.5",
            "--no-commit",
        ],
        cwd=root_path,
    )

    result = subprocess.run(
        [
            "forge",
            "create",
            "--rpc-url",
            "http://localhost:8545",
            "--private-key",
            "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
            "PaimaL2Contract.sol:PaimaL2Contract",
            "--constructor-args",
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "0",
            "--root",
            ".",
            "--contracts",
            ".",
            "--lib-paths",
            "../../lib",
            "--remappings",
            "@openzeppelin/contracts/=../../lib/openzeppelin-contracts/contracts",
        ],
        stdout=subprocess.PIPE,
        cwd=root_path / "contracts" / "evm-contracts",
        universal_newlines=True,
    )

    address = ""
    for line in result.stdout.split("\n"):
        if "Deployed to" in line:
            address = line.split(":")[1].strip().split(" ")[0]
            break

    return address


def deployMyErc20():
    result = subprocess.run(
        [
            "forge",
            "create",
            "--root",
            ".",
            "--rpc-url",
            "http://localhost:8545",
            "--private-key",
            "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
            "src/CustomErc20.sol:CustomERC20",
        ],
        stdout=subprocess.PIPE,
        universal_newlines=True,
        cwd=root_path / "my-erc20",
    )

    token = ""
    for line in result.stdout.split("\n"):
        if "Deployed to" in line:
            token = line.split(":")[1].strip().split(" ")[0]
            break

    print(f"Custom ERC20 deployed to: {token}")

    return token


def startDb():
    subprocess.run(
        ["npm", "run", "database:reset"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        cwd=root_path / "chess",
    )

    docker = subprocess.Popen(
        ["docker", "compose", "up"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        cwd=root_path / "chess" / "db" / "docker",
    )

    time.sleep(5)

    print(f"Docker db started")


def lastBlock():
    r = subprocess.run(
        # "cast block 'latest' --rpc-url http://localhost:8545 | rg 'timestamp' | awk -F' +' '{ print $2 }'",
        "cast block 'latest' --rpc-url http://localhost:8545",
        shell=True,
        capture_output=True,
        universal_newlines=True,
    )

    return r.stdout


def main():
    global ANVIL

    ANVIL = startAnvil()

    setNextTimestamp(timestamp(2))

    # block 1
    paima_l2 = deployPaimaContract()

    print(f"Paima L2 Contract deployed to: {paima_l2}")

    setNextTimestamp(timestamp(3))

    # block 2
    token = deployMyErc20()

    print(f"Deployed ERC20: {token}")

    ###### Impersonate accounts

    impersonateAccount(USER)

    # Start the main chain process

    # block 3
    mineEmptyBlock(timestamp(4))

    print(f"{token}")

    # block 4
    mineBlockWithErcTransfer(timestamp(61), token)

    lastBlock()

    # block 5
    mineBlockWithErcTransfer(timestamp(674), token)

    # block 6
    mineBlockWithErcTransfer(timestamp(821), token)

    # block 7
    mineBlockWithErcTransfer(timestamp(825), token)

    # End of main chain

    NETWORK = "localhost"

    startDb()

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
        "psql -c 'SELECT cde_id,tx_id FROM cde_cardano_transfer;'", shell=True
    )

    print("")
    print("                            \033[1;32mSuccess\033[0m")
    print("")


server = None

try:
    server = run_server(3000)
    main()

finally:
    subprocess.run(
        ["docker", "compose", "down"],
        cwd=root_path / "chess" / "db" / "docker",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    if ANVIL is not None:
        ANVIL.send_signal(subprocess.signal.SIGTERM)
        ANVIL.wait()

    if server is not None:
        server.shutdown()
        server.server_close()

    time.sleep(2)
