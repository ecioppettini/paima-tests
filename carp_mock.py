#!/usr/bin/python3

import json
import logging
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from itertools import islice

PAGINATION_LIMIT = 2

def filterOutput(slot, low, high):
    return slot > low and slot <= high


def HTTPRequestHandlerFactory(output, paginatedPath, getSlot, getTxHash, mapResult):
    class HTTPRequestHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)

        def do_POST(self):
            # logging.info("path: %s", self.path)
            if re.search(paginatedPath, self.path):
                length = int(self.headers.get("content-length"))
                input = self.rfile.read(length).decode("utf8")

                logging.info("received %s", input)

                input = json.loads(input)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                # print(input)

                after = -1

                if input.get("after") is not None:
                    tx = input["after"]["tx"]

                    # print(f"{tx}")

                    maybeAfter = next(
                        map(
                            lambda t: t[0],
                            filter(
                                lambda x: getTxHash(x[1]) == tx,
                                enumerate(output),
                            ),
                        ),
                        None,
                    )

                    if maybeAfter is not None:
                        after = maybeAfter

                filteredData = list(
                    islice(
                        filter(
                            lambda x: filterOutput(
                                getSlot(x),
                                input["slotLimits"]["from"],
                                input["slotLimits"]["to"],
                            ),
                            output[after + 1 :],
                        ),
                        PAGINATION_LIMIT,
                    )
                )

                jsonData = json.dumps(
                    mapResult(filteredData)
                ).encode("utf-8")

                # logging.info("get record: %s", data)
                self.wfile.write(jsonData)
            elif re.search("/block/latest", self.path):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                jsonData = json.dumps(
                    {
                        "block": {
                            "slot": 12680810,
                            "epoch": 0,
                            "height": 1247300,
                            "hash": "00000000000000000000000000000000",
                            "era": 0,
                        },
                    }
                ).encode("utf-8")
                # logging.info("get record: %s", data)
                self.wfile.write(jsonData)
            else:
                self.send_response(403)
            self.end_headers()

    return HTTPRequestHandler


class SignalingHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ready_event = threading.Event()

    def service_actions(self):
        self.ready_event.set()

    def __enter__(self):
        thread = threading.Thread(target=lambda: self.serve_forever(), name="server")
        thread.start()

        self.ready_event.wait()

    def __exit__(self, *args):
        self.shutdown()
        self.server_close()


def carp_mock(port, output, paginatedPath, getSlot, getTxHash, mapResult):
    server = SignalingHTTPServer(
        ("localhost", port),
        HTTPRequestHandlerFactory(output, paginatedPath, getSlot, getTxHash, mapResult),
    )

    return server


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8000), HTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
