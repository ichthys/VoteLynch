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
      ('/creategame', CreateGamePage),
      ('/creategame.do', CreateGameAction),
      ('/managegame', ManageGamePage),
      ('/createstage.do', CreateStageAction),
      ('/managestage', ManageStagePage),
      ('/managestage.do', ManageStageAction),
      ('/killplayer.do', KillPlayerAction),
      ('/reviveplayer.do', RevivePlayerAction),
      ('/createvote.do', CreateVoteAction),
      ('/managevote', ManageVotePage),
      ('/openvote.do', OpenVoteAction),
      ('/closevote.do', CloseVoteAction),
      ('/join', JoinGamePage),
      ('/joingame.do', JoinGameAction),
      ('/play', PlayGamePage),
      ('/vote', VotePage),
      ('/castvote.do', CastVoteAction),
      ('/addmoderator.do', AddModeratorAction),
      ], debug=_DEBUG)
   wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
   main()
