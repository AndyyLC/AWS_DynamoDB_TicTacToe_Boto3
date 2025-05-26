import boto3
from botocore.exceptions import ClientError
from datetime import datetime

class GameController:
    """
    This GameController class basically acts as a singleton providing the necessary
    DynamoDB API calls.
    """
    def __init__(self, connectionManager):
        self.cm = connectionManager
        self.ResourceNotFound = 'com.amazonaws.dynamodb.v20120810#ResourceNotFoundException'

    def createNewGame(self, gameId, creator, invitee):
        """
        Creates a new game and saves it to the DynamoDB table.
        """
        now = str(datetime.now())
        statusDate = "PENDING_" + now
        table = self.cm.getGamesTable()
        
        item = {
            "GameId": gameId,
            "HostId": creator,
            "StatusDate": statusDate,
            "OUser": creator,
            "Turn": invitee,
            "OpponentId": invitee
        }

        try:
            table.put_item(Item=item)
            return True
        except ClientError as e:
            print(f"Error creating new game: {e}")
            return False

    def checkIfTableIsActive(self):
        table = self.cm.getGamesTable()
        try:
            description = table.table_status
            return description == "ACTIVE"
        except ClientError as e:
            print(f"Error checking table status: {e}")
            return False

    def getGame(self, gameId):
        """
        Fetches a game from the DynamoDB table based on GameId.
        Returns None if the item is not found.
        """
        table = self.cm.getGamesTable()
        try:
            response = table.get_item(Key={'GameId': gameId})
            return response.get('Item', None)
        except ClientError as e:
            print(f"Error retrieving game: {e}")
            return None

    def acceptGameInvite(self, game):
        date = str(datetime.now())
        statusDate = "IN_PROGRESS_" + date
        table = self.cm.getGamesTable()

        try:
            response = table.update_item(
                Key={'GameId': game["GameId"]},
                UpdateExpression="SET StatusDate = :statusDate",
                ConditionExpression="begins_with(StatusDate, :pending)",
                ExpressionAttributeValues={
                    ':statusDate': statusDate,
                    ':pending': "PENDING_"
                },
                ReturnValues="ALL_NEW"
            )
            return True
        except ClientError as e:
            print(f"Error accepting game invite: {e}")
            return False

    def rejectGameInvite(self, game):
        """
        Rejects the game invite by deleting the game if it is still in "PENDING_" status.
        """
        table = self.cm.getGamesTable()

        try:
            response = table.delete_item(
                Key={'GameId': game["GameId"]},
                ConditionExpression="StatusDate = :pending",
                ExpressionAttributeValues={':pending': "PENDING_"}
            )
            return True
        except ClientError as e:
            print(f"Error rejecting game invite: {e}")
            return False

    def getGameInvites(self, user):
        """
        Retrieves up to 10 game invites for the user.
        """
        
        invites = []
        if user == None:
            return invites

        table = self.cm.getGamesTable()
        try:
            response = table.query(
                IndexName="OpponentId-StatusDate-index",
                KeyConditionExpression=boto3.dynamodb.conditions.Key('OpponentId').eq(user) & boto3.dynamodb.conditions.Key('StatusDate').begins_with("PENDING_"),
                Limit=10
            )
            for item in response.get('Items', []):
                invites.append(item)
        except ClientError as e:
            print(f"Error fetching game invites: {e}")
            invites=None

        return invites

    def updateBoardAndTurn(self, item, position, current_player):
        """
        Updates the board and the player's turn.
        """
        player_one = item["HostId"]
        player_two = item["OpponentId"]
        gameId = item["GameId"]
        statusDate = item["StatusDate"]
        date = statusDate.split("_")[1]

        representation = "X" if item["OUser"] != current_player else "O"
        
        next_player = player_two if current_player == player_one else player_one

        print(position)
        print(current_player)
        print(representation)
        print(next_player)

        print(f"GameId: {gameId}") 
        print(f"StatusDate: {statusDate}")
        print(f"Turn: {item['Turn']}, Current Player: {current_player}")
        print(f"Position: {position}, Existing Value: {item.get(position, 'Not Set')}")

        table = self.cm.getGamesTable()

        try:
            response = table.update_item(
                Key={'GameId': gameId},
                UpdateExpression="SET #position = :representation, Turn = :next_player",
                ConditionExpression="begins_with(StatusDate, :statusDate) AND Turn = :current_player AND attribute_not_exists(#position)",
                ExpressionAttributeNames={'#position': position},
                ExpressionAttributeValues={
                    ':representation': representation,
                    ':next_player': next_player,
                    ':statusDate': "IN_PROGRESS_",
                    ':current_player': current_player
                },
                ReturnValues="ALL_NEW"
            )
            return True
        except ClientError as e:
            print(f"Error updating board and turn: {e}")
            return False

    def getBoardState(self, item):
        """
        Returns the current state of the game board as a list.
        """
        squares = ["TopLeft", "TopMiddle", "TopRight", "MiddleLeft", "MiddleMiddle", "MiddleRight", "BottomLeft", "BottomMiddle", "BottomRight"]
        state = [item.get(square, " ") for square in squares]
        return state

    def checkForGameResult(self, board, item, current_player):
        """
        Checks for game result (Win, Loss, Tie).
        """
        yourMarker = "O" if current_player == item["OUser"] else "X"
        theirMarker = "X" if yourMarker == "O" else "O"

        winConditions = [[0, 3, 6], [0, 1, 2], [0, 4, 8], [1, 4, 7], [2, 5, 8], [2, 4, 6], [3, 4, 5], [6, 7, 8]]

        for winCondition in winConditions:
            b_zero, b_one, b_two = board[winCondition[0]], board[winCondition[1]], board[winCondition[2]]
            if b_zero == b_one == b_two == yourMarker:
                return "Win"
            if b_zero == b_one == b_two == theirMarker:
                return "Lose"

        if self.checkForTie(board):
            return "Tie"

        return None

    def checkForTie(self, board):
        """
        Checks if the game is a tie.
        """
        return all(cell != " " for cell in board)

    def changeGameToFinishedState(self, item, result, current_user):
        """
        Sets the game to finished state and updates the result.
        """
        if item.get("Result") is not None:
            return True

        date = str(datetime.now())
        status = "FINISHED"
        item["StatusDate"] = status + "_" + date
        item["Turn"] = "N/A"
        item["Result"] = result if result != "Win" else current_user

        table = self.cm.getGamesTable()

        try:
            table.put_item(Item=item)
            return True
        except ClientError as e:
            print(f"Error finishing the game: {e}")
            return False

    def mergeQueries(self, host, opp, limit=10):
        """
        Merges two queries (host and opponent) and returns the top 10 most recent games.
        """
        games = []
        game_one = None
        game_two = None

        while len(games) <= limit:
            if game_one is None:
                try:
                    game_one = next(host)
                except StopIteration:
                    if game_two:
                        games.append(game_two)
                    games.extend(opp)
                    return games

            if game_two is None:
                try:
                    game_two = next(opp)
                except StopIteration:
                    if game_one:
                        games.append(game_one)
                    games.extend(host)
                    return games

            if game_one['StatusDate'] > game_two['StatusDate']:
                games.append(game_one)
                game_one = None
            else:
                games.append(game_two)
                game_two = None

        return games

    def getGamesWithStatus(self, user, status):
        """
        Fetches games with the specified status.
        """
        if user == None:
            return []
        print("progress")
        table = self.cm.getGamesTable()

        
        print("progress")
        try:
            hostGamesInProgress = table.query(
                IndexName="HostId-StatusDate-index",
                KeyConditionExpression=boto3.dynamodb.conditions.Key('HostId').eq(user) & boto3.dynamodb.conditions.Key('StatusDate').begins_with(status),
                Limit=10
            )

            oppGamesInProgress = table.query(
                IndexName="OpponentId-StatusDate-index",
                KeyConditionExpression=boto3.dynamodb.conditions.Key('OpponentId').eq(user) & boto3.dynamodb.conditions.Key('StatusDate').begins_with(status),
                Limit=10
            )

            games = self.mergeQueries(iter(hostGamesInProgress['Items']), iter(oppGamesInProgress['Items']))
            return games
        except ClientError as e:
            print(f"Error fetching in progress {e}")
            return False
