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
   """Display games moderating and participaing.

         Links:
            create game (/creategame)

         Template variables:
            list_of_games_playing
            list_of_games_moderating
            archive (flag if archives are being displayed)
   """
   @login_required
   def get(self):
      games_playing = Game.get_current_user_games_playing()
      games_moderating = Game.get_current_user_games_moderating()
      show_archive = self.request.get('archive')
      if not show_archive:    # get only non archived games
         games_playing = [game for game in games_playing if not game.archived]
         games_moderating = [game for game in games_moderating if not game.archived]
      self.generate('index.html', {
         'list_of_games_playing': games_playing,
         'list_of_games_moderating': games_moderating,
         'archive': show_archive,
         })

class CreateGamePage(BaseRequestHandler):
   """Page to create a game.

         Form fields:
            name
            password
   """
   @login_required
   def get(self):
      self.generate('create.html', {})

class CreateGameAction(BaseRequestHandler):
   """POST action to create game

         POST fields:
            name
            password

         Handler:
            Creates new game
            Redirects to /managegame?game=<newgameid>
   """
   @login_required
   def post(self):
      user = users.GetCurrentuser()
      name = self.request.get('name')
      password = self.request.get('password')

      if not user or not name or not pasword:
         self.error(403)
         return

      password_hash = md5(MMSALT+password)

      game = Game(name=name, password_hash = password_hash)
      game.put()

      game_moderator = GameModerator(game=game, user=user)
      game_moderator.put()

      if self.request.get('next'):
         self.redirect(self.request.get('next'))
      else:
         self.redirect('/manage?game=' + str(game.key()))

class ManageGamePage(BaseRequestHandler):
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
   @login_required
   def get(self):
      game = Game.get(self.request.get('game'))

      if not game:
         self.error(403)         # game does not exist
         return

      if not game.current_user_moderating():
         self.error(403)
         return

      list_of_stages = game.stages
      currentstage = Stage.get(game.currentStage)

      list_of_votes = currentstage.votes


class CreateStageAction(BaseRequestHandler):
   """POST action to create stage

         POST fields:
            game

         Handler:
            Creates new stage and new StageGamePlayer relationships for each player
            redirects to /managestage?stage=<stageid>
   """
   pass

class ManageStagePage(BaseRequestHandler):
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
   pass

class CreateVoteAction(BaseRequestHandler):
   """POST action to create a vote
         url: /createvote.do?game=<gameid>

         Creates a new vote in the current stage of the game
         by default adds all alive players, moderators can remove from the manage page
         redirects to /managevote?vote=<voteid>
   """
   pass

class ManageVotePage(BaseRequestHandler):
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
   pass

class OpenVoteAction(BaseRequestHandler):
   """ url: /openvote.do?vote=<voteid>

         Opens vote for players to cast their choice
   """
   pass

class CloseVoteAction(BaseRequestHandler):
   """ url: /closevote.do?vote=<voteid>

         Closes vote so players cannot vote
   """
   pass

class JoinGamePage(BaseRequestHandler):
   """/join?game=<gameid>

      Page for players to join the game.
      They will need the url from the moderator and the password
      They choose their alias to use for the game.
         (perhaps default to last used alias)
      We don't want email addresses for player names

         Form fields
            password
            alias

         Template variables:
            game_name
            alias (users most recently used alias)
   """
   pass

class JoinGameAction(BaseRequestHandler):
   """ POST action to join a game

         Post fields:
            alias (player chooses name
            password
            game

         redirects to /play?game=<gameid>
   """
   pass

class PlayGamePage(BaseRequestHandler):
   """
         Page to display state of game to players
         Just a live list and links to active votes

         Template variables:
            currentstage
            list_of_live_stagegameplayers
            list_of_votes
   """
   pass

class VotePage(BaseRequestHandler):
   """url: /vote?vote=<voteid>

         Players view vote options to vote, or voting results

         Template variables:
            list_of_gamestageplayers
            vote_cast (set if player has already voted, should be selected on the page)
   """
   pass

class CastVoteAction(BaseRequestHandler):
   """Post action to cast a vote

         Post fields:
            vote (id of the vote)
            choice (players choice - choice is an id from list_of_gamestageplayers)

   """
   pass

class  AddModeratorAction(BaseRequestHandler):
   """ Post action to add a moderator to a game
            Moderator supplies email of user to add

         Post fields:
            email
            game
   """
   pass
