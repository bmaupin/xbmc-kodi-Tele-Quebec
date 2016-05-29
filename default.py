# -*- coding: utf-8 -*-


##### -*- coding: cp1252 -*-
import os,time, urllib,urllib2,re,xbmcplugin,xbmcaddon,xbmcgui,xbmc,simplejson
import pprint
if sys.version >= "2.5":
    from hashlib import md5 as _hash
else:
    from md5 import new as _hash

# version 2.7
#By SlySen
# version 2.6
#By CB

addon = xbmcaddon.Addon()
addon_cache_basedir = os.path.join(xbmc.translatePath(addon.getAddonInfo('path')),".cache")
addon_cache_ttl = float(addon.getSetting('CacheTTL').replace("0",".5").replace("25","0"))
addon_icon = addon.getAddonInfo('icon')
addon_name = addon.getAddonInfo('name')
addon_images_base_path = addon.getAddonInfo('path')+'/resources/media/images/'
addon_fanart = addon.getAddonInfo('path')+'/fanart.jpg'

TELEQUEBEC_BASE_URL = 'http://zonevideo.telequebec.tv'

if not os.path.exists(addon_cache_basedir):
    os.makedirs(addon_cache_basedir)

def is_cached_content_expired(lastUpdate):
    #log('LASTUPDATE: '+str(lastUpdate))
    #log('TTL: '+str(addon_cache_ttl))
    expired = time.time() >= (lastUpdate + (addon_cache_ttl * 60**2))
    return expired

def get_cached_filename(path):
    filename = "%s" % _hash(repr(path)).hexdigest()
    return os.path.join(addon_cache_basedir, filename)

def get_cached_content(path):
    content=None
    try:
        filename = get_cached_filename(path)
        if os.path.exists(filename) and not is_cached_content_expired(os.path.getmtime(filename)):
            content=open(filename).read()
        else:
            content=getURLtxt(path)
            try:
                file(filename,"w").write(content) # cache the requested web content
            except:
                print_exc()
    except:
        return None
    return content

#Merci � l'auteur de cette fonction
def unescape_callback(matches):
        html_entities = {
                'quot':'\"', 'amp':'&', 'apos':'\'', 'lt':'<', 'gt':'>', 'nbsp':' ', 'copy':'�', 'reg':'�',
                'Agrave':'�', 'Aacute':'�', 'Acirc':'�', 'Atilde':'�', 'Auml':'�', 'Aring':'�', 'AElig':'�',
                'Ccedil':'�', 'Egrave':'�', 'Eacute':'�', 'Ecirc':'�', 'Euml':'�', 'Igrave':'�', 'Iacute':'�',
                'Icirc':'�', 'Iuml':'�', 'ETH':'�', 'Ntilde':'�', 'Ograve':'�', 'Oacute':'�', 'Ocirc':'�',
                'Otilde':'�', 'Ouml':'�', 'Oslash':'�', 'Ugrave':'�', 'Uacute':'�', 'Ucirc':'�', 'Uuml':'�',
                'Yacute':'�', 'agrave':'�', 'aacute':'�', 'acirc':'�', 'atilde':'�', 'auml':'�', 'aring':'�',
                'aelig':'�', 'ccedil':'�', 'egrave':'�', 'eacute':'�', 'ecirc':'�', 'euml':'�', 'igrave':'�',
                'iacute':'�', 'icirc':'�', 'iuml':'�', 'eth':'�', 'ntilde':'�', 'ograve':'�', 'oacute':'�',
                'ocirc':'�', 'otilde':'�', 'ouml':'�', 'oslash':'�', 'ugrave':'�', 'uacute':'�', 'ucirc':'�',
                'uuml':'�', 'yacute':'�', 'yuml':'�'
        }

        entity = matches.group(0)
        val = matches.group(1)

        try:
                if entity[:2] == '\u':
                        return entity.decode('unicode-escape')
                elif entity[:3] == '&#x':
                        return unichr(int(val, 16))
                elif entity[:2] == '&#':
                        return unichr(int(val))
                else:
                        return html_entities[val].decode('utf-8')

        except (ValueError, KeyError):
                pass

def HTMLUnescape(data):
        data = data.decode('utf-8')
        data = re.sub('&#?x?(\w+);|\\\\u\d{4}', unescape_callback, data)
        data = data.encode('utf-8')

        return data

def rechercherUnElement(argument, rechercherDans):
        reponse = re.compile(argument, re.DOTALL).search(rechercherDans)
        if(reponse):
                return reponse.group(1)
        else:
                return ""

def getURLtxt(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0')
        req.add_header('Accept-Charset', 'utf-8')
        response = urllib2.urlopen(req)
        link=response.read()
        link = HTMLUnescape(link)
        response.close()
        return link

def getBlock(url):
        link = get_cached_content(url)
        main = rechercherUnElement('content azsContainer index(.+?)<footer>',link)
        return main

def getCategories(url):
        main = getBlock(url)
        match=re.compile('<option value="(.+?)">(.+?)</option>',re.DOTALL).findall(main)
        return match

def getListeEmissions(url):
        main = getBlock(url)
        match=re.compile('<li data-genre="(.+?)"><a href="(.+?)">(.+?)</a></li>',re.DOTALL).findall(main)
        return match

def comparerCategorie(categorieVoulue, listeCategorie):
        if categorieVoulue == '0' : return 1
        match=re.split(';',listeCategorie)
        for catListee in match:
                if catListee==categorieVoulue:
                        return 1
        return 0

def trouverInfosEmission(url):
       link = get_cached_content(url)
       main = rechercherUnElement('<article class="emission">(.+?)</article>',link)
       sub= rechercherUnElement('class="emissionHeader"(.+?)</div>',main)
       icon = rechercherUnElement('img src="(.+?)"',sub)
       sub2= rechercherUnElement('class="emissionInfo"(.+?)</div>',main)
       resume = rechercherUnElement('<p>(.+?)</p>',sub2)
       return [icon,resume]


def creerMenuCategories():
        urlAZ = TELEQUEBEC_BASE_URL+'/a-z/'
        nomCategories = getCategories(urlAZ)
        for numberCat,nomCat in nomCategories:
                if numberCat<>'All':
                        addDir(nomCat,urlAZ,1,'',numberCat,0)
        addDir('A %C3%A0 Z - Tous les genres',urlAZ,1,addon_images_base_path+'default-folder.png','0',0)
        addDir('Documentaires',urlAZ,1,addon_images_base_path+'default-folder.png','1',0)
        addDir('Dossiers',TELEQUEBEC_BASE_URL+'/dossiers/',6,addon_images_base_path+'default-folder.png','0',1)
        addDir('Famille',urlAZ,1,addon_images_base_path+'default-folder.png','2',0)
        addDir('Films',urlAZ,1,addon_images_base_path+'default-folder.png','3',0)
        addDir('Jeunesse - Pour les petits',urlAZ,1,addon_images_base_path+'default-folder.png','6',0)
        addDir('Jeunesse - Pour les plus grands',urlAZ,1,addon_images_base_path+'default-folder.png','4',0)
        addDir('Jeunesse - Pour les vraiment grands',urlAZ,1,addon_images_base_path+'default-folder.png','5',0)
        addDir('Magazines',urlAZ,1,addon_images_base_path+'default-folder.png','7',0)
        addDir('S%C3%A9ries de fiction',urlAZ,1,addon_images_base_path+'default-folder.png','9',0)
        addDir('Vari%C3%A9t%C3%A9s',urlAZ,1,addon_images_base_path+'default-folder.png','10',0)
        addDir('-- Populaires',TELEQUEBEC_BASE_URL+'/populaires/',2,addon_images_base_path+'default-folder.png','0',1)
        addDir('-- R%C3%A9cents',TELEQUEBEC_BASE_URL,2,addon_images_base_path+'default-folder.png','0',1)

def creerListeFiltree(categorieVoulue,url):
        liste = getListeEmissions(url)
        for categ,lien,titre in liste:
                if comparerCategorie(str(categorieVoulue),categ)==1:
                    # <!-- Sly
                    if lien != '/a-z/289/le-skwat': 
                        elementsInformations = trouverInfosEmission(TELEQUEBEC_BASE_URL+lien) 
                        addEmission(titre,TELEQUEBEC_BASE_URL+lien,elementsInformations[0],elementsInformations[1],'') 
                    # -->

def creerDossiers(url):
        link = get_cached_content(url)
        container = re.split('<div class="listItem floatContainer">',link)
        liste = re.split('<div class="item"',container[1])
        for item in liste:
                sub2 = re.compile('<div class="info">(.+?)</div>',re.DOTALL).findall(item)
                if len(sub2)>0:
                        sub2=sub2[0]
                        urlDossier = rechercherUnElement('href="(.+?)">',sub2)
                        nomDossier = rechercherUnElement('<a(?:.+?)>(.+?)</a>',sub2)
                        icon = rechercherUnElement('src="(.+?)"',item)
                        fanart = icon
                        #infos = trouverInfosEpisode(TELEQUEBEC_BASE_URL+urlEpisode)
                        addEmission(nomDossier,TELEQUEBEC_BASE_URL+urlDossier,icon,'',fanart)

def creerListeVideos(url,fanart):
       if fanart == '':
            fanart=addon_fanart
       link = get_cached_content(url)
       nbSaisons=creerListeSaisons(link,fanart)
       nbSaisons=creerListeSupplement(link,nbSaisons)

def creerListeSaisons(link,fanart):
       nbSaisons = 0
       sub = rechercherUnElement('<ul class="menu(.+?)</ul>',link)
       match = re.compile('<li(.+?)</li>',re.DOTALL).findall(sub)
       for saisonTxt in match:
               nbSaisons = nbSaisons+1
               nomSaison = rechercherUnElement('<a.*?><span class="icon"></span>(.+?)</a>',saisonTxt)
               sub= rechercherUnElement('class="emissionHeader"(.+?)</div>',link)
               icon = rechercherUnElement('img src="(.+?)"',sub) 
               nomEmission = rechercherUnElement('<h1>(.+?)</h1>',sub) 
               log(nomEmission)
               if icon == "":
                       icon=addon_images_base_path+'default-folder.png'
               addDirSaison(nomSaison,url,icon,nbSaisons,nomEmission)
               xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE) 
       if nbSaisons==0:
               creerListeEpisodes(url,1,fullName,fanart)
       return nbSaisons


def creerListeSupplement(link,nbSaisons):
        main = re.compile('class="extrasEmission"(.+?)</section>',re.DOTALL).findall(link)
        for extra in main:
                nbSaisons = nbSaisons+1
                titre = rechercherUnElement('<h2.*?<span>(.+?)</span>',link)
                sub= rechercherUnElement('class="emissionHeader"(.+?)</div>',link)
                icon = rechercherUnElement('img src="(.+?)"',sub) 
                nomEmission = rechercherUnElement('<h1>(.+?)</h1>',sub) 
                if icon == "":
                        icon=addon_images_base_path+'default-folder.png'
                addDirSaison(titre,url,icon,nbSaisons,nomEmission)
        return nbSaisons

def creerListeEpisodes(url,saison,nomComplet,fanart):
        link = get_cached_content(url)

        #emissionHeader = rechercherUnElement('<div class="emissionHeader">',link) 
        #log("EEE:"+emissionHeader)
        #sub = rechercherUnElement('<ul class="menu(.+?)</ul>',link)
        #nomEmission2 = rechercherUnElement('<h1>(.+?)</h1>',sub)
        try: 
            nomEmission2 = urllib.unquote_plus(params["emission"])
        except:
            nomEmission2 = ''

        containerSaison = re.split('<div class="listItem floatContainer">',link) 

        if len(containerSaison)<saison:
                debugPrint('Probleme de scraper de saisons')
        else:
                 if saison==1:
                        containerSaisonStr = ''.join(containerSaison)
                 else:
                        containerSaisonStr = ''.join(containerSaison[saison])

                 liste = re.split('<div class="item',containerSaisonStr)
                 medialUrlList=[]
                 for item in liste:
                        sub2 = re.compile('<div class="info">(.+?)</div>',re.DOTALL).findall(item)
                        if len(sub2)>0:
                                sub2=sub2[0]
                                urlEpisode = rechercherUnElement('href="(.+?)">',sub2)
                                nomEmission = rechercherUnElement('<p(?:.+?)>(.+?)</p>',sub2)
                                nomEpisode = rechercherUnElement('<a(?:.+?)>(.+?)</a>',sub2)
                                icon = rechercherUnElement('src="(.+?)"',item)
                                dureeBlock = rechercherUnElement('"infoSaison"(.+?)</p>',item)
                                duree = rechercherUnElement('(\d+:\d+:\d+)',dureeBlock)
                                # C'est laid. FIXME
                                if not duree:
                                    duree = rechercherUnElement('(\d+:\d+)',dureeBlock)
                                    if not duree:
                                        duree=""
                                    else:
                                        d_entries=re.findall(r'(\d+):(\d+)', duree)
                                        duree=int(d_entries[0][0])*60+int(d_entries[0][1])
                                else:
                                    # hh:mm:ss
                                    d_entries=re.findall(r'(\d+):(\d+):(\d+)', duree)
                                    duree=int(d_entries[0][0])*60*60+int(d_entries[0][1])*60+int(d_entries[0][2])
                                # / C'est laid. FIXME

                                #infos = trouverInfosEpisode(TELEQUEBEC_BASE_URL+urlEpisode)

                                mediaUrl=TELEQUEBEC_BASE_URL+urlEpisode
                                if (nomComplet==1):
                                    addLink(nomEmission+' : '+nomEpisode,mediaUrl,icon,'',nomEmission2,duree,fanart)
                                else:
                                    addLink(nomEpisode,mediaUrl,icon,'',nomEmission2,duree,fanart)

def trouverInfosEpisode(url):
       link = get_cached_content(url)
       icon = rechercherUnElement('<meta itemprop="image" content="(.+?)">',link)
       description = rechercherUnElement('<meta name="description" content="(.+?)>',link)

       return [icon,description]

def JOUERVIDEO(url,name,url_info):
        link = get_cached_content(url)

        #Obtenir mediaUID pure de l'�mission
        mediaUID = rechercherUnElement('mediaUID: \'Limelight_(.+?)\'',link)
        # <!-- Sly 
        if mediaUID == "":
            mediaID = rechercherUnElement('mediaId: (.+?),',link)
            if mediaID != "":
                mediaMetadata = get_cached_content('http://medias.api.telequebec.tv/api/v1/media/%s' % mediaID)
                mediaMetadataJSON = simplejson.loads(mediaMetadata)
                mediaUID = mediaMetadataJSON['media']['streamInfo']['sourceId'] 
        # -->

        #Obtenir JSON avec liens RTMP du playlistService
        link = get_cached_content('http://production.ps.delve.cust.lldns.net/r/PlaylistService/media/%s/getPlaylistByMediaId' % mediaUID)
        videoJSON = simplejson.loads(link)

        #Preparer list de videos � jouer
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        #Analyser chaque stream disponible pour trouver la meilleure qualit�
        for playlistItem in videoJSON['playlistItems']:
            highestBitRate = 0
            streamURL = None
            for stream in playlistItem['streams']:
                if stream['videoBitRate'] > highestBitRate:
                    highestBitRate = stream['videoBitRate']
                    streamURL = stream['url']

            if streamURL:
                #S�parer le lien en RTMP et PLAYPATH
                rtmpUrl = streamURL[:streamURL.find('mp4')]
                playPath = streamURL[streamURL.find('mp4'):]

                #G�n�rer un lien compatible pour librtmp
                swfUrl = 'http://s.delvenetworks.com/deployments/flash-player/flash-player-5.10.1.swf?playerForm=Chromeless'
                url = '%s playPath=%s swfUrl=%s swfVfy=true' % (rtmpUrl, playPath, swfUrl)

                log('Starting playback of :' + urllib.quote_plus(url))
                item = xbmcgui.ListItem(videoJSON['title'],iconImage=videoJSON['imageUrl'],thumbnailImage=videoJSON['imageUrl'])
                playlist.add(url, item)
            else:
                xbmc.executebuiltin('Notification(%s,Incapable d''obtenir lien du video,5000,%s' % (addon_name, addon_icon))

        if playlist.size() > 0:
            xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(playlist)


def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]

        return param

def addDir(name,url,mode,iconimage,categorie,nomComplet):
        name=name
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+\
            "&mode="+str(mode)+\
            "&name="+urllib.quote_plus(name)+\
            "&categorie="+str(categorie)+\
            "&fullName="+urllib.quote_plus(str(nomComplet))
        ok=True
        liz=xbmcgui.ListItem(urllib.unquote(name), iconImage=addon_images_base_path+'default-folder.png', thumbnailImage=iconimage)
        liz.setInfo(\
            type="Video",\
            infoLabels={\
                "Title": urllib.unquote(name),\
                "plot":\
                    addon.getAddonInfo('id')+' v.'+addon.getAddonInfo('version')+'[CR]'+\
                    '[B]'+urllib.unquote(name.replace('-- ',''))+'[/B]'\
            }\
        )
        if addon.getSetting('FanartEnabled') == 'true':
            if addon.getSetting('FanartEmissionsEnabled') == 'true':
                if iconimage==addon_images_base_path+'default-folder.png': # Main dicrectory listing
                    liz.setProperty('fanart_image', addon_fanart)
                else:
                    liz.setProperty('fanart_image', iconimage)
            else:
                liz.setProperty('fanart_image', addon_fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addEmission(name,url,iconimage,plot,fanart):
        prochainMode = 2
        if fanart=='':
            fanart=iconimage
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+\
            "&mode="+str(prochainMode)+\
            "&name="+urllib.quote_plus(name)+\
            "&fanart="+urllib.quote_plus(str(fanart))+\
            "&fullName="+urllib.quote_plus(str(fullName))
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=addon_images_base_path+'default-folder.png', thumbnailImage=iconimage)
        liz.setInfo(\
            type="Video",\
            infoLabels={"Title":urllib.unquote(name),"Plot":'[B]'+urllib.unquote(name.lstrip())+'[/B]'+'[CR]'+plot.lstrip()}\
        )
        if addon.getSetting('FanartEnabled') == 'true':
            if addon.getSetting('FanartEmissionsEnabled') == 'true':
                liz.setProperty('fanart_image', fanart)
            else:
                liz.setProperty('fanart_image', addon_fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addDirSaison(name,url,iconimage,saison,emission):
        prochainMode = 3
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+\
            "&mode="+str(prochainMode)+\
            "&name="+urllib.quote_plus(name)+\
            "&emission="+urllib.quote_plus(emission)+\
            "&fanart="+urllib.quote_plus(str(iconimage))+\
            "&season="+str(saison)+\
            "&fullName="+urllib.quote_plus(str(fullName))
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=addon_images_base_path+'default-folder.png', thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": urllib.unquote(name),"Plot":'[B]'+emission+'[/B][CR]'+name} )
        if addon.getSetting('FanartEnabled') == 'true':
            if addon.getSetting('FanartEmissionsEnabled') == 'true':
                liz.setProperty('fanart_image', iconimage)
            else:
                liz.setProperty('fanart_image', addon_fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addLink(name,url,iconimage,url_info,plot,duree,fanart):
        ok=True
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+\
            "&mode=4"+\
            "&name="+urllib.quote_plus(name)+\
            "&Info="+urllib.quote_plus(url_info)

        if plot != '':
            plot = '[B]'+plot.lstrip()+'[/B]'+'[CR]'+name.lstrip()
        else:
            plot = name.lstrip()

        liz=xbmcgui.ListItem(name, iconImage=addon_images_base_path+"default-video.png", thumbnailImage=iconimage)
        liz.setInfo(\
            type="Video",\
            infoLabels={\
                "Title": name,\
                "Plot":plot,\
                "Duration":duree\
            }
        )

        if fanart==addon_fanart:
            fanart=iconimage 
        if addon.getSetting('FanartEnabled') == 'true':
            if addon.getSetting('FanartEmissionsEnabled') == 'true':
                if fanart != '':
                    liz.setProperty('fanart_image', fanart)
                else:
                    liz.setProperty('fanart_image', iconimage)
            else:
                liz.setProperty('fanart_image', addon_fanart)

        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        return ok

def setContent(content):
        xbmcplugin.setContent(int(sys.argv[1]), content)
        return

def setSortingMethods(mode):
        # c.f.: https://github.com/notspiff/kodi-cmake/blob/master/xbmc/SortFileItem.h
        log('MODE:'+str(mode))
        if mode != None and mode != 1:
            if addon.getSetting('SortMethodTvShow') == '1':
                xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE) 
                xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        return

def debugPrint(texte):
        u=sys.argv[0]+"?url="+urllib.quote_plus(TELEQUEBEC_BASE_URL)+\
            "&mode="+str(0)+\
            "&name="+urllib.quote_plus(texte)
        ok=True
        liz=xbmcgui.ListItem(texte, iconImage=addon_images_base_path+'default-folder.png', thumbnailImage='')
        liz.setInfo( type="Video", infoLabels={ "Title": texte } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def log(msg):
        xbmc.log('[%s - DEBUG]: %s' % (addon_name,msg))

# ---

log('--- init -----------------')
params=get_params()
url=None
name=None
emission=None
mode=None
url_info=None
categorie=None
season=0
fullName=0

try:
        url=urllib.unquote_plus(params["url"])
        log("params['url']:"+url)
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
        log("params['name']:"+name)
except:
        pass
try:
        emission=urllib.unquote_plus(params["emission"])
        log("params['emission']:"+emission)
except:
        pass
try:
        mode=int(params["mode"])
        log("params['mode']:"+str(mode))
except:
        pass
try:
        categorie=int(params["categorie"])
        log("params['categorie']:"+str(categorie))
except:
        pass
try:
        url_info=int(params["Info"])
        log("params['Info']:"+str(url_info))
except:
        pass
try:
        season=int(params["season"])
        log("params['season']:"+str(season))
except:
        pass
try:
        fullName=int(params["fullName"])
        log("params['fullName']:"+str(fullName))
except:
        pass
try:
        fanart=urllib.unquote_plus(params["fanart"])
        log("params['fanart']:"+fanart)
except:
        fanart=''
        pass

if mode==None or url==None or len(url)<1:
        creerMenuCategories()
        setContent('episodes')

elif mode==1:
        creerListeFiltree(categorie,url)
        setContent('episodes')

elif mode==2:
        creerListeVideos(url,fanart)
        setContent('episodes')

elif mode==3:
        creerListeEpisodes(url,season,fullName,fanart)
        setContent('episodes')

elif mode==4:
        JOUERVIDEO(url,name,url_info)

elif mode==6:
        creerDossiers(url)
        #setContent('tvshows')
        setContent('episodes')

setSortingMethods(mode)
xbmcplugin.endOfDirectory(int(sys.argv[1]))
