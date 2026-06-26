// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract YanVerify {
    function verifyA3(
        bytes32 G1,
        bytes32 ID_v,
        uint256 pR
    ) public pure returns (bytes32 G7) {
        // Simulated on-chain workload corresponding to Algorithm 3 of Yan et al.
        bytes32 h2 = keccak256(abi.encodePacked(pR));
        bytes32 G5 = G1 ^ h2;
        bytes32 G6 = ID_v ^ h2;
        G7 = keccak256(abi.encodePacked(G5, G6));
    }
}
