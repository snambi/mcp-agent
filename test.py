import json


def add(a, b):
    return a + b

# Simulate receiving JSON-RPC request
request_json = '''
{
    "jsonrpc": "2.0",
    "method": "add",
    "params": [2, 3],
    "id": 1
}
'''

# Parse request
request = json.loads(request_json)
if request["method"] == "add":
    result = add(*request["params"])
    response = {
        "jsonrpc": "2.0",
        "result": result,
        "id": request["id"]
    }
else:
    response = {
        "jsonrpc": "2.0",
        "error": {
            "code": -32601,
            "message": "Method not found"
        },
        "id": request["id"]
    }

print(json.dumps(response))