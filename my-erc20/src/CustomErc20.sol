// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "lib/openzeppelin-contracts/contracts/token/ERC20/ERC20.sol";

contract CustomERC20 is ERC20 {
    constructor() ERC20("CustomErc20", "TOKEN") {
        _mint(msg.sender, 1000);
    }
} 
