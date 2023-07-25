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

from . import basic_views
from . import game_views
from . import extra_views

from . import rest_api


urlpatterns = [

    path('login/', basic_views.login, name='login'),
    path('signup/', basic_views.signup, name='signup'),
    path('', basic_views.index, name='index'),
    path('home/',basic_views.home,name='home'),
    path('faq/',basic_views.faq,name='faq'),
    path('signup/post/',basic_views.signUpPost,name='signuppost'),
    path('signout/',basic_views.signOut,name='signOut'),
    path('login/post',basic_views.loginPost,name='loginpost'),
    path('user/<int:userID>',basic_views.profile,name='profile'),
    path('user-settings',basic_views.userSettings,name='userSettings'),
    path('user-settings/post',basic_views.userSettingsPost,name='userSettingsPost'),
    path('getPassword',basic_views.getPassword,name='getPassword'),
    path('getPasswordPost',basic_views.getPasswordPost,name='getPasswordPost'),
    path('joingame',game_views.joinGame,name='joinGame'),
    path('startGame',game_views.startGame,name='startGame'),
    path('startGame/post',game_views.startGamePost,name='startGamePost'),
    path('joinGame',game_views.joinGame,name='jointGame'),
    path('joinGame/post',game_views.joinGamePost,name='joinGamePost'),
    path('game/<int:gameID>',game_views.game,name='game'),
    path('startPlaying/<int:gameID>',game_views.startPlaying,name='startPlaying'),
    path('modKill/<int:gameID>/<int:assassinPlayerID>/<int:assassinatedPlayerID>/',game_views.modKill,name='modKill'),
    path('modReverseDeath/<int:gameID>/<int:assassinPlayerID>/<int:assassinatedPlayerID>/',game_views.modReverseDeath,name='modReverseDeath'),
    path('confirmDeath/<int:playerID>',game_views.confirmDeath,name='confirmDeath'),
    path('confirmKill/<int:playerID>',game_views.confirmKill,name='confirmKill'),
    path('game-settings/<int:gameID>',game_views.gameSettings,name='gameSettings'),
    path('game-settings/post/<int:gameID>',game_views.gameSettingsPost,name='gameSettingsPost'),
    path('deletP/<int:gameID>/<int:playerID>',game_views.deletePlayer,name='deletePlayer'),
    path('mod-help',game_views.modHelp,name='modHelp'),
    path('deletG/<int:gameID>/',game_views.deleteGame,name='deleteGame'),
    path('contactMod/<int:gameID>/',game_views.contactMod,name='contactMod'),
    path('killVideo/<int:killerID>/<int:targetID>/<int:gameID>',extra_views.killVideo,name ='killVideo'),
    path('killVideo/post/<int:killerID>/<int:targetID>/<int:gameID>',extra_views.killVideoPost,name ='killVideoPost'),
    path('allowVideoUsePost/<int:killedID>/<int:gameID>',extra_views.allowVideoUsePost,name ='allowVideoUsePost'),
    path('termsConditions',basic_views.termsConditions,name ='termsConditions'),
    path('contract/<int:gameID>',game_views.contract,name ='contract'),
    path('contractExtraInfo/<int:gameID>',game_views.contractExtraInfo,name ='contractExtraInfo'),
    path('intro',basic_views.intro,name ='intro'),
    path('autoJoin/<int:gameID>',game_views.autoJoin,name ='autoJoin'),
    path('contractPost/<int:gameID>',game_views.contractPost,name ='contractPost'),
    path('contractExtraInfoPost/<int:gameID>',game_views.contractExtraInfoPost,name ='contractExtraInfoPost'),
    path('testAuth',rest_api.TestAuthView.as_view()),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/login', basic_views.login, name='login'),
    path('gamesData', rest_api.ListGames.as_view()),
    path('api-token-auth/', authviews.obtain_auth_token),
    path('getGameID/<str:gameString>',rest_api.GetGameID.as_view()),
    path('getTarget/<int:gameID>',rest_api.GetTarget.as_view()),
    path('getLeaderboard/<int:gameID>',rest_api.GetLeaderboard.as_view()),
    path('increaseScore/<int:gameID>/<int:playerID>/<int:amount>',rest_api.IncreaseScore.as_view()),
    path('randomizeTargets/<int:gameID>', game_views.randomizeTargets, name='randomizeTargets'),
    path('duelSubmissionPost/<int:gameID>', game_views.duelSubmissionPost, name='duelSubmissionPost'),
    path('duelSubmission/<int:gameID>', game_views.duelSubmission, name='duelSubmission'),
    path('getToken', rest_api.getToken, name="getToken"),
    path('checkout',extra_views.checkout,name='checkout'),

    
]
