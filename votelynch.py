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

# Salt value for password hash value generation
MMSALT = "a8b8d8e8t8g"

#import from external py files
from handlers import *
from models import *

def main():
   application = webapp.WSGIApplication([
      ('/', MainPage),
         """Display games moderating and participaing.

         Links:
            create game (/creategame)

         Template variables:
            list_of_games_playing
            list_of_games_moderating
            archive (flag if archives are being displayed)
         """

      ('/creategame', CreateGamePage),
         """Page to create a game.

         Form fields:
            name
            password
         """

      ('/creategame.do', CreateGameAction),
         """POST action to create game

         POST fields:
            name
            password

         Handler:
            Creates new game
            Redirects to /managegame?game=<newgameid>
         """

      ('/managegame', ManageGamePage),
         """url: /managegame?game=<gameid>
         Displays state of game to moderator.
          List of GameStagePlayers and isAlive status

         Links:
            Create vote (/createvote?game=<gameid>)
            Next stage (/createstage?game=<gameid>)
            Links for template variable data (see below)

         Template variables:
            list_of_stages
            list_of_votes (for current stage)
            currentstage
         """
      ('/createstage.do', CreateStageAction),
         """POST action to create stage

         POST fields:
            game

         Handler:
            Creates new stage and new StageGamePlayer relationships for each player
            redirects to /managestage?stage=<stageid>
         """

      ('/managestage', ManageStagePage),
         """url: /managestage?game=<gameid>
         Page to start/manage stage of the game.

         createstage.do redirects here after creating a new stage
         The moderator must then pick the live players and start the stage

         Stages will default to automate between day and night
          but the moderator can choose to override that
          (option box - Day/Night)

         A list of players from the stage should be on the page
          with a tick box next to their name. This is for the moderator
          to select the players who died in the previous stage
           (list of StageGamePlayers - tick boxes)

         Template Variables:
            list_of_stagegameplayers
            is_day (1 = day, 0 = night - defaults to correct value)


         NOTE: This page may be deemed redundant. This information can all be on the
          manage game page. Moderator creates a new stage. All players are copied over
          and before the moderator starts the new stage he can choose which players to
          be alive. For now we'll leave these as seperate pages and merge them at a
          later time
         """
      ('/createvote.do', CreateVoteAction),
         """POST action to create a vote
         url: /createvote.do?game=<gameid>

         Creates a new vote in the current stage of the game
         by default adds all alive players, moderators can remove from the manage page
         redirects to /managevote?vote=<voteid>
         """

      ('/managevote', ManageVotePage),
         """ url: /managevote?vote=<voteid>

         Page for moderator to manage vote
         Allows moderator to open and close voting

         Links/Buttons:
            Open - /openvote.do?vote=<voteid>
            Close - /closevote.do?vote=<voteid>
            End - /endvote.do?vote=<voteid>

         Template variables:
            list_of_gamestageplayers - should show who they voted for

            created
            updated
            archived
            published

            day_index
            vote_index
         """

      ('/openvote.do', OpenVoteAction),
         """ url: /openvote.do?vote=<voteid>

         Opens vote for players to cast their choice
         """
      ('/closevote.do', CloseVoteAction),
         """ url: /closevote.do?vote=<voteid>

         Closes vote so players cannot vote
         """

      ('/join', JoinGamePage),
         """/join?game=<gameid>

         Page for players to join the game. They will need the url from the moderator and the password
         They choose their alias to use for the game. (perhaps default to last used alias)
          We don't want email addresses for player names

         Form fields
            password
            alias

         Template variables:
            game_name
            alias (users most recently used alias)
         """

      ('/joingame.do', JoinGameAction),
         """ POST action to join a game

         Post fields:
            alias (player chooses name
            password
            game

         redirects to /play?game=<gameid>
         """

      ('/play', PlayGamePage),
         """
         Page to display state of game to players
         Just a live list and links to active votes
         
         Template variables:
            currentstage
            list_of_live_stagegameplayers
            list_of_votes
         """
         
      ('/vote', VotePage),
         """url: /vote?vote=<voteid>
         
         Players view vote options to vote, or voting results
         
         Template variables:
            list_of_gamestageplayers
            vote_cast (set if player has already voted, should be selected on the page)
         """

      ('/castvote.do', CastVoteAction),
         """Post action to cast a vote
         
         Post fields:
            vote (id of the vote)
            choice (players choice - choice is an id from list_of_gamestageplayers)
            
         """

      ('/addmoderator.do', AddModeratorAction),
         """ Post action to add a moderator to a game
            Moderator supplies email of user to add
         
         Post fields:
            email
            game
         """
         
      ], debug=_DEBUG)
   wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
   main()
#     print "Hello ichthys!"
#     print "lol sup john"
#     print "maybe poo will come too"
#     wow double #'s make bright comments in np++, remove'dded em

