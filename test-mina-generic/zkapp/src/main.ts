import { Square } from "./Square.js";
import {
  Field,
  Lightnet,
  Mina,
  PrivateKey,
  AccountUpdate,
  fetchAccount,
} from "o1js";
import { zkAppBodyPrefix } from "o1js/dist/node/mina-signer/src/signature.js";
import { feePayerHash } from "o1js/dist/node/mina-signer/src/sign-zkapp-command.js";

// Network configuration
const network = Mina.Network({
  mina: "http://localhost:8080/graphql",
  archive: "http://localhost:8282",
  lightnetAccountManager: "http://localhost:8181",
});

Mina.setActiveInstance(network);

// Fee payer setup
const feePayerPrivateKey = (await Lightnet.acquireKeyPair()).privateKey;
const feePayerAccount = feePayerPrivateKey.toPublicKey();

// Create a public/private key pair. The public key is your address and where you deploy the zkApp to
// const zkAppPrivateKey = PrivateKey.random();
const zkAppPrivateKey = PrivateKey.fromBase58(
  "EKEBsPebmNqD7gqu3LaUtJbM3DRXhpiUGbMHZ5pNJooTneYRZDp4",
);
console.log("private key", zkAppPrivateKey.toBase58());

const zkAppAddress = zkAppPrivateKey.toPublicKey();

console.log("public key", zkAppAddress.toBase58());

// create an instance of Square - and deploy it to zkAppAddress
const zkAppInstance = new Square(zkAppAddress);

await Square.compile();

async function deploy() {
  const deployTxn = await Mina.transaction(
    { sender: feePayerAccount, fee: 0.1e9 },
    async () => {
      AccountUpdate.fundNewAccount(feePayerAccount);
      await zkAppInstance.deploy({});
    },
  );

  await deployTxn.sign([feePayerPrivateKey, zkAppPrivateKey]).send();
}

console.log("deploying");
deploy();

console.log("deployed");

async function waitForStateToEqual(state: string) {
  while (true) {
    try {
      // get the initial state of Square after deployment

      await zkAppInstance.num.fetch();
      const num0 = zkAppInstance.num.get();

      if (num0.toString() === state) {
        console.log("state:", num0.toString());
        return;
      }
    } catch (error) {
      await sleep(1000);
    }
  }
}

await waitForStateToEqual("3");

await setStateTo(9);
await setStateTo(81);
await setStateTo(6561);
await setStateTo(43046721);

console.log("releasing", feePayerAccount.toBase58());

// Release previously acquired key pair
const keyPairReleaseMessage = await Lightnet.releaseKeyPair({
  publicKey: feePayerAccount.toBase58(),
});
if (keyPairReleaseMessage) console.log(keyPairReleaseMessage);

async function setStateTo(to: number) {
  const txn1 = await Mina.transaction(
    { sender: feePayerAccount, fee: 0.1e9 },
    async () => {
      await zkAppInstance.update(Field(to));
    },
  );
  await txn1.prove();
  await txn1.sign([feePayerPrivateKey]).send();

  await waitForStateToEqual(to.toString());
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
