import boto3
from datetime import datetime

class Game:
    """
    This Game class acts as a wrapper on top of an item in the Games table.
    Each of the fields in the table is of a String type.
    GameId is the primary key.
    HostId-StatusDate, Opponent-StatusDate are Global Secondary Indexes that are Hash-Range Keys.
    The other attributes are used to maintain game state.
    """
    def __init__(self, item):
        self.item = item
        self.gameId       = item['GameId']
        self.hostId       = item['HostId']
        self.opponent     = item['OpponentId']
        self.statusDate   = item['StatusDate'].split("_")
        self.o            = item['OUser']
        self.turn         = item['Turn']

    def getStatus(self):
        status = self.statusDate[0]
        if len(self.statusDate) > 2:
            status += "_" + self.statusDate[1]
        return status
    status = property(getStatus)

    def getDate(self):
        index = 1
        if len(self.statusDate) > 2:
            index = 2
        date = datetime.strptime(self.statusDate[index], '%Y-%m-%d %H:%M:%S.%f')
        return datetime.strftime(date, '%Y-%m-%d %H:%M:%S')
    date = property(getDate)

    def __lt__(self, otherGame):
        """Comparison method for sorting based on statusDate."""
        if otherGame is None:
            return False
        return self.statusDate[1] < otherGame.statusDate[1]

    def getOpposingPlayer(self, current_player):
        """Returns the opposing player based on the current player."""
        if current_player == self.hostId:
            return self.opponent
        else:
            return self.hostId

    def getResult(self, current_player):
        """Returns the game result based on the current player's outcome."""
        if self.item.get('Result') is None:
            return None
        if self.item['Result'] == "Tie":
            return "Tie"
        if self.item['Result'] == current_player:
            return "Win"
        else:
            return "Lose"

    @staticmethod
    def get_item(dynamodb, game_id):
        """Fetches a Game item from DynamoDB based on GameId."""
        table = dynamodb.Table('Games')
        try:
            response = table.get_item(Key={'GameId': game_id})
            if 'Item' in response:
                return Game(response['Item'])
            else:
                return None
        except Exception as e:
            print(f"Error fetching game with ID {game_id}: {e}")
            return None
