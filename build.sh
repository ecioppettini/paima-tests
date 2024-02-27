#!/usr/bin/bash

pushd ~/Projects/paima-engine
npm run build

pushd packages/engine/paima-standalone/

npm run build
npm run pack

bash package.sh

popd
popd

cp ~/Projects/paima-engine/packages/engine/paima-standalone/packaged/@standalone/paima-engine-linux .

if ! test -f chess; then
  ./paima-engine-linux init template chess

  pushd chess

  npm install
  npm run build
  npm run pack

  popd
fi

if ! test -f contracts; then
  ./paima-engine-linux contracts
fi

rm logs.log

