import boto3
from botocore.exceptions import ClientError
from uuid import uuid4
import sys
sys.path.append("C:/Users/andy1/Downloads/dynamodb_local_latest/NewVersion/dynamodb")
from setupDynamoDB          import getDynamoDBConnection, createGamesTable 
class ConnectionManager:

    def __init__(self, mode=None, config=None, endpoint=None, port=None, use_instance_metadata=False):
        self.db = None
        self.gamesTable = None

        if mode == "local":
            if config is not None:
                raise Exception('Cannot specify config when in local mode')
            if endpoint is None:
                endpoint = 'http://localhost'
            if port is None:
                port = 8000
            self.db = getDynamoDBConnection(endpoint=endpoint, port=port, local=True)
        elif mode == "service":
            self.db = getDynamoDBConnection(config=config, endpoint=endpoint, use_instance_metadata=use_instance_metadata)
        else:
            raise Exception("Invalid arguments, please refer to usage.")

        self.setupGamesTable()

    def setupGamesTable(self):
        print("g")
        try:
            self.gamesTable = self.db.Table("Games")
        except ClientError as e:
            print(f"Error getting table: {e.response['Error']['Message']}")
            raise Exception("There was an issue trying to retrieve the Games table.")

    def getGamesTable(self):
        if self.gamesTable is None:
            self.setupGamesTable()
        return self.gamesTable

    def createGamesTable(self):
        print("c")
        self.gamesTable = createGamesTable(self.db)
            
    

