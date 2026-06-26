// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;
import "forge-std/Test.sol";
import "../src/YanVerify.sol";

contract YanVerifyTest is Test {
    YanVerify yan;
    function setUp() public { yan = new YanVerify(); }

    function testGas() public {
        uint256 gStart = gasleft();
        // Use synthetic inputs to measure the gas cost of the modeled verification logic.
        yan.verifyA3(bytes32(uint256(1)), bytes32(uint256(2)), 999);
        uint256 gUsed = gStart - gasleft();

        console.log("-----------------------------------------");
        console.log("Measured Gas Used for Yan A3:", gUsed);
        console.log("-----------------------------------------");
    }
}
