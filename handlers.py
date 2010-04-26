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
            games_playing = [game for game in games_playing if not game.archived]
            games_moderating = [game for game in games_moderating if not game.archived]
         self.generate('index.html', {
            'list_of_games_playing': games_playing,
            'list_of_games_moderating': games_moderating,
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
         creates game - redirects to /managegame?game=<newgameid>
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
      """Page to show the moderator status of game, progress to new stage or create votes
        for current stage"""

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
      """placeholder"""
      pass

   class ManageStagePage(BaseRequestHandler):
      """placeholder"""
      pass

   class CreateVoteAction(BaseRequestHandler):
      """placeholder"""
      pass

   class ManageVotePage(BaseRequestHandler):
      """placeholder"""
      pass

   class OpenVoteAction(BaseRequestHandler):
      """place holder"""
      pass

   class CloseVoteAction(BaseRequestHandler):
      """place holder"""
      pass

   class JoinGamePage(BaseRequestHandler):
      """placeholder"""
      pass

   class JoinGameAction(BaseRequestHandler):
      """placeholder"""
      pass

   class PlayGamePage(BaseRequestHandler):
      """placeholder"""
      pass

   class VotePage(BaseRequestHandler):
      """placeholder"""
      pass

   class CastVoteAction(BaseRequestHandler):
      """placeholder"""
      pass

   class  AddModeratorAction(BaseRequestHandler):
      """placeholder"""
      pass

