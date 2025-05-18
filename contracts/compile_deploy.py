import json
import os
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

# Install specific solc version
install_solc("0.8.0")

# Load environment variables
load_dotenv()

def compile_contract():
    # Read the contract source code
    with open("contracts/TraceabilityContract.sol", "r") as file:
        contract_source_code = file.read()
    
    # Compile the contract
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {
                "TraceabilityContract.sol": {
                    "content": contract_source_code
                }
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            }
        },
        solc_version="0.8.0"
    )
    
    # Save the compiled contract
    with open("contracts/compiled_contract.json", "w") as file:
        json.dump(compiled_sol, file)
    
    return compiled_sol

def deploy_contract(compiled_sol, w3, account_address, private_key):
    # Get contract data
    contract_data = compiled_sol["contracts"]["TraceabilityContract.sol"]["TraceabilityContract"]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]
    
    # Save ABI to a file for later use
    with open("contracts/contract_abi.json", "w") as file:
        json.dump(abi, file)
    
    # Create contract instance
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Get nonce
    nonce = w3.eth.get_transaction_count(account_address)
    
    # Build transaction
    transaction = Contract.constructor().build_transaction(
        {
            "chainId": w3.eth.chain_id,
            "gasPrice": w3.eth.gas_price,
            "from": account_address,
            "nonce": nonce,
        }
    )
    
    # Sign transaction
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    # Wait for transaction receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Save contract address to a file
    with open("contracts/contract_address.txt", "w") as file:
        file.write(tx_receipt.contractAddress)
    
    print(f"Contract deployed at address: {tx_receipt.contractAddress}")
    
    return tx_receipt.contractAddress, abi

def main():
    # Connect to Ganache
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
    
    # Check if connected
    if not w3.is_connected():
        print("Failed to connect to Ethereum node!")
        return
    
    print(f"Connected to Ethereum node. Chain ID: {w3.eth.chain_id}")
    
    # Get account from environment or use default Ganache account
    account_address = os.getenv("ETHEREUM_ADDRESS")
    private_key = os.getenv("ETHEREUM_PRIVATE_KEY")
    
    # Compile the contract
    print("Compiling contract...")
    compiled_sol = compile_contract()
    
    # Deploy the contract
    print("Deploying contract...")
    contract_address, abi = deploy_contract(compiled_sol, w3, account_address, private_key)
    
    print("Contract compilation and deployment completed successfully!")
    print(f"Contract address: {contract_address}")
    print("ABI saved to contracts/contract_abi.json")

if __name__ == "__main__":
    main()
