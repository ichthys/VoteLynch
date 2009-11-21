#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import datetime
import os
import random
import string
import sys
import wsgiref.handlers

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required

# Add our custom Django template filters to the built in filters
template.register_template_library('templatefilters')

# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True


## forward declarations (redefined later)
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
   game = db.Reference(Game)
   currentvote = db.Reference(Vote)
    
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
   currentStage = db.Reference(Stage)
   
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
   game = db.Reference(Game,required=True)

class GameModerator(db.Model):
   """Represents the many-to-nany relationship between Games and Users
    
   Game Moderator ACL
    
   Properties
     user: related user
     game: related game
   """
   user = db.UserProperty(required=True)
   game = db.Reference(Game,required=True)
    
class StageGamePlayer(db.Model):
   """Represents the many-to-many relationship between Stages and GamePlayers
    
   Properties
        player: related player
        stage: related stage
   """
   stage = db.Reference(Stage, required=True)
   player = db.Reference(GamePlayer, required=True)
    
   alive = db.BooleanProperty(required=True, default=False)
    

class Vote(db.Model):
   """
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
     
   day = db.Reference(Day)
   index = db.IntegerProperty()
  
class VoteGamePlayer(db.Model):
   """Represend the many-to-many relationship between Votes and Players
   """
   choice = db.Reference(StageGamePlayer, required=True)
   player = db.Reference(GamePlayer, required=True)
   vote = db.Reference(Vote, required=True)
  
class BaseRequestHandler(webapp.RequestHandler):
   """Supplies a common template generation function.

   When you call generate(), we augment the template variables supplied with
   the current user in the 'user' variable and the current webapp request
   in the 'request' variable.
   """
   def generate(self, template_name, template_values={}):
      values = {
            'request': self.request,
            'user': users.GetCurrentUser(),
            'login_url': users.CreateLoginURL(self.request.uri),
            'logout_url': users.CreateLogoutURL('http://' + self.request.host + '/'),
            'debug': self.request.get('deb'),
            'application_name': 'VoteLynch',
         }
      values.update(template_values)
      directory = os.path.dirname(__file__)
      path = os.path.join(directory, os.path.join('templates', template_name))
      self.response.out.write(template.render(path, values, debug=_DEBUG))

class MainPage(BaseRequestHandler):
   """Lists the games moderating and playing for the current user."""
   @login_required
   def get(self):
      games_playing = Game.get_current_user_games_playing()
      games_moderating = Game.get_current_user_games_moderating()
      show_archive = self.request.get('archive')
      if not show_archive:    # get only non archived games
         non_archived = []
         for game in games_playing:
            if not game.archived:
               non_archived.append(game)
         games_playing = non_archived
         non_archived = []
         for game in games_moderating:
            if not game.archived:
               non_archived.append(game)
         games_moderating = non_archived
      self.generate('index.html', {
         'games_playing': games_playing,
         'games_moderating': games_moderating,
         'archive': show_archive,
         })
    
class CreateGamePage(BaseRequestHandler):
   """Page to create a new game
   """

   @login_required
   def get(self):
      self.generate('create.html', {})
        
class CreateGameAction(BaseRequestHandler):
   """Creates a new game
   
      Recieves (name,password) from post
      creates game - redirects to /managegame/?game=<newgameid>
   """
   def post(self):
      user = users.GetCurrentuser()
      name = self.request.get('name')

      if not user or not name:
         self.error(403)
         return

      game = Game(name=name)
      game.put()

      game_moderator = GameModerator(game=game, user=user)
      game_moderator.put()

      if self.request.get('next'):
         self.redirect(self.request.get('next'))
      else:
         self.redirect('/manage?id' + str(game.key()))

class ManageGamePage(BaseRequestHandler):
    """Page to show the moderator status of game, progress to new stage or create votes
        for current stage"""
    
    def get(self):
        game = Game.get(self.request.get('id'))
        
        if not game:
            self.error(403)         # game does not exist
            return
            
        if not game.current_user_moderating():
            pass
        
def main():
   application = webapp.WSGIApplication([
      ('/', MainPage),
         #Display games moderating and participaing. Links to create game

         #list_of_games_playing
         #list_of_games_moderating

      ('/creategame', CreateGamePage),
         #Page to create a game. Fields: (name, password)

      ('/creategame.do', CreateGameAction),
         #post - (name,password) to create game 
         #redirects to /managegame/?game=<newgameid>

      ('/managegame', ManagePage),
         #/managegame/?game=<gameid>
         #displays state of game to moderator
            #links to create a next stage or create a vote for current stage

         #information needed
               #list_of_stages, currentstage, list_of_votes (for currentstage)
               #(links on all of these)
            #other links needed
               #create new vote, create next stage
      ('/createstage.do', CreateStageAction),
         #post - (gameid)
         
         #creates a new stage for the current game
         
         #redirects to /managestage/?stage=<stageid>
      ('/managestage', ManageStagePage),
         #/managestage/?stage=<stageid>
         
         #lets moderators pick live players for stage
         #Defaults to all players alive from previous stage
         
         #Have a list of players with checkboxes.
         #Each live player from previous stage checkbox is default to true
         
         #list_of_stagegameplayers
         
      ('/createvote.do', CreateVoteAction),
         #post - (gameid)    Creates a new vote in the current stage of the game
         # by default adds all alive players, moderators can remove from the manage page
         #redirects to /managevote/?vote=<voteid>
      ('/managevote', CreateVotePage),
         #/managevote/?vote=<voteid>
         #moderators view vote page
         #allows moderator to open and close voting

         #list_of_gamestageplayers (all alive)
      ('/join', JoinGamePage),
         #/join/?game=<gameid>
         #page for players to join the game. They will need the url from the moderator and the password
         #they choose their alias to use for the game. (perhaps default to last used alias)
         #we don't want email addresses for player names
         #fields: (password, alias)

      ('/joingame.do', JoinGameAction),
         #post - (game, password, alias)
         #Post action to add player to a game
         #redirects to (/play/?game=<gameid>)

      ('/play', PlayGamePage),
         #Page to display state of game to players
         #Just a live list and links to active any votes

         #information
            #currentstage
            #list_of_live_stagegameplayers, list_of_votes
      

      ('/vote', VotePage),
         #/vote/?vote=<voteid>
         #Players view vote options to vote, or voting results

         #list_of_gamestageplayers
      ('/castvote.do', CastVoteAction),
         #post - (vote, choice)
            #choice is an id from list_of_gamestageplayers

      ('/addmoderator.do', AddModeratorAction),
         #post - (email, game)
         #moderator supplies email of user to add
      ], debug=_DEBUG)
   wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
   main()
##     print "Hello ichthys!"
##     print "lol sup john"
##     print "maybe poo will come too"
