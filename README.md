Test scenario setup for [paima engine](https://github.com/PaimaStudios/paima-engine)

These are not really tests, as there are no asserts. It's mostly a bunch of
tools made in order to be able to play with timestamps/pagination cursors/data
and observe what happens in a what that is easily repeatable. 

`setup.py` has some utils functions to pupeteer the network, start the db and
stuff. `carp_mock.py` has a mock for the carp api, although only for the
paginated endpoint.

To run scenario, compile paima-engine and put it in this directory. 

Then enter the `chess` directory and run:

```sh
npm install
npm run build
npm run pack
```

Also extract the contracts `./paima-engine-linux contracts`

Then cd into `test-cardano-transfer` and run `run.py`.

The chess template is included since it's modified to include the custom parsing rules. 
