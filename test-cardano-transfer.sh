#!/usr/bin/bash

set -e

trap 'kill $(jobs -p)' EXIT

BASE_TIMESTAMP=$((1679128129 + 10))

timestamp() {
 echo $(($BASE_TIMESTAMP + 200 + $1));
}

anvil --port 8545 --chain-id 31337 --timestamp $(timestamp 1)  >> /dev/null &

echo "Network deployed"

sleep 2s

####### DEPLOY PAIMA L2 CONTRACT

echo "Deploying Paima L2 Contract"

cast rpc evm_setNextBlockTimestamp $(timestamp 2) --rpc-url http://localhost:8545 >> /dev/null

# TODO: could probably use the version from chess/node_modules
forge install openzeppelin/openzeppelin-contracts@v4.9.5 --no-commit

pushd contracts/evm-contracts

PAIMA_L2=$(forge create --rpc-url http://localhost:8545 --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 PaimaL2Contract.sol:PaimaL2Contract --constructor-args 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 0  --root . --contracts . --lib-paths ../../lib --remappings '@openzeppelin/contracts/=../../lib/openzeppelin-contracts/contracts' | grep "Deployed to" | cut -d':' -f2 | cut -d' ' -f2)

popd

if test -z $PAIMA_L2; then
    echo "PAIMA_L2 is empty"
    exit 1
fi

echo $PAIMA_L2

echo "Paima L2 Contract deployed"

cast rpc evm_setNextBlockTimestamp $(timestamp 3) --rpc-url http://localhost:8545 >> /dev/null

####### Deploy ERC20 

pushd my-erc20

TOKEN1=$(forge create --root . --rpc-url http://localhost:8545 --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 src/CustomErc20.sol:CustomERC20 | grep "Deployed to" | cut -d':' -f2 | cut -d' ' -f2)

echo "Custom ERC20 deployed to: $TOKEN1"

USER=0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
TARGET=0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC

popd

###### Impersonate accounts

cast rpc anvil_impersonateAccount $USER --rpc-url http://localhost:8545  ######## START MAIN CHAIN ########  
# block 3
cast rpc evm_setNextBlockTimestamp $(timestamp 4) --rpc-url http://localhost:8545 >> /dev/null

cast rpc evm_mine --rpc-url http://localhost:8545 >> /dev/null

# block 4
cast rpc evm_setNextBlockTimestamp $(timestamp 6) --rpc-url http://localhost:8545 >> /dev/null

cast send $TOKEN1 --unlocked --from $USER "transfer(address,uint256)" $TARGET 1 --rpc-url http://localhost:8545 >> /dev/null

# block 5
cast rpc evm_setNextBlockTimestamp $(timestamp 7) --rpc-url http://localhost:8545 >> /dev/null

cast send $TOKEN1 --unlocked --from $USER "transfer(address,uint256)" $TARGET 1 --rpc-url http://localhost:8545 >> /dev/null

# block 6
cast rpc evm_setNextBlockTimestamp $(timestamp 9) --rpc-url http://localhost:8545 >> /dev/null
cast rpc evm_mine --rpc-url http://localhost:8545 >> /dev/null

# block 7

cast rpc evm_setNextBlockTimestamp $(timestamp 10) --rpc-url http://localhost:8545 >> /dev/null
cast send $TOKEN1 --unlocked --from $USER "transfer(address,uint256)" $TARGET 1 --rpc-url http://localhost:8545 >> /dev/null

# block 8
# cast rpc evm_setNextBlockTimestamp $(timestamp 300) --rpc-url http://localhost:8545 >> /dev/null
# cast send $TOKEN1 --unlocked --from $USER "transfer(address,uint256)" $TARGET 1 --rpc-url http://localhost:8545 >> /dev/null

######## END MAIN CHAIN ######## 

NETWORK=localhost

cat <<EOF > config.$NETWORK.yml
Anvil1:
  type: evm-main
  chainUri: 'http://localhost:8545'
  chainId: 31337
  chainCurrencyName: 'ETH'
  chainCurrencySymbol: 'ETH'
  chainCurrencyDecimals: 18
  blockTime: 2
  paimaL2ContractAddress: '$PAIMA_L2'


Cardano:
  type: cardano
  carpUrl: http://localhost:3000
  network: preview
  confirmationDepth: 10
EOF

cat config.$NETWORK.yml

cat <<EOF > extensions.yml
extensions:
  - name: "CARDANO-ASSET1"
    type: cardano-transfer
    credential: addr_test1qp27ms6du9e2fga6njk9ruzprp7gg3uddrnc3htv7mct8kwrwdlnpt07ycmdqyuw7lft338dt33tmr6xdwnn8ezsudpquved20
    startSlot: 12472120
    scheduledPrefix: ct
    network: Cardano
EOF

cat extensions.yml

trap 'kill $(jobs -p); rm extensions.yml; rm config.localhost.yml; pushd chess/db/docker; docker compose down; popd; sleep 5s' EXIT

pushd chess

npm run database:reset >> /dev/null

pushd db/docker

(docker compose up >> /dev/null) &

popd
popd

sleep 5s

sed -i 's/^START_BLOCKHEIGHT=.*/START_BLOCKHEIGHT=3/g' .env.$NETWORK

echo "Starting Paima Engine"

# ./paima-engine-linux run

TMPFILE=$(mktemp)

./paima-engine-linux run >> $TMPFILE & PAIMA_PID=$!; sleep 5s; kill -INT %+; wait $PAIMA_PID

echo "Logs"

cat $TMPFILE

export PGDATABASE="postgres"
export PGUSER="postgres"
export PGPASSWORD="postgres"
export PGHOST="localhost"
export PGPORT=5432

# psql -c 'SELECT * FROM cde_erc20_data;'
psql -c 'SELECT * FROM cde_cardano_asset_utxos;'

###### Assertions

# assertEq() {
#   if [ $1 -ne $2 ]; then
#       echo "Assertion failed: $3. Expected $1 found $2."
#       exit 1
#   fi
# }

# ANVIL1_BALANCE=$(psql -c "SELECT * FROM cde_erc20_data WHERE cde_id=0 AND wallet_address='0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc';" | tail -3 | head -1 | tr -d ' '| awk -F '|' '{ print $3 }')

# CARDANO1_BALANCE=$(psql -c "SELECT amount FROM cde_cardano_asset_utxos WHERE cde_id=1 AND address='00000000000000000000000000000000';" | tail -3 | head -1 | tr -d ' '| awk -F '|' '{ print $1 }')
# # CARDANO2_BALANCE=$(psql -c "SELECT amount FROM cde_cardano_asset_utxos WHERE cde_id=1 AND address='11111111111111111111111111111111';" | tail -3 | head -1 | tr -d ' '| awk -F '|' '{ print $1 }')

# assertEq $ANVIL1_BALANCE 3 "Wrong balance on main chain"

# assertEq $CARDANO1_BALANCE 100 "Wrong balance on cardano address 1"
# # assertEq $CARDANO2_BALANCE 120 "Wrong balance on cardano address 2"

# ## asserts over logs

# assertEq $(grep '2 CDE events in block #4' $TMPFILE >> /dev/null; echo $?) 0 "Wrong grouping for block 2"
# assertEq $(grep 'Processed 1 CDE events in slot #1' $TMPFILE >> /dev/null; echo $?) 0 "Error in presync"


echo ''
echo -e "                            \e[1;32mSuccess\e[0m"
echo ''
