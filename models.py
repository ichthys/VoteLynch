# forward declarations (redefined later)
class Game(db.Model):
   pass
class Vote(db.Model):
   pass


class Stage(db.Model):
   """Base class for days&nights

   Properties
     index: 0,1,2,... ordered index of stage
     game: related game

     players: implicit - list of players in stage (PlayerStage)
   """

   index = db.IntegerProperty()
   game = db.ReferenceProperty(Game, collection_name="stages")
   currentvote = db.ReferenceProperty(Vote)

class Day(Stage):
   """Storage for a day of a game

   Properties
     votes: implicit - list of votes
   """
   pass

class Night(Stage):
   """Storage for a day of a game

   Properties
   ...

   """
   pass


class Game(db.Model):
   """Storage for a game

   Properties
      name: Name of game
      creator: User who created the game
      created: datetime the game was created
      updated: datetime the game was updated
      published: Game is in play
      archived: Game over
      currentStage: current stage

      players: implicit - List of players participating
      stages: implicit - List of stages(days&nights)
   """
   name = db.StringProperty(required=True)
   currentStage = db.ReferenceProperty(Stage)
   password_hash = db.StringProperty(required=True)

   created = db.DateTimeProperty(auto_now_add=True)
   updated = db.DateTimeProperty(auto_now=True)
   archived = db.BooleanProperty(default=False)
   published = db.BooleanProperty(default=False)
   locked = db.BooleanProperty(default=False)

   @staticmethod
   def get_current_user_games_moderating():
      """Returns the games that the current user has moderator access"""
      return Game.get_user_games_moderating(users.GetCurrentUser())

   @staticmethod
   def get_user_games_moderating(user):
      """Returns the games that the given user has moderator access"""
      if not user: return []
      moderating = db.Query(GameModerator).filter('user =', user)
      return [m.game for m in moderating]

   @staticmethod
   def get_current_user_games_playing():
      """Returns the games that the current user has joined"""
      return Game.get_user_games_playing(users.GetCurrentUser())

   @staticmethod
   def get_user_games_playing(user):
      """Returns the games that the given user has joined"""
      if not user: return []
      playing = db.Query(GamePlayer).filter('user =', user)
      return [p.game for p in playing]

   def current_user_moderating(self):
      """Returns true if the current user has moderator access to this game."""
      return self.user_moderating(users.GetCurrentUser())

   def user_moderating(self, user):
      """Returns true if the given user has moderator acces to this game."""
      if not user: return False
      query = db.Query(GameModerator)
      query.filter('game =', self)
      query.filter('user =', user)
      return query.get()

   def current_user_playing(self):
      """Returns true if the current user has joined this game"""
      return self.user_playing(users.GetCurrentUser())

   def user_playing(self, user):
      """Returns true if the given user has joined this game"""
      if not user:
         return False
      query = db.Query(GamePlayer)
      query.filter('game =', self)
      query.filter('user =', user)
      return query.get()

class GamePlayer(db.Model):
   """Represents the many-to-many relationship between Games and Users

   Game Player ACL

   Properties
     user: related user
     game: related game
   """
   user = db.UserProperty(required=True)
   game = db.ReferenceProperty(Game,required=True)

class GameModerator(db.Model):
   """Represents the many-to-nany relationship between Games and Users

   Game Moderator ACL

   Properties
     user: related user
     game: related game
   """
   user = db.UserProperty(required=True)
   game = db.ReferenceProperty(Game,required=True)

class StageGamePlayer(db.Model):
   """Represents the many-to-many relationship between Stages and GamePlayers

   Properties
        player: related player
        stage: related stage
   """
   stage = db.ReferenceProperty(Stage, required=True)
   player = db.ReferenceProperty(GamePlayer, required=True)

   alive = db.BooleanProperty(required=True, default=False)


class Vote(db.Model):
   """Represents the one-to-many relationship between Stages and Votes
    This is the vote class (like a poll).
    Properties
        day: related day(stage)

        StageGamePlayers: indirect - players in stage (get from Stage)

     """
   name = db.StringProperty()
   created = db.DateTimeProperty(auto_now_add=True)
   updated = db.DateTimeProperty(auto_now=True)
   archived = db.BooleanProperty(default=False)
   published = db.BooleanProperty(default=False)

   day = db.ReferenceProperty(Day, collection_name="votes")
   index = db.IntegerProperty()

class VoteGamePlayer(db.Model):
   """Represents the many-to-many relationship between Votes and Players
   """
   choice = db.ReferenceProperty(StageGamePlayer, required=True)
   player = db.ReferenceProperty(GamePlayer, required=True)
   vote = db.ReferenceProperty(Vote, required=True)
   
   
   
   
