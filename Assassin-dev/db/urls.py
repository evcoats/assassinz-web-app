from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf.urls import include
from django.contrib.auth.models import User
from .models import Game, Player, Profile, Mod
from rest_framework import routers, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken import views as authviews
from rest_framework import authentication
from rest_framework.authtoken.models import Token

import traceback

from . import views

#Authentication:
#curl -X GET http://127.0.0.1:8000/gamesData/ -H "Authorization: Token TOKEN_HERE"
#curl -X GET http://127.0.0.1:8000/getTarget/84 -H "Authorization: Token TOKEN_HERE"
#curl -X GET http://127.0.0.1:8000/getLeaderboard/97 -H "Authorization: Token TOKEN_HERE"
#curl -X GET http://127.0.0.1:8000/getTarget/84 -H "Authorization: Token TOKEN_HERE"


#curl -X GET http://127.0.0.1:8000/getTarget/84 -H "Authorization: Token TOKEN_HERE"

#curl -X GET http://127.0.0.1:8000/increaseScore/96/270/5 -H "Authorization: Token TOKEN_HERE"


# Serializers define the API representation.
class TestAuthView(APIView):
    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        return Response("Hello {0}!".format(request.user))

    def post(self, request, format=None):
        return Response("Hello {0}! Posted!".format(request.user))

class UserSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['url', 'username']

class GameSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Game
        fields = ['id','WitnessProtection','Safety','SafetyCircumstances','KillMethod','ExtraRules','phase','otherContactInfo','email','phone','killCam','compilationDone','limit']

class PlayerData(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    class Meta: 
        model = Player 
        fields = ['username','kills','alive','score']

    def get_username(self, obj):
        user = User.objects.get(id = obj.userID)
        return user.username


class TargetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    userID = serializers.SerializerMethodField()
    fullNameField = serializers.SerializerMethodField()
    usernameField = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ['id','userID','extraInfo','fullNameField','usernameField']
    
    def get_fullNameField(self, obj):
        profile = Profile.objects.get(userID = obj.userID)
        return profile.fullName
    
    def get_usernameField(self, obj):
        user = User.objects.get(id = obj.userID)
        return user.username

    def get_userID(self,obj):
        return obj.userID



class GamePlayerSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Player
        fields = ['userID','kills','alive','score','id']

class GameDataSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Game
        fields = ['id','WitnessProtection','Safety','SafetyCircumstances','KillMethod','ExtraRules','phase','otherContactInfo','phone','limit','teams','ExtraUserInfoString','gameString']

# ViewSets define the view behavior.
class ListGames(APIView):

    def get(self, request, *args, **kwargse):
        """
        Return a list of all users.
        """
        print("hello")
        print(" " + request.auth.key)
        print(request.user.username)
        if (request.user.username):
            try:
                ps = Player.objects.filter(userID = request.user.id)
                g = []
                for x in ps:
                    g.append(Game.objects.get(id=x.gameID))
                print("here")
                serializer = GameSerializer(g, many=True)
                return Response(serializer.data)
            except:
                print(traceback.print_exc())
                return Response(data={'error':"not-found",'status':"404"})

        return Response(data={'error':"not-found",'status':"404"})

class GamePlayerList(APIView):
    def get(self,request, *args, **kwargs):
        if (request.auth.key and request.user.username):
            try:
                ps = Player.objects.filter(userID = request.user.id)
                p = []
                for x in ps:
                    p2 = []
                    for y in Player.objects.get(userID = id):
                        p2.append(y)
                    p.append(p2)

                print("here")
                serializer = GamePlayerSerializer(p, many=True)
                return Response(serializer.data)
            except:
                print(traceback.print_exc())
                return Response(data={'error':"not-found",'status':"404"})
        return Response(data={'error':"not-found",'status':"404"})

class GetGameID(APIView):
    def get(self,request, gameString, *args, **kwargs):
        if (request.auth.key and request.user.username):
            try:
                # tProf = Profile.objects.get(userID = t.userID)
                g = Game.objects.get(gameString = gameString)
                m = Mod.objects.get(userID = request.user.id, gameID = g.id)

                serializer = GameDataSerializer(g)
                return Response(serializer.data)
            except:
                print(traceback.print_exc())
                return Response(data={'error':"not-found",'status':"404"})

        return Response(data={'error':"not-found",'status':"404"})


class GetTarget(APIView):
    def get(self,request, gameID, *args, **kwargs):
        if (request.auth.key and request.user.username):
            try:
                ps = Player.objects.get(userID = request.user.id, gameID = gameID)
                t = Player.objects.get(id = ps.targetID)
                # tProf = Profile.objects.get(userID = t.userID)
                serializer = TargetSerializer(t)
                return Response(serializer.data)
            except:
                print(traceback.print_exc())
                return Response(data={'error':"not-found",'status':"404"})

        return Response(data={'error':"not-found",'status':"404"})

class GetLeaderboard(APIView):
    def get(self,request, gameID, *args, **kwargs):
        try:
            ps = Player.objects.filter(gameID = gameID)
            # t = Player.objects.get(id = ps.targetID)
            # tProf = Profile.objects.get(userID = t.userID)
            serializer = PlayerData(ps,many=True)
            return Response(serializer.data)
        except:
            
            print(traceback.print_exc())
        return Response(data={'error':"not-found",'status':"404"})

class IncreaseScore(APIView):
    def get(self,request, playerID, gameID, amount, *args, **kwargs):
        if (request.auth.key and request.user.username):
            try:
                # tProf = Profile.objects.get(userID = t.userID)
                g = Game.objects.get(id = gameID)
                m = Mod.objects.get(userID = request.user.id, gameID = g.id)
                ps = Player.objects.get(id = playerID, gameID = gameID)
                score2 = ps.score + amount
                ps.score = score2
                ps.save()
                print("hello")
                serializer = GamePlayerSerializer(ps)
                return Response(serializer.data)
            except:
                print(traceback.print_exc())
                return Response(data={'error':"not-found",'status':"404"})

        return Response(data={'error':"not-found",'status':"404"})    


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'gamesData/', ListGames.as_view(),basename="gamesdata")
router.register(r'gamePlayerList/', ListGames.as_view(),basename="gamesdata")


# Routers provide an easy way of automatically determining the URL conf.

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
# curl -X GET http://127.0.0.1:8000/getGameID/6B8DYQMQ -H "Authorization: Token 284e63dc27e36f3fbbc431e860988a7128c7ccb4"

urlpatterns = [

    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('', views.index, name='index'),
    path('home/',views.home,name='home'),
    path('faq/',views.faq,name='faq'),
    path('signup/post/',views.signUpPost,name='signuppost'),
    path('signout/',views.signOut,name='signOut'),
    path('login/post',views.loginPost,name='loginpost'),
    path('joingame',views.joinGame,name='joinGame'),
    path('startGame',views.startGame,name='startGame'),
    path('startGame/post',views.startGamePost,name='startGamePost'),
    path('joinGame',views.joinGame,name='jointGame'),
    path('joinGame/post',views.joinGamePost,name='joinGamePost'),
    path('user/<int:userID>',views.profile,name='profile'),
    path('user-settings',views.userSettings,name='userSettings'),
    path('user-settings/post',views.userSettingsPost,name='userSettingsPost'),
    path('game/<int:gameID>',views.game,name='game'),
    path('startPlaying/<int:gameID>',views.startPlaying,name='startPlaying'),
    path('modKill/<int:gameID>/<int:assassinPlayerID>/<int:assassinatedPlayerID>/',views.modKill,name='modKill'),
    path('modReverseDeath/<int:gameID>/<int:assassinPlayerID>/<int:assassinatedPlayerID>/',views.modReverseDeath,name='modReverseDeath'),
    path('confirmDeath/<int:playerID>',views.confirmDeath,name='confirmDeath'),
    path('confirmKill/<int:playerID>',views.confirmKill,name='confirmKill'),
    path('game-settings/<int:gameID>',views.gameSettings,name='gameSettings'),
    path('game-settings/post/<int:gameID>',views.gameSettingsPost,name='gameSettingsPost'),
    path('deletP/<int:gameID>/<int:playerID>',views.deletePlayer,name='deletePlayer'),
    path('mod-help',views.modHelp,name='modHelp'),
    path('deletG/<int:gameID>/',views.deleteGame,name='deleteGame'),
    path('contactMod/<int:gameID>/',views.contactMod,name='contactMod'),
    path('getPassword',views.getPassword,name='getPassword'),
    path('getPasswordPost',views.getPasswordPost,name='getPasswordPost'),
    path('checkout',views.checkout,name='checkout'),
    path('killVideo/<int:killerID>/<int:targetID>/<int:gameID>',views.killVideo,name ='killVideo'),
    path('killVideo/post/<int:killerID>/<int:targetID>/<int:gameID>',views.killVideoPost,name ='killVideoPost'),
    path('allowVideoUsePost/<int:killedID>/<int:gameID>',views.allowVideoUsePost,name ='allowVideoUsePost'),
    path('termsConditions',views.termsConditions,name ='termsConditions'),
    path('contract/<int:gameID>',views.contract,name ='contract'),
    path('contractExtraInfo/<int:gameID>',views.contractExtraInfo,name ='contractExtraInfo'),
    path('intro',views.intro,name ='intro'),
    path('autoJoin/<int:gameID>',views.autoJoin,name ='autoJoin'),
    path('contractPost/<int:gameID>',views.contractPost,name ='contractPost'),
    path('contractExtraInfoPost/<int:gameID>',views.contractExtraInfoPost,name ='contractExtraInfoPost'),
    path('testAuth',TestAuthView.as_view()),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/login', views.login, name='login'),
    path('gamesData', ListGames.as_view()),
    path('api-token-auth/', authviews.obtain_auth_token),
    path('getGameID/<str:gameString>',GetGameID.as_view()),
    path('getTarget/<int:gameID>',GetTarget.as_view()),
    path('getLeaderboard/<int:gameID>',GetLeaderboard.as_view()),
    path('increaseScore/<int:gameID>/<int:playerID>/<int:amount>',IncreaseScore.as_view()),
    path('randomizeTargets/<int:gameID>', views.randomizeTargets, name='randomizeTargets'),
    path('duelSubmissionPost/<int:gameID>', views.duelSubmissionPost, name='duelSubmissionPost'),
    path('duelSubmission/<int:gameID>', views.duelSubmission, name='duelSubmission'),
    path('getToken', views.getToken, name="getToken")
    
]
