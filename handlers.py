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
      
      # Name and password for game
      name = self.request.get('name')
      password = self.request.get('password')
      
      if not user or not name or not password:
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
         self.redirect('/managegame?game=' + str(game.key()))

class ManageGamePage(BaseRequestHandler):
   """url: /managegame?game=<gameid>
         Displays state of game to moderator.
          List of stagegameplayers and isAlive status

         Links:
            Create vote (/createvote?game=<gameid>)
            Next stage (/createstage?game=<gameid>)
            Links for template variable data (see below)

         Template variables:
            list_of_stages
            list_of_votes (for current stage)
            current_stage
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
      if game.currentStage:
         current_stage = Stage.get(game.currentStage)
         list_of_votes = currentstage.votes
      else:
         current_stage = None
         list_of_votes = []
      
      self.generate('managegame.html', {
         'list_of_stages': list_of_stages,
         'list_of_votes': list_of_votes,
         'current_stage': current_stage, #potentially NULL
         })


class CreateStageAction(BaseRequestHandler):
   """POST action to create stage

         POST fields:
            game

         Handler:
            Creates new stage and new StageGamePlayer relationships for each player
            redirects to /managestage?stage=<stageid>
   """
   @login_required
   def post(self):
      game = Game.get(self.request.get('game'))
      
      if not game:
         self.error(403)         # game does not exist
         return
      
      if not game.current_user_moderating():
         self.error(403)
         return
      
      #need the currentStage for index and day/night swap
      if game.currentStage:
         current_stage = game.currentStage
         new_stage = Stage(index = current_stage.index + 1, game = game)
         new_stage.isDay = not current_stage.isDay
         for player in current_stage.StageGamePlayer_set:
            #copy values from previous StageGamePlayer relationships
            new_player = StageGamePlayer(stage = new_stage,
                                         player = player.player,
                                         isAlive = player.isAlive)
            new_player.put()
            
      else:
         new_stage = Stage(index = 0, game = game, isDay = True)
         for player in game.GamePlayer_set:
            #create values from players in game
            new_player = StageGamePlayer(stage = new_stage,
                                         player = player,
                                         isALive = True)
            new_player.put()
      
      new_stage.put()
      
      self.redirect('/managestage?stage=' + str(new_stage.key()))
      
class ManageStagePage(BaseRequestHandler):
   """url: /managestage?stage=<stage>
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
            stage

         NOTE: This page may be deemed redundant. This information can all be on the
          manage game page. Moderator creates a new stage. All players are copied over
          and before the moderator starts the new stage he can choose which players to
          be alive. For now we'll leave these as seperate pages and merge them at a
          later time
   """
   @login_required
   def get(self):
      stage = Stage.get(self.request.get('stage'))
      
      if not stage:
         self.error(403)         # stage does not exist
         return
      
      game = stage.game
      
      if not game.current_user_moderating():
         self.error(403)
         return
      
      list_of_stagegameplayers = [p for p in stage.StageGamePlayers_set]
                  
      self.generate('managestage.html', {
         'list_of_stagegameplayers': list_of_stagegameplayers,
         'stage': stage
         })

class ManageStageAction(BaseRequestHandler):
   """ url: /managestage.do
   
         POST action to update stage (selecting alive players)
   """
   pass

class KillPlayerAction(BaseRequestHandler):
   """
      url: /killplayer.do?player=<StageGamePlayer_id>
      
         sets a players isAlive to False
   """
   @login_required
   def post(self):
      player = StageGamePlayer.get(self.request.get('player'))
      
      if not player:
         self.error(403)
         return
      
      if not player.stage.game.current_user_moderating():
         self.error(403)
         return
      
      player.isAlive = False
      player.put()

class RevivePlayerAction(BaseRequestHandler):
   """
      url: /reviveplayer.do?player=<StageGamePlayer_id>
      
         sets a players isAlive to True
   """
   @login_required
   def post(self):
      player = StageGamePlayer.get(self.request.get('player'))
      
      if not player:
         self.error(403)
         return
      
      if not player.stage.game.current_user_moderating():
         self.error(403)
         return
      
      player.isAlive = True
      player.put()

class CreateVoteAction(BaseRequestHandler):
   """POST action to create a vote
         url: /createvote.do?game=<gameid>

         Creates a new vote in the current stage of the game
         by default adds all alive players, moderators can remove from the manage page
         redirects to /managevote?vote=<voteid>
   """
   @login_required
   def post(self):
      game = Game.get(self.request.get('game'))
      
      if not game:
         self.error(403)         # game does not exist
         return
      
      if not game.current_user_moderating():
         self.error(403)
         return
      
      #need the currentStage to add vote to
      if not game.currentStage:
         self.error(403)
         return
      
      
      current_stage = game.currentStage
      
      if current_stage.currentVote:
         index = current_stage.currentVote.index + 1
      else:
         index = 0
         
      new_vote = Vote(stage = current_stage, index = index)
      
      new_vote.put()
      self.redirect('/managevote?vote=' + str(new_vote.key()))

class ManageVotePage(BaseRequestHandler):
   """ url: /managevote?vote=<voteid>

         Page for moderator to manage vote
         Allows moderator to open and close voting

         Links/Buttons:
            Open - /openvote.do?vote=<voteid>
            Close - /closevote.do?vote=<voteid>
            End - /endvote.do?vote=<voteid>

         Template variables:
            list_of_stagegameplayers - should show who they voted for

            created
            updated
            archived
            published

            day_index
            vote_index
   """
   @login_required
   def get(self):
      vote = Vote.get(self.request.get('vote'))
      
      if not vote:
         self.error(403)
         return
         
      if not vote.stage.game.current_user_moderating():
         self.error(403)
         return
      
      list_of_stagegameplayers = vote.stage.players
      
      self.generate('managevote.html', {
         'list_of_stagegameplayers': list_of_stages,
         'vote': vote,
         'stage': vote.stage,
         'game': vote.stage.game,
         })

class OpenVoteAction(BaseRequestHandler):
   """ url: /openvote.do?vote=<voteid>

         Opens vote for players to cast their choice
   """
   @login_required
   def post(self):
      vote = Vote.get(self.request.get('vote'))
      
      if not vote:
         self.error(403)
         return
      
      if not vote.stage.game.current_user_moderating():
         self.error(403)
         return
      
      vote.isOpen = True
      vote.put()
      
      if self.request.get('next'):
         self.redirect(self.request.get('next'))

class CloseVoteAction(BaseRequestHandler):
   """ url: /closevote.do?vote=<voteid>

         Closes vote so players cannot vote
   """
   @login_required
   def post(self):
      vote = Vote.get(self.request.get('vote'))
      
      if not vote:
         self.error(403)
         return
      
      if not vote.stage.game.current_user_moderating():
         self.error(403)
         return
      
      vote.isOpen = False
      vote.put()
      
      if self.request.get('next'):
         self.redirect(self.request.get('next'))

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
            #alias (users most recently used alias)
   """
   
   @login_required
   def get(self):
      game = Game.get(self.request.get('game'))
      
      if not game:
         self.error(403)         # game does not exist
         return
      
      #Check if user is already in the game
      user = users.GetCurrentUser()
      if user in game.players:
         self.redirect('/play?game=' + str(game.key()))
      
      self.generate('joingame.html', {
         'game_name': game.name,
         })

class JoinGameAction(BaseRequestHandler):
   """ POST action to join a game

         Post fields:
            alias (player chooses name
            password
            game

         redirects to /play?game=<gameid>
   """
   @login_required
   def post(self):
      game = Game.get(self.request.get('game'))
      
      if not game:
         self.error(403)         # game does not exist
         return
      
      #Check if user is already in the game
      user = users.GetCurrentUser()
      if user in game.players:
         self.redirect('/play?game=' + str(game.key()))
      
      alias = self.request.get('alias')
      # Need to introduce some alias input checks here
      if not alias:
         self.error(403)
         return
      
      password = self.request.get('password')
      if (md5(MMSALT+password) != game.password_hash):
         self.error(403)
         return
      
      new_gameplayer = GamePlayer(user = user, game = game)
      new_gameplayer.put()
      
      self.redirect('/play?game=' + str(game.key()))


class PlayGamePage(BaseRequestHandler):
   """
      url:/play?game=<gameid>
      
         Page to display state of game to players
         Just a live list and links to active votes

         Template variables:
            current_stage
            list_of_live_stagegameplayers
            list_of_dead_stagegameplayers
            list_of_votes
   """
   @login_required
   def get(self):
      game = Game.get(self.request.get('game'))
      
      if not game:
         self.error(403)
         return
         
      user = users.GetCurrentUser()
      
      # User needs to join game
      if user not in game.players:
         self.redirect('/joingame?game=' + str(game.key())
      
      list_of_live_stagegameplayers = []
      list_of_dead_stagegameplayers = []
      
      for player in game.players:
         if player.isAlive:
            list_of_live_stagegameplayers.append(player)
         else:
            list_of_dead_stagegameplayers.append(player)
      
      self.generate('play.html', {
         'current_stage': game.currentStage,
         'list_of_live_stagegameplayers': list_of_live_stagegameplayers,
         'list_of_dead_stagegameplayers': list_of_dead_stagegameplayers,
         'list_of_votes': game.currentStage.votes,
         })

class VotePage(BaseRequestHandler):
   """url: /vote?vote=<voteid>

         Players view vote options to vote, or voting results

         Template variables:
            list_of_live_stagegameplayers
            vote_cast (set if player has already voted, should be selected on the page)
   """
   @login_required
   def get(self):
      vote = Vote.get(self.request.get('vote'))
      
      if not vote:
         self.error(403)
         return
      
      user = users.GetCurrentUser()
      
      list_of_live_stagegameplayers = vote.stage.players.filter('isAlive =', True)
      
      stagegameplayer = \
         next((p for p in list_of_live_stagegameplayers if p.player.user == user),
               None)
      
      # User is not in game and alive
      if not stagegameplayer:
         self.error(403)
         return
      
      choice = vote.choices.filter('player =', stagegameplayer.player).choice
      
      self.generate('vote.html', {
         'list_of_live_stagegameplayers': list_of_live_stagegameplayers,
         'vote_cast': choice,
      })

class CastVoteAction(BaseRequestHandler):
   """Post action to cast a vote

         Post fields:
            vote (id of the vote)
            choice (players choice - choice is an id from list_of_stagegameplayers)

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
