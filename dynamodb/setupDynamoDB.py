from urllib.request import urlopen
import boto3
from botocore.exceptions import ClientError
from flask import json

def getDynamoDBConnection(config=None, endpoint=None, port=None, local=False, use_instance_metadata=False):
    if local:
        
        return boto3.resource(
            'dynamodb',
            endpoint_url=f"{endpoint}:{port}",
            aws_access_key_id='ticTacToeSampleApp',
            aws_secret_access_key='ticTacToeSampleApp',
            region_name='us-west-2'
        )
    
    else:
        params = {}

        # ✅ Read from config if provided
        if config:
            if config.has_option('dynamodb', 'region'):
                params['region_name'] = config.get('dynamodb', 'region')
            if config.has_option('dynamodb', 'endpoint'):
                params['endpoint_url'] = config.get('dynamodb', 'endpoint')
            if config.has_option('dynamodb', 'aws_access_key_id'):
                params['aws_access_key_id'] = config.get('dynamodb', 'aws_access_key_id')
                params['aws_secret_access_key'] = config.get('dynamodb', 'aws_secret_access_key')

        # ✅ Override endpoint if provided
        if endpoint:
            params['endpoint_url'] = f"http://{endpoint}:{port}"

        # ✅ Auto-detect AWS endpoint (if no endpoint is provided)
        if 'endpoint_url' not in params and use_instance_metadata:
            try:
                response = urlopen('http://169.254.169.254/latest/dynamic/instance-identity/document').read()
                doc = json.loads(response)
                params['region_name'] = doc['region']
            except Exception as e:
                raise Exception("Error accessing instance metadata: ", e)

        # ✅ Create DynamoDB connection
        db = boto3.resource('dynamodb', **params)

    return db
        
    # else:
    #     return boto3.resource('dynamodb', region_name='us-west-2')

def createGamesTable(dynamodb=None):
    print("sD")
    try:
        table = dynamodb.create_table(
            TableName='Games',
            KeySchema=[
                {'AttributeName': 'GameId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'GameId', 'AttributeType': 'S'},
                {'AttributeName': 'HostId', 'AttributeType': 'S'},
                {'AttributeName': 'StatusDate', 'AttributeType': 'S'},
                {'AttributeName': 'OpponentId', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'HostId-StatusDate-index',
                    'KeySchema': [
                        {'AttributeName': 'HostId', 'KeyType': 'HASH'},
                        {'AttributeName': 'StatusDate', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                },
                {
                    'IndexName': 'OpponentId-StatusDate-index',
                    'KeySchema': [
                        {'AttributeName': 'OpponentId', 'KeyType': 'HASH'},
                        {'AttributeName': 'StatusDate', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )
        table.wait_until_exists()
        return table
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            return dynamodb.Table('Games')
        else:
            raise
