from web3 import Web3

# Thay địa chỉ ví bên dưới bằng ví số 0 mới nhất từ log Ganache Render
address = "0x627306090abaB3A6e1400e9345bC60c78a8BEf57"

w3 = Web3(Web3.HTTPProvider("https://ganache-service-7809.onrender.com/"))
balance = w3.eth.get_balance(address)
print(f"Số dư (wei): {balance}")
print(f"Số dư (ETH): {w3.from_wei(balance, 'ether')}") 