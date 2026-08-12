// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract EvidenceLedger {
    struct CustodyEvent {
        address actor;
        string action;
        uint256 timestamp;
        string notes;
    }

    struct Evidence {
        string evidenceId;
        string fileHash;
        string suitNumber;
        address currentCustodian;
        bool isRegistered;
    }

    mapping(string => Evidence) public evidenceRegistry;
    mapping(string => CustodyEvent[]) public custodyHistory;

    event EvidenceRegistered(string indexed evidenceId, string fileHash, address indexed custodian);
    event CustodyTransferred(string indexed evidenceId, address indexed prevCustodian, address indexed newCustodian);

    function registerEvidence(string memory _evidenceId, string memory _fileHash, string memory _suitNumber) public {
        require(!evidenceRegistry[_evidenceId].isRegistered, "Evidence ID already exists.");

        evidenceRegistry[_evidenceId] = Evidence({
            evidenceId: _evidenceId,
            fileHash: _fileHash,
            suitNumber: _suitNumber,
            currentCustodian: msg.sender,
            isRegistered: true
        });

        custodyHistory[_evidenceId].push(CustodyEvent({
            actor: msg.sender,
            action: "REGISTERED",
            timestamp: block.timestamp,
            notes: "Initial registration on permissioned ledger."
        }));

        emit EvidenceRegistered(_evidenceId, _fileHash, msg.sender);
    }

    function transferCustody(string memory _evidenceId, address _newCustodian, string memory _notes) public {
        require(evidenceRegistry[_evidenceId].isRegistered, "Evidence not found.");
        require(evidenceRegistry[_evidenceId].currentCustodian == msg.sender, "Unauthorized: Only current custodian can transfer.");

        address prevCustodian = msg.sender;
        evidenceRegistry[_evidenceId].currentCustodian = _newCustodian;

        custodyHistory[_evidenceId].push(CustodyEvent({
            actor: msg.sender,
            action: "TRANSFERRED",
            timestamp: block.timestamp,
            notes: _notes
        }));

        emit CustodyTransferred(_evidenceId, prevCustodian, _newCustodian);
    }
}
