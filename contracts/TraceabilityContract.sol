// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title TraceabilityContract
 * @dev Smart contract for agricultural product traceability
 */
contract TraceabilityContract {
    address public owner;
    
    // Batch structure
    struct Batch {
        uint256 id;
        string productName;
        string harvestDate;
        string location;
        string additionalInfo;
        bool exists;
    }
    
    // Supply chain step structure
    struct SupplyChainStep {
        uint256 batchId;
        string stepName;
        string timestamp;
        string location;
        string handler;
        string additionalInfo;
    }
    
    // Mapping from batch ID to Batch
    mapping(uint256 => Batch) public batches;
    
    // Mapping from batch ID to array of supply chain steps
    mapping(uint256 => SupplyChainStep[]) public supplyChainSteps;
    
    // Events
    event BatchRegistered(uint256 indexed batchId, string productName, string harvestDate);
    event SupplyChainStepAdded(uint256 indexed batchId, string stepName, string timestamp);
    
    /**
     * @dev Constructor sets the owner of the contract
     */
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @dev Modifier to check if the caller is the owner
     */
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    /**
     * @dev Register a new batch
     * @param _batchId Unique identifier for the batch
     * @param _productName Name of the product
     * @param _harvestDate Date of harvest
     * @param _location Location of harvest
     * @param _additionalInfo Additional information about the batch
     */
    function registerBatch(
        uint256 _batchId,
        string memory _productName,
        string memory _harvestDate,
        string memory _location,
        string memory _additionalInfo
    ) public {
        require(!batches[_batchId].exists, "Batch already exists");
        
        Batch memory newBatch = Batch({
            id: _batchId,
            productName: _productName,
            harvestDate: _harvestDate,
            location: _location,
            additionalInfo: _additionalInfo,
            exists: true
        });
        
        batches[_batchId] = newBatch;
        
        emit BatchRegistered(_batchId, _productName, _harvestDate);
    }
    
    /**
     * @dev Add a supply chain step to a batch
     * @param _batchId Batch ID to add the step to
     * @param _stepName Name of the step
     * @param _timestamp Timestamp of the step
     * @param _location Location where the step occurred
     * @param _handler Person or entity handling the step
     * @param _additionalInfo Additional information about the step
     */
    function addSupplyChainStep(
        uint256 _batchId,
        string memory _stepName,
        string memory _timestamp,
        string memory _location,
        string memory _handler,
        string memory _additionalInfo
    ) public {
        require(batches[_batchId].exists, "Batch does not exist");
        
        SupplyChainStep memory newStep = SupplyChainStep({
            batchId: _batchId,
            stepName: _stepName,
            timestamp: _timestamp,
            location: _location,
            handler: _handler,
            additionalInfo: _additionalInfo
        });
        
        supplyChainSteps[_batchId].push(newStep);
        
        emit SupplyChainStepAdded(_batchId, _stepName, _timestamp);
    }
    
    /**
     * @dev Get batch information
     * @param _batchId Batch ID to retrieve
     * @return id Batch ID
     * @return productName Name of the product
     * @return harvestDate Date of harvest
     * @return location Location of harvest
     * @return additionalInfo Additional information about the batch
     * @return exists Whether the batch exists
     */
    function getBatch(uint256 _batchId) public view returns (
        uint256 id,
        string memory productName,
        string memory harvestDate,
        string memory location,
        string memory additionalInfo,
        bool exists
    ) {
        Batch memory batch = batches[_batchId];
        require(batch.exists, "Batch does not exist");
        
        return (
            batch.id,
            batch.productName,
            batch.harvestDate,
            batch.location,
            batch.additionalInfo,
            batch.exists
        );
    }
    
    /**
     * @dev Get the number of supply chain steps for a batch
     * @param _batchId Batch ID to check
     * @return Number of steps
     */
    function getSupplyChainStepCount(uint256 _batchId) public view returns (uint256) {
        require(batches[_batchId].exists, "Batch does not exist");
        return supplyChainSteps[_batchId].length;
    }
    
    /**
     * @dev Get a specific supply chain step for a batch
     * @param _batchId Batch ID to retrieve from
     * @param _stepIndex Index of the step to retrieve
     * @return batchId Batch ID
     * @return stepName Name of the step
     * @return timestamp Timestamp of the step
     * @return location Location of the step
     * @return handler Handler of the step
     * @return additionalInfo Additional information about the step
     */
    function getSupplyChainStep(uint256 _batchId, uint256 _stepIndex) public view returns (
        uint256 batchId,
        string memory stepName,
        string memory timestamp,
        string memory location,
        string memory handler,
        string memory additionalInfo
    ) {
        require(batches[_batchId].exists, "Batch does not exist");
        require(_stepIndex < supplyChainSteps[_batchId].length, "Step index out of bounds");
        
        SupplyChainStep memory step = supplyChainSteps[_batchId][_stepIndex];
        
        return (
            step.batchId,
            step.stepName,
            step.timestamp,
            step.location,
            step.handler,
            step.additionalInfo
        );
    }
    
    /**
     * @dev Transfer ownership of the contract
     * @param _newOwner Address of the new owner
     */
    function transferOwnership(address _newOwner) public onlyOwner {
        require(_newOwner != address(0), "New owner cannot be the zero address");
        owner = _newOwner;
    }
}
