import requests

res = requests.post("http://127.0.0.1:5001/api/v0/version")
print(res.json())
