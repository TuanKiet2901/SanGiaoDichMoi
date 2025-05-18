from web3 import Web3

# Thay địa chỉ ví bên dưới bằng ví số 0 mới nhất từ log Ganache Render
address = "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1"
#address = "0xc5b22e8042dCC32874a958Cc4881526ef64A4Bc6"

w3 = Web3(Web3.HTTPProvider("https://ganache-service-7809.onrender.com/"))
balance = w3.eth.get_balance(address)
print(f"Số dư (wei): {balance}")
print(f"Số dư (ETH): {w3.from_wei(balance, 'ether')}") 