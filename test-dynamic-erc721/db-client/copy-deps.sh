#!/usr/bin/env sh

rm -rf ./node_modules/@paima/mw-core
cp -r $PAIMA_ENGINE_PATH/packages/paima-sdk/paima-mw-core ./node_modules/@paima/mw-core

rm -rf ./node_modules/@paima/providers
cp -r $PAIMA_ENGINE_PATH/packages/paima-sdk/paima-providers ./node_modules/@paima/providers

rm -rf -f ./node_modules/@paima/build-utils
cp -r $PAIMA_ENGINE_PATH/packages/build-utils/paima-build-utils ./node_modules/@paima/build-utils

rm -rf -f ./node_modules/@paima/crypto
cp -r $PAIMA_ENGINE_PATH/packages/paima-sdk/paima-crypto ./node_modules/@paima/crypto

rm -rf -f ./node_modules/@paima/utils-backend
cp -r $PAIMA_ENGINE_PATH/packages/node-sdk/paima-utils-backend/ ./node_modules/@paima/utils-backend

rm -rf ./node_modules/@paima/utils
cp -r $PAIMA_ENGINE_PATH/packages/paima-sdk/paima-utils ./node_modules/@paima/utils

rm -rf -f ./node_modules/@paima/db
cp -r $PAIMA_ENGINE_PATH/packages/node-sdk/paima-db/ ./node_modules/@paima/db
