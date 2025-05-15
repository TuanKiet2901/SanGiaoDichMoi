from app.blockchain.ethereum import EthereumClient

# Create a global instance of the Ethereum client
ethereum_client = None

def init_app(app):
    """Initialize blockchain integration with the Flask app"""
    global ethereum_client
    
    # Initialize Ethereum client
    ethereum_client = EthereumClient()
    
    # Log connection status
    if ethereum_client.is_connected():
        app.logger.info("Connected to Ethereum node")
    else:
        app.logger.warning("Failed to connect to Ethereum node")
    
    # Add ethereum client to app context
    app.config['ETHEREUM_CLIENT'] = ethereum_client
