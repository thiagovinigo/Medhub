def handler(request):
    return {"body": '{"pong": true}', "statusCode": 200, "headers": {"Content-Type": "application/json"}}
