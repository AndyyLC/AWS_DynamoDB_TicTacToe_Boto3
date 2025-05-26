from dynamodb.connectionManager     import ConnectionManager
from dynamodb.gameController        import GameController
from models.game                    import Game

import boto3

# Create a DynamoDB client
dynamodb = boto3.client('dynamodb', 
                        region_name='us-west-2',  # You can use any region for local setup
                        endpoint_url='http://localhost:8000')  # Endpoint for DynamoDB Local

#Delete tables
table_name = 'Games'
try:
    response = dynamodb.delete_table(TableName=table_name)
    print(f"Table {table_name} deleted successfully!")
    print(response)
except Exception as e:
    print(f"Error deleting table {table_name}: {e}")

# cm = ConnectionManager(mode="local", endpoint="http://localhost", port=8000)

# # Call the createGamesTable method on the instance
# cm.createGamesTable()
# cm.setupGamesTable()

# table = cm.getGamesTable()

# try:

#     statusDate = "IN_PROGRESS_"
#     response = table.update_item(
#         Key={'GameId': "555594a3-d43a-4754-9ca3-5354d4a063d2"},
#         UpdateExpression="SET StatusDate = :statusDate",
#         ConditionExpression="begins_with(StatusDate, :pending)",
#         ExpressionAttributeValues={
#             ':statusDate': statusDate,
#             ':pending': "PENDING_"
#         },
#         ReturnValues="ALL_NEW"
#     )
# except:
#     print(f"Error accepting game invite:")


