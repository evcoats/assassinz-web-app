def checkout(request):
    if signedIn(request):
        stripe.api_key = 'NONE'
        session = stripe.checkout.Session.create(
          payment_method_types=['card'],
          line_items=[{
            'price': 'price_1GvFJRHbXUyzkEEyL9ysmjuE',
            'quantity': 1
          }],
          mode='payment',
          success_url='https://example.com/success?session_id={CHECKOUT_SESSION_ID}',
          cancel_url='https://example.com/cancel',
        )
        info = {'session':session.id,'signedIn':signedIn(request), 'user':getUser(request)}
        template = loader.get_template('db/checkout.html')
        return HttpResponse(template.render(info,request))
    return HttpResponseRedirect(reverse('login'))

def killVideo(request,killerID,targetID,gameID):
    try:
        game = Game.objects.get(id = gameID)
        killer = Player.objects.get(id = killerID)

        if game.killCam == True and request.session['user'] == killer.userID and killer.targetID == targetID:
            if killer.killConfirmed == True:
                killer.killConfirmed = False
                killer.save()
                try:
                    kv = KillVideo.objects.get(killerID = killerID, killedID = targetID, gameID = gameID)
                    deleteKillVideo(kv.id)
                except:
                    print(traceback.print_exc())
                try:
                    kv = KillVideo.objects.get(killerID = killerID, targetID = targetID, gameID = gameID)
                    kv.delete()
                except:
                    pass
                return HttpResponseRedirect(reverse('index'))
            else:
                template = loader.get_template('db/submitKillVid.html')
                g = Game.objects.get(id = gameID)
                killCam = g.killCam
                killMethod = g.KillMethod
                info = {'signedIn':signedIn(request), 'user':getUser(request),'killerID':killerID,'targetID':targetID,'gameID':gameID, 'killCam': killCam, 'killMethod': killMethod}
                try:
                    info = {'signedIn':signedIn(request), 'user':getUser(request),'killerID':killerID,'targetID':targetID,'gameID':gameID,'error_message':request.session['error_message'], 'killCam':killCam, 'killMethod':killMethod}
                    del request.session['error_message']
                except:
                    pass
                return HttpResponse(template.render(info,request))
        return HttpResponseRedirect(reverse('login'))
    except Exception:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('login'))

def killVideoPost(request,killerID,targetID,gameID):
    try:
        game = Game.objects.get(id = gameID)
        killer = Player.objects.get(id = killerID)
        if request.method == 'POST':
            if game.killCam == True and request.session['user'] == killer.userID and killer.targetID == targetID and killer.killConfirmed == False:

                try:
                    form = VideoForm(request.POST, request.FILES)
                except:
                    request.session['error_message'] = "You must upload a video."
                    return HttpResponseRedirect(reverse('killVideo', kwargs = {'gameID' : game.id, 'killerID' : killerID, 'targetID' : targetID}))


                print(request.FILES)
                if request.FILES['video'].size < 10000000:
                    if request.FILES['video'].content_type[:5]=="video":
                        s3 = boto3.resource('s3',aws_access_key_id='NONE',aws_secret_access_key='NONE')
                        allowed = False
                        try:
                            if request.POST['compilationUse'] == "yes":
                                allowed = True
                        except:
                            pass
                        kv = KillVideo(killerID = killerID, killedID = targetID, gameID = gameID, usable = allowed)
                        try:
                            kv = KillVideo.objects.get(killerID = killerID, killedID = targetID, gameID = gameID)
                            if allowed == False:
                                kv.usable = False
                        except:
                            pass
                        kv.save()
                        s3.meta.client.upload_fileobj(request.FILES['video'], 'videosassassinlive', str(kv.id))
                        del request.FILES['video']
                        template = loader.get_template('db/killConfirmSuccess.html')
                        info = {'signedIn':signedIn(request), 'user':getUser(request),'gameID':gameID}
                        killer.killConfirmed = True
                        killer.save()
                        doubleConf(killerID, targetID, gameID)

                        return HttpResponse(template.render(info,request))
                    else:
                        request.session['error_message'] = "The file you uploaded is not recognized as a video."
                else:
                    request.session['error_message'] = "Video must be less than 10mb (try cutting down the length)"
                return HttpResponseRedirect(reverse('killVideo', kwargs = {'gameID' : game.id, 'killerID' : killerID, 'targetID' : targetID}))
            return HttpResponseRedirect(reverse('login'))
    except Exception:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('login'))

def deleteKillVideo(id):
    kv = KillVideo.objects.get(id = id)
    s3 = boto3.resource('s3',aws_access_key_id='NONE',aws_secret_access_key='NONE')
    s3.meta.client.delete_object(Bucket = 'videosassassinlive', Key = str(id))
    kv.delete()

def createCompilation(gameID):
    try:
        s3 = boto3.resource('s3',aws_access_key_id='NONE',aws_secret_access_key='NONE')
        v = None
        a = None
        if KillVideo.objects.filter(gameID = gameID,usable=True).count() == 0:
            return False
        for x in KillVideo.objects.filter(gameID = gameID,usable=True):
            try:
                print(str(x.id))
                s3.meta.client.download_file('videosassassinlive', str(x.id),str(x.id)+".mp4")
                if v == None and a == None:
                    inte = ffmpeg.input(str(x.id)+".mp4")
                    a = inte.audio
                    v = inte.video.filter('scale', w=1920,h=1080,force_original_aspect_ratio='decrease').filter('pad',w=1920,h=1080,x='(ow-iw)/2',y='(oh-ih)/2')

                else:
                    inew = ffmpeg.input(str(x.id)+".mp4")
                    anew = inew.audio
                    vnew = inew.video.filter('scale', w=1920,h=1080,force_original_aspect_ratio='decrease').filter('pad',w=1920,h=1080,x='(ow-iw)/2',y='(oh-ih)/2')
                    inte = ffmpeg.concat(v,a,vnew,anew,v=1,a=1).node
                    v = inte[0]
                    a = inte[1]
            except:
                subject = 'Error'
                html_message = render_to_string('mail/player-gameStart.html', {'gameID':traceback.format_exc()})
                plain_message = strip_tags(html_message)
                send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',["evan.coats9@gmail.com"], html_message = html_message, fail_silently=False)

        ffmpeg.output(v,a,str(gameID)+"comp"+".mp4",f="mp4").run()

        for x in KillVideo.objects.filter(gameID = gameID):
            try:
                os.remove(str(x.id)+".mp4")
                obj = s3.Object('videosassassinlive', str(x.id))
                obj.delete()
            except:
                print(traceback.print_exc())

        s3.meta.client.upload_file(str(gameID)+"comp"+".mp4", 'videosassassinlive', "comps/"+str(gameID)+".mp4")
        os.remove(str(gameID)+"comp"+".mp4")
        return True
    except:
        subject = 'Error'
        html_message = render_to_string('mail/player-gameStart.html', {'gameID':traceback.format_exc()})
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',["evan.coats9@gmail.com"], html_message = html_message, fail_silently=False)

def allowVideoUsePost(request,killedID,gameID):
    try:
        p = Player.objects.get(id = killedID)
        if request.session['user']==p.userID and p.alive and p.deathConfirmed == False and Game.objects.get(id = p.gameID):
            allowed = False
            try:
                if request.POST['compilationUse'] == "yes":
                    allowed = True
            except:
                pass
            kv = KillVideo(killerID = Player.objects.get(targetID = killedID).id, killedID = killedID, gameID = gameID, usable = allowed)
            try:
                kv = KillVideo.objects.get(killerID = Player.objects.get(targetID = killedID).id, killedID = killedID, gameID = gameID)
                if allowed == False:
                    kv.usable = False
            except:
                pass
            kv.save()
            p.deathConfirmed = True
            p.save()
            try:
                subject = 'Your death was confirmed'
                html_message = render_to_string('mail/player-deathConfirmed.html', {'user':User.objects.get(id = p.userID).username, 'kills':p.kills, 'gameID':p.gameID})
                plain_message = strip_tags(html_message)
                send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[User.objects.get(id = p.userID).email], html_message = html_message, fail_silently=False)
            except:
                print(traceback.print_exc())
            doubleConf(Player.objects.get(targetID = killedID).id, killedID, p.gameID)
        return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))
    except:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))


# @background(schedule=5,queue="videoqueue")
# def startComp(gameID):
#     try:
#         if createCompilation(gameID) == True:
#             g = Game.objects.get(id=gameID)
#             g.compilationDone = True
#             g.save()
#     except:
#         pass

# @background(schedule=5)
# def send_email(temp, info):
#     try:
#         if temp == "gamestart":
#             for x in info:
#                 try:
#                     subject = 'Game ' + convertTo64(gameID) +' has started!'
#                     html_message = render_to_string('mail/player-gameStart.html', {'user':x['username'], 'targetID':x['targetID'], 'targetName':x['targetname'], 'gameID':x['gameID']})
#                     plain_message = strip_tags(html_message)
#                     send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[x['email']], html_message = html_message, fail_silently=False)
#                 except:
#                     pass
#         if temp == "gamefinish":
#             for x in info:
#                 try:
#                     subject = 'Game ' + convertTo64(gameID) +' is finished!'
#                     html_message = render_to_string('mail/player-gameFinish.html', {'gameID':x['gameID'],'champID':x['champID'],'champname':x['champName']})
#                     plain_message = strip_tags(html_message)
#                     send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[x['email']], html_message = html_message, fail_silently=False)
#                 except:
#                     pass
#     except:
#         print(traceback.print_exc())
