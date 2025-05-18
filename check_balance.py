from web3 import Web3

# Thay địa chỉ ví bên dưới bằng ví số 0 mới nhất từ log Ganache Render
address = "0x7D44ceF653944abaE6Fd6b15f3ab14dB07c6ac2B"

w3 = Web3(Web3.HTTPProvider("https://ganache-service-7809.onrender.com/"))
balance = w3.eth.get_balance(address)
print(f"Số dư (wei): {balance}")
print(f"Số dư (ETH): {w3.from_wei(balance, 'ether')}") 