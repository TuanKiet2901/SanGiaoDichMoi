import json
import os
from web3 import Web3
from flask import current_app

class EthereumClient:
    def __init__(self, provider_url=None):
        """
        Initialize Ethereum client
        
        Args:
            provider_url: URL of the Ethereum node (default: http://127.0.0.1:7545 for Ganache)
        """
        self.provider_url = provider_url
        self.is_initialized = False
        
        # Thêm timeout và retry cho HTTPProvider
        self.w3 = Web3(Web3.HTTPProvider(
            self.provider_url,
            request_kwargs={
                'timeout': 30,  # 30 seconds timeout
                'verify': False,  # Disable SSL verification for development
                'headers': {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            }
        ))
        
        # Thử kết nối và in thông tin chi tiết
        try:
            # Sử dụng eth_blockNumber thay vì chain_id để kiểm tra kết nối
            block_number = self.w3.eth.block_number
            print(f"Successfully connected to block number: {block_number}")
            self.is_initialized = True
        except Exception as e:
            print(f"Failed to connect to Ethereum node at {self.provider_url}")
            print(f"Error details: {str(e)}")
            # Thử lại với URL không có dấu / ở cuối
            if self.provider_url.endswith('/'):
                try:
                    self.provider_url = self.provider_url[:-1]
                    print(f"Retrying with URL: {self.provider_url}")
                    self.w3 = Web3(Web3.HTTPProvider(
                        self.provider_url,
                        request_kwargs={
                            'timeout': 30,
                            'verify': False,
                            'headers': {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            }
                        }
                    ))
                    block_number = self.w3.eth.block_number
                    print(f"Successfully connected to block number: {block_number}")
                    self.is_initialized = True
                except Exception as e2:
                    print(f"Failed to connect on retry: {str(e2)}")
                    self.is_initialized = False
                    return
            else:
                self.is_initialized = False
                return
        # Load contract ABI and address
        try:
            with open('contracts/contract_abi.json', 'r') as f:
                self.contract_abi = json.load(f)
            with open('contracts/contract_address.txt', 'r') as f:
                self.contract_address = f.read().strip()
            # Create contract instance
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
            self.is_initialized = True
            print(f"Successfully initialized Ethereum client with contract at {self.contract_address}")
        except Exception as e:
            print(f"Failed to initialize Ethereum client: {str(e)}")
            self.is_initialized = False
    
    def is_connected(self):
        """Check if connected to Ethereum node"""
        return self.w3.is_connected() and self.is_initialized
    
    def register_batch(self, batch_id, product_name, harvest_date, location, additional_info=""):
        """
        Register a batch on the blockchain
        
        Args:
            batch_id: Unique identifier for the batch
            product_name: Name of the product
            harvest_date: Date of harvest
            location: Location of harvest
            additional_info: Additional information about the batch
            
        Returns:
            Transaction hash
        """
        if not self.is_connected():
            raise Exception("Not connected to Ethereum node")
        
        # Get account from environment
        account_address = os.getenv('ETHEREUM_ADDRESS')
        private_key = os.getenv('ETHEREUM_PRIVATE_KEY')
        
        if not account_address or not private_key:
            raise Exception("Ethereum account address or private key not set")
        
        # Get nonce
        nonce = self.w3.eth.get_transaction_count(account_address)
        
        # Build transaction
        transaction = self.contract.functions.registerBatch(
            int(batch_id),
            product_name,
            harvest_date,
            location,
            additional_info
        ).build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
            'from': account_address
        })
        
        # Sign transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=private_key)
        
        # Send transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return tx_receipt.transactionHash.hex()
    
    def add_supply_chain_step(self, batch_id, step_name, timestamp, location, handler, additional_info=""):
        """
        Add a supply chain step to a batch on the blockchain
        
        Args:
            batch_id: Batch ID to add the step to
            step_name: Name of the step
            timestamp: Timestamp of the step
            location: Location where the step occurred
            handler: Person or entity handling the step
            additional_info: Additional information about the step
            
        Returns:
            Transaction hash
        """
        if not self.is_connected():
            raise Exception("Not connected to Ethereum node")
        
        # Get account from environment
        account_address = os.getenv('ETHEREUM_ADDRESS')
        private_key = os.getenv('ETHEREUM_PRIVATE_KEY')
        
        if not account_address or not private_key:
            raise Exception("Ethereum account address or private key not set")
        
        # Get nonce
        nonce = self.w3.eth.get_transaction_count(account_address)
        
        # Build transaction
        transaction = self.contract.functions.addSupplyChainStep(
            int(batch_id),
            step_name,
            timestamp,
            location,
            handler,
            additional_info
        ).build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
            'from': account_address
        })
        
        # Sign transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=private_key)
        
        # Send transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return tx_receipt.transactionHash.hex()
    
    def get_batch(self, batch_id):
        """
        Get batch information from the blockchain
        
        Args:
            batch_id: Batch ID to retrieve
            
        Returns:
            Batch information
        """
        if not self.is_connected():
            raise Exception("Not connected to Ethereum node")
        
        try:
            batch = self.contract.functions.getBatch(int(batch_id)).call()
            
            return {
                'id': batch[0],
                'product_name': batch[1],
                'harvest_date': batch[2],
                'location': batch[3],
                'additional_info': batch[4],
                'exists': batch[5]
            }
        except Exception as e:
            print(f"Failed to get batch from blockchain: {str(e)}")
            return None
    
    def get_supply_chain_steps(self, batch_id):
        """
        Get all supply chain steps for a batch from the blockchain
        
        Args:
            batch_id: Batch ID to retrieve steps for
            
        Returns:
            List of supply chain steps
        """
        if not self.is_connected():
            raise Exception("Not connected to Ethereum node")
        
        try:
            # Get number of steps
            step_count = self.contract.functions.getSupplyChainStepCount(int(batch_id)).call()
            
            steps = []
            for i in range(step_count):
                step = self.contract.functions.getSupplyChainStep(int(batch_id), i).call()
                
                steps.append({
                    'batch_id': step[0],
                    'step_name': step[1],
                    'timestamp': step[2],
                    'location': step[3],
                    'handler': step[4],
                    'additional_info': step[5]
                })
            
            return steps
        except Exception as e:
            print(f"Failed to get supply chain steps from blockchain: {str(e)}")
            return []
    
    def verify_transaction(self, tx_hash):
        """
        Verify a transaction on the blockchain
        
        Args:
            tx_hash: Transaction hash to verify
            
        Returns:
            Transaction information
        """
        if not self.is_connected():
            raise Exception("Not connected to Ethereum node")
        
        try:
            # Convert string hash to bytes if needed
            if isinstance(tx_hash, str) and tx_hash.startswith('0x'):
                tx_hash = bytes.fromhex(tx_hash[2:])
            
            # Get transaction receipt
            tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            # Get transaction
            tx = self.w3.eth.get_transaction(tx_hash)
            
            # Get block
            block = self.w3.eth.get_block(tx_receipt.blockNumber)
            
            return {
                'transaction_hash': tx_receipt.transactionHash.hex(),
                'block_number': tx_receipt.blockNumber,
                'from': tx['from'],
                'to': tx['to'],
                'gas_used': tx_receipt.gasUsed,
                'status': tx_receipt.status,
                'timestamp': block.timestamp,
                'chain_id': self.w3.eth.chain_id
            }
        except Exception as e:
            print(f"Failed to verify transaction: {str(e)}")
            return None
