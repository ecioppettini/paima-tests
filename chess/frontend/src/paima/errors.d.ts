import type { EndpointErrorFxn } from '@paima/sdk/mw-core';
export declare const enum MiddlewareErrorCode {
    GENERIC_ERROR = 1000001,
    CALCULATED_ROUND_END_IN_PAST = 1000002,
    UNABLE_TO_BUILD_EXECUTOR = 1000003,
    NO_OPEN_LOBBIES = 1000004,
    FAILURE_VERIFYING_LOBBY_CREATION = 1000005,
    FAILURE_VERIFYING_LOBBY_CLOSE = 1000006,
    FAILURE_VERIFYING_LOBBY_JOIN = 1000007,
    FAILURE_VERIFYING_MOVE_SUBMISSION = 1000008,
    CANNOT_JOIN_OWN_LOBBY = 1000009,
    CANNOT_CLOSE_SOMEONES_LOBBY = 1000010
}
export declare function buildEndpointErrorFxn(endpointName: string): EndpointErrorFxn;
