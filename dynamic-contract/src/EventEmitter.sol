// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;
contract EventEmitter {
    event MyEvent(int256 indexed val, address value);

    function triggerEvent(address _value) external {
        emit MyEvent(1,  _value);
    }
}
