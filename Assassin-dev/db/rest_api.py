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

#Authentication:
#curl --data "username=USERNAME_HERE&password=PASSWORD_HERE" http://cyclic.games/api-token-auth/

#REST_API_COMMANDS
#curl -X GET http://cyclic.games/gamesData/ -H "Authorization: Token TOKEN_HERE"
#curl -X GET http://cyclic.games/getTarget/84 -H "Authorization: Token TOKEN_HERE"
#curl -X GET http://cyclic.games/getLeaderboard/97 -H "Authorization: Token TOKEN_HERE"
#curl -X GET http://cyclic.games/getTarget/84 -H "Authorization: Token TOKEN_HERE"


#curl -X GET http://cyclic.games/getTarget/84 -H "Authorization: Token TOKEN_HERE"

#curl -X GET http://cyclic.games/increaseScore/96/270/5 -H "Authorization: Token TOKEN_HERE"


# Serializers define the API representation.


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
# curl -X GET http://cyclic.games/getGameID/"GAME_STRING" -H "Authorization: Token TOKEN_HERE"

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
    

def getToken(request):
    if signedIn(request):
        try:
            del request.session['getToken']
            token,created= Token.objects.get_or_create(user = User.objects.get(id = request.session['user']))
            template = loader.get_template('db/get-token.html')
            info = {'signedIn':signedIn(request), 'user':getUser(request),'discord_code':token.key}
            return HttpResponse(template.render(info,request))
        except:
            print(traceback.print_exc())
        request.session['getToken'] = True
        return HttpResponseRedirect(reverse('index'))
    request.session['getToken'] = True
    return HttpResponseRedirect(reverse('index'))

