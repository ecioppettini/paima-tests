#!/usr/bin/python3

import os
import subprocess
import time
import tempfile
import shutil
import threading
from pathlib import Path

script_path = Path(__file__).resolve()
root_path = script_path.parent

USER = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
TARGET = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"

class Anvil:
    def __init__(self, ts):
        self.ts = ts

    def __enter__(self):
        anvil = subprocess.Popen(
            ["anvil", "--port", "8545", "--chain-id", "31337", "--timestamp", str(self.ts)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            text=True,
        )
   
        time.sleep(2)

        if anvil.poll() is not None:
            raise RuntimeError("Couldn't start anvil")
        else:
            print("Network deployed")

        self.process = anvil

    def __exit__(self, *args):
        if self.process is not None:
            self.process.send_signal(subprocess.signal.SIGTERM)
            self.process.wait()
    

def setNextTimestamp(ts):
    status = subprocess.run(
        [
            "cast",
            "rpc",
            "evm_setNextBlockTimestamp",
            str(ts),
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
            "openzeppelin/openzeppelin-contracts@v5.0.2",
            "--no-commit",
        ],
        cwd=root_path,
    )

    subprocess.run(
        [
            "forge",
            "install",
            "openzeppelin/openzeppelin-contracts-upgradeable@v5.0.2",
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
            "--remappings",
            "@openzeppelin/contracts-upgradeable/=../../lib/openzeppelin-contracts-upgradeable/contracts",
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

def deployMyErc721():
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
            "src/CustomErc721.sol:CustomErc721",
        ],
        stdout=subprocess.PIPE,
        universal_newlines=True,
        cwd=root_path / "my-erc721",
    )

    token = ""
    for line in result.stdout.split("\n"):
        if "Deployed to" in line:
            token = line.split(":")[1].strip().split(" ")[0]
            break

    print(f"Custom ERC721 deployed to: {token}")

    return token


def transferErc721(contractAddress, fro, to, tokenId):
    result = subprocess.run(
        [
            "cast",
            "send",
            str(contractAddress),
            "--unlocked",
            "--from",
            USER,
            "--rpc-url",
            "http://localhost:8545",
            "transferFrom(address, address, uint256)",
            fro,
            to,
            str(tokenId)
        ],
        cwd=root_path,
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )

    result.check_returncode()

def burnErc721(contractAddress, tokenId):
    result = subprocess.run(
        [
            "cast",
            "send",
            str(contractAddress),
            "--unlocked",
            "--from",
            USER,
            "--rpc-url",
            "http://localhost:8545",
            "burn(uint256)",
            str(tokenId)
        ],
        cwd=root_path,
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )

    result.check_returncode()

class PaimaDb:
    def __enter__(self):
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

    def __exit__(self, *args):
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=root_path / "chess" / "db" / "docker",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

        time.sleep(2)

def lastBlock():
    r = subprocess.run(
        # "cast block 'latest' --rpc-url http://localhost:8545 | rg 'timestamp' | awk -F' +' '{ print $2 }'",
        "cast block 'latest' --rpc-url http://localhost:8545",
        shell=True,
        capture_output=True,
        universal_newlines=True,
    )

    return r.stdout
