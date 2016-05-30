# -*- coding: cp1252 -*-


""" -*- coding: utf-8 -*- """
import os, time, urllib, urllib2, re, sys, traceback, xbmcplugin, xbmcaddon, xbmcgui, xbmc, simplejson
if sys.version >= "2.5":
    from hashlib import md5 as _hash
else:
    from md5 import new as _hash

# version 2.0.2 - By SlySen
# version 0.2.6 - By CB

ADDON = xbmcaddon.Addon()
ADDON_CACHE_BASEDIR = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), ".cache")
ADDON_CACHE_TTL = float(ADDON.getSetting('CacheTTL').replace("0", ".5").replace("25", "0"))
ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_IMAGES_BASEPATH = ADDON.getAddonInfo('path')+'/resources/media/images/'
ADDON_FANART = ADDON.getAddonInfo('path')+'/fanart.jpg'

TELEQUEBEC_BASE_URL = 'http://zonevideo.telequebec.tv'

if not os.path.exists(ADDON_CACHE_BASEDIR):
    os.makedirs(ADDON_CACHE_BASEDIR)

def is_cached_content_expired(last_update):
    """ function docstring """
    expired = time.time() >= (last_update + (ADDON_CACHE_TTL * 60**2))
    return expired

def get_cached_filename(path):
    """ function docstring """
    filename = "%s" % _hash(repr(path)).hexdigest()
    return os.path.join(ADDON_CACHE_BASEDIR, filename)

def get_cached_content(path):
    """ function docstring """
    content = None
    try:
        filename = get_cached_filename(path)
        if os.path.exists(filename) and not is_cached_content_expired(os.path.getmtime(filename)):
            content = open(filename).read()
        else:
            content = get_url_txt(path)
            try:
                file(filename, "w").write(content) # cache the requested web content
            except Exception:
                traceback.print_exc()
    except Exception:
        return None
    return content

#Merci à l'auteur de cette fonction
def unescape_callback(matches):
    """ function docstring """
    html_entities =\
    {
        'quot':'\"', 'amp':'&', 'apos':'\'', 'lt':'<',
        'gt':'>', 'nbsp':' ', 'copy':'©', 'reg':'®',
        'Agrave':'À', 'Aacute':'Á', 'Acirc':'Â',
        'Atilde':'Ã', 'Auml':'Ä', 'Aring':'Å',
        'AElig':'Æ', 'Ccedil':'Ç', 'Egrave':'È',
        'Eacute':'É', 'Ecirc':'Ê', 'Euml':'Ë',
        'Igrave':'Ì', 'Iacute':'Í', 'Icirc':'Î',
        'Iuml':'Ï', 'ETH':'Ð', 'Ntilde':'Ñ',
        'Ograve':'Ò', 'Oacute':'Ó', 'Ocirc':'Ô',
        'Otilde':'Õ', 'Ouml':'Ö', 'Oslash':'Ø',
        'Ugrave':'Ù', 'Uacute':'Ú', 'Ucirc':'Û',
        'Uuml':'Ü', 'Yacute':'Ý', 'agrave':'à',
        'aacute':'á', 'acirc':'â', 'atilde':'ã',
        'auml':'ä', 'aring':'å', 'aelig':'æ',
        'ccedil':'ç', 'egrave':'è', 'eacute':'é',
        'ecirc':'ê', 'euml':'ë', 'igrave':'ì',
        'iacute':'í', 'icirc':'î', 'iuml':'ï',
        'eth':'ð', 'ntilde':'ñ', 'ograve':'ò',
        'oacute':'ó', 'ocirc':'ô', 'otilde':'õ',
        'ouml':'ö', 'oslash':'ø', 'ugrave':'ù',
        'uacute':'ú', 'ucirc':'û', 'uuml':'ü',
        'yacute':'ý', 'yuml':'ÿ'
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

def html_unescape(data):
    """ function docstring """
    data = data.decode('utf-8')
    data = re.sub('&#?x?(\w+);|\\\\u\d{4}', unescape_callback, data)
    data = data.encode('utf-8')
    return data

def rechercher_un_element(argument, rechercher_dans):
    """ function docstring """
    reponse = re.compile(argument, re.DOTALL).search(rechercher_dans)
    if reponse:
        return reponse.group(1)
    else:
        return ""

def get_url_txt(the_url):
    """ function docstring """
    req = urllib2.Request(the_url)
    req.add_header(\
        'User-Agent',\
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0'\
    )
    req.add_header('Accept-Charset', 'utf-8')
    response = urllib2.urlopen(req)
    link = response.read()
    link = html_unescape(link)
    response.close()
    return link

def get_block(the_url):
    """ function docstring """
    link = get_cached_content(the_url)
    main = rechercher_un_element('content azsContainer index(.+?)<footer>', link)
    return main

def get_categories(the_url):
    """ function docstring """
    main = get_block(the_url)
    match = re.compile('<option value="(.+?)">(.+?)</option>', re.DOTALL).findall(main)
    return match

def get_liste_emissions(the_url):
    """ function docstring """
    main = get_block(the_url)
    match = re.compile('<li data-genre="(.+?)"><a href="(.+?)">(.+?)</a></li>', re.DOTALL).findall(main)
    return match

def comparer_categorie(categorie_voulue, liste_categorie):
    """ function docstring """
    if categorie_voulue == '0':
        return 1
    match = re.split(';', liste_categorie)
    for cat_listee in match:
        if cat_listee == categorie_voulue:
            return 1
    return 0

def trouver_infos_emission(the_url):
    """ function docstring """
    link = get_cached_content(the_url)
    main = rechercher_un_element('<article class="emission">(.+?)</article>', link)
    sub = rechercher_un_element('class="emissionHeader"(.+?)</div>', main)
    icon = rechercher_un_element('img src="(.+?)"', sub)
    sub2 = rechercher_un_element('class="emissionInfo"(.+?)</div>', main)
    resume = rechercher_un_element('<p>(.+?)</p>', sub2)
    return [icon, resume]


def creer_menu_categories():
    """ function docstring """
    url_az = TELEQUEBEC_BASE_URL+'/a-z/'
    nom_categories = get_categories(url_az)
    for number_cat, nom_cat in nom_categories:
        if number_cat is not 'All':
            add_dir(nom_cat, url_az, 1, '', number_cat, 0)
    add_dir('A %C3%A0 Z - Tous les genres', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '0', 0)
    add_dir('Documentaires', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '1', 0)
    add_dir('Dossiers', TELEQUEBEC_BASE_URL+'/dossiers/', 6, ADDON_IMAGES_BASEPATH+'default-folder.png', '0', 1)
    add_dir('Famille', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '2', 0)
    add_dir('Films', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '3', 0)
    add_dir('Jeunesse - Pour les petits', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '6', 0)
    add_dir('Jeunesse - Pour les plus grands', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '4', 0)
    add_dir('Jeunesse - Pour les vraiment grands', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '5', 0)
    add_dir('Magazines', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '7', 0)
    add_dir('S%C3%A9ries de fiction', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '9', 0)
    add_dir('Vari%C3%A9t%C3%A9s', url_az, 1, ADDON_IMAGES_BASEPATH+'default-folder.png', '10', 0)
    add_dir('-- Populaires', TELEQUEBEC_BASE_URL+'/populaires/', 2, ADDON_IMAGES_BASEPATH+'default-folder.png', '0', 1)
    add_dir('-- R%C3%A9cents', TELEQUEBEC_BASE_URL, 2, ADDON_IMAGES_BASEPATH+'default-folder.png', '0', 1)

def creer_liste_filtree(categorie_voulue, the_url):
    """ function docstring """
    liste = get_liste_emissions(the_url)
    for categ, lien, titre in liste:
        if comparer_categorie(str(categorie_voulue), categ) == 1:
            # <!-- Sly
            if lien != '/a-z/289/le-skwat': # 404 en mai 2016
                elements_infos = trouver_infos_emission(TELEQUEBEC_BASE_URL+lien)
                add_emission(titre, TELEQUEBEC_BASE_URL+lien, elements_infos[0], elements_infos[1], '')
            # -->

def creer_dossiers(the_url):
    """ function docstring """
    link = get_cached_content(the_url)
    container = re.split('<div class="listItem floatContainer">', link)
    liste = re.split('<div class="item"', container[1])
    for item in liste:
        sub2 = re.compile('<div class="info">(.+?)</div>', re.DOTALL).findall(item)
        if len(sub2) > 0:
            sub2 = sub2[0]
            url_dossier = rechercher_un_element('href="(.+?)">', sub2)
            nom_dossier = rechercher_un_element('<a(?:.+?)>(.+?)</a>', sub2)
            icon = rechercher_un_element('src="(.+?)"', item)
            add_emission(nom_dossier, TELEQUEBEC_BASE_URL+url_dossier, icon, '', icon)

def creer_liste_videos(the_url, the_fanart):
    """ function docstring """
    if the_fanart == '':
        the_fanart = ADDON_FANART
    link = get_cached_content(the_url)
    nb_saisons = creer_liste_saisons(link, the_fanart)
    nb_saisons = creer_liste_supplement(link, nb_saisons)

def creer_liste_saisons(link, the_fanart):
    """ function docstring """
    nb_saisons = 0
    sub = rechercher_un_element('<ul class="menu(.+?)</ul>', link)
    match = re.compile('<li(.+?)</li>', re.DOTALL).findall(sub)
    for saison_txt in match:
        nb_saisons = nb_saisons+1
        nom_saison = rechercher_un_element('<a.*?><span class="icon"></span>(.+?)</a>', saison_txt)
        sub = rechercher_un_element('class="emissionHeader"(.+?)</div>', link)
        icon = rechercher_un_element('img src="(.+?)"', sub)
        nom_emission = rechercher_un_element('<h1>(.+?)</h1>', sub)
        log(nom_emission)
        if icon == "":
            icon = ADDON_IMAGES_BASEPATH+'default-folder.png'
        add_dir_saison(nom_saison, url, icon, nb_saisons, nom_emission)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    if nb_saisons == 0:
        creer_liste_episodes(url, 1, fullName, the_fanart)
    return nb_saisons

def creer_liste_supplement(link, nb_saisons):
    """ function docstring """
    main = re.compile('class="extrasEmission"(.+?)</section>', re.DOTALL).findall(link)
    for extra in main:
        nb_saisons = nb_saisons+1
        titre = rechercher_un_element('<h2.*?<span>(.+?)</span>', link)
        sub = rechercher_un_element('class="emissionHeader"(.+?)</div>', link)
        icon = rechercher_un_element('img src="(.+?)"', sub)
        nom_emission = rechercher_un_element('<h1>(.+?)</h1>', sub)
        if icon == "":
            icon = ADDON_IMAGES_BASEPATH+'default-folder.png'
        add_dir_saison(titre, url, icon, nb_saisons, nom_emission)
    return nb_saisons

def creer_liste_episodes(the_url, saison, nom_complet, the_fanart):
    """ function docstring """
    link = get_cached_content(the_url)

    #emissionHeader = rechercher_un_element('<div class="emissionHeader">',link)
    #log("EEE:"+emissionHeader)
    #sub = rechercher_un_element('<ul class="menu(.+?)</ul>',link)
    #nom_emission = rechercher_un_element('<h1>(.+?)</h1>',sub)
    try:
        nom_emission_2 = urllib.unquote_plus(PARAMS["emission"])
    except Exception:
        nom_emission_2 = ''

    container_saison = re.split('<div class="listItem floatContainer">', link)

    if len(container_saison) < saison:
        debug_print('Probleme de scraper de saisons')
    else:
        if saison == 1:
            container_saison_str = ''.join(container_saison)
        else:
            container_saison_str = ''.join(container_saison[saison])

        liste = re.split('<div class="item', container_saison_str)
        media_url_list = []
        for item in liste:
            sub2 = re.compile('<div class="info">(.+?)</div>', re.DOTALL).findall(item)
            if len(sub2) > 0:
                sub2 = sub2[0]
                url_episode = rechercher_un_element('href="(.+?)">', sub2)
                nom_emission = rechercher_un_element('<p(?:.+?)>(.+?)</p>', sub2)
                nom_episode = rechercher_un_element('<a(?:.+?)>(.+?)</a>', sub2)
                icon = rechercher_un_element('src="(.+?)"', item)
                duree_block = rechercher_un_element('"infoSaison"(.+?)</p>', item)
                duree = rechercher_un_element('(\d+:\d+:\d+)', duree_block)
                # C'est laid. FIXME
                if not duree:
                    duree = rechercher_un_element('(\d+:\d+)', duree_block)
                    if not duree:
                        duree = ""
                    else:
                        d_entries = re.findall(r'(\d+):(\d+)', duree)
                        duree = int(d_entries[0][0])*60+int(d_entries[0][1])
                else:
                    # hh:mm:ss
                    d_entries = re.findall(r'(\d+):(\d+):(\d+)', duree)
                    duree = int(d_entries[0][0])*60*60+int(d_entries[0][1])*60+int(d_entries[0][2])
                # / C'est laid. FIXME

                #infos = trouver_info_episode(TELEQUEBEC_BASE_URL+url_episode)

                # Pour eviter les duplication (surtout dans Populaires et Recents)
                the_full_name = nom_emission+' : '+nom_episode
                try:
                    #media_url_liste_index = media_url_list.index(the_full_name)
                    log('media_url_list.index:'+str(media_url_list.index(the_full_name)))
                except ValueError:
                    media_url_list.append(the_full_name)
                    media_url = TELEQUEBEC_BASE_URL+url_episode
                    if nom_complet == 1:
                        add_link(the_full_name, media_url, icon, '', nom_emission_2, duree, the_fanart)
                    else:
                        add_link(nom_episode, media_url, icon, '', nom_emission_2, duree, the_fanart)

def trouver_info_episode(the_url):
    """ function docstring """
    link = get_cached_content(the_url)
    icon = rechercher_un_element('<meta itemprop="image" content="(.+?)">', link)
    description = rechercher_un_element('<meta name="description" content="(.+?)>', link)
    return [icon, description]

def jouer_video(the_url, url_info):
    """ function docstring """
    link = get_cached_content(the_url)

    # Obtenir media_uid pure de l'émission
    media_uid = rechercher_un_element('mediaUID: \'Limelight_(.+?)\'', link)
    # <!-- Sly
    if media_uid == "":
        media_id = rechercher_un_element('mediaId: (.+?),', link)
        if media_id != "":
            media_metadata = get_cached_content('http://medias.api.telequebec.tv/api/v1/media/%s' % media_id)
            media_metadata_json = simplejson.loads(media_metadata)
            media_uid = media_metadata_json['media']['streamInfo']['sourceId']
    # -->

    # Obtenir JSON avec liens RTMP du playlistService
    link = get_cached_content(\
        'http://production.ps.delve.cust.lldns.net/r/PlaylistService/media/%s/getPlaylistByMediaId' % media_uid\
    )
    video_json = simplejson.loads(link)

    # Preparer list de videos à jouer
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()

    # Analyser chaque stream disponible pour trouver la meilleure qualité
    for play_list_item in video_json['playlistItems']:
        highest_bit_rate = 0
        stream_url = None
        for stream in play_list_item['streams']:
            if stream['videoBitRate'] > highest_bit_rate:
                highest_bit_rate = stream['videoBitRate']
                stream_url = stream['url']

        if stream_url:
            # Séparer le lien en RTMP et PLAYPATH
            rtmp_url = stream_url[:stream_url.find('mp4')]
            play_path = stream_url[stream_url.find('mp4'):]

            # Générer un lien compatible pour librtmp
            swf_url = 'http://s.delvenetworks.com/deployments/flash-player/flash-player-5.10.1.swf?playerForm=Chromeless'
            url_final = '%s playPath=%s swfUrl=%s swfVfy=true' % (rtmp_url, play_path, swf_url)

            log('Starting playback of :' + urllib.quote_plus(url_final))
            item = xbmcgui.ListItem(\
                video_json['title'],\
                iconImage=video_json['imageUrl'],\
                thumbnailImage=video_json['imageUrl']\
            )
            playlist.add(url_final, item)
        else:
            xbmc.executebuiltin('Notification(%s,Incapable d''obtenir lien du video,5000,%s' % (ADDON_NAME, ADDON_ICON))

    if playlist.size() > 0:
        xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(playlist)

def get_params():
    """ function docstring """
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if params[len(params)-1] == '/':
            params = params[0:len(params)-2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param

def add_dir(name, url, mode, iconimage, categorie, nom_complet):
    """ function docstring """
    name = name
    entry_url = sys.argv[0]+"?url="+urllib.quote_plus(url)+\
        "&mode="+str(mode)+\
        "&name="+urllib.quote_plus(name)+\
        "&categorie="+str(categorie)+\
        "&fullName="+urllib.quote_plus(str(nom_complet))
    is_it_ok = True
    liz = xbmcgui.ListItem(urllib.unquote(name), iconImage=ADDON_IMAGES_BASEPATH+'default-folder.png', thumbnailImage=iconimage)
    liz.setInfo(\
        type="Video",\
        infoLabels={\
            "Title": urllib.unquote(name),\
            "plot":\
                ADDON.getAddonInfo('id')+' v.'+ADDON.getAddonInfo('version')+'[CR]'+\
                '[B]'+urllib.unquote(name.replace('-- ', ''))+'[/B]'\
        }\
    )
    if ADDON.getSetting('FanartEnabled') == 'true':
        if ADDON.getSetting('FanartEmissionsEnabled') == 'true':
            if iconimage == ADDON_IMAGES_BASEPATH+'default-folder.png': # Main dicrectory listing
                liz.setProperty('fanart_image', ADDON_FANART)
            else:
                liz.setProperty('fanart_image', iconimage)
        else:
            liz.setProperty('fanart_image', ADDON_FANART)
    is_it_ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=entry_url, listitem=liz, isFolder=True)
    return is_it_ok

def add_emission(name, the_url, iconimage, plot, the_fanart):
    """ function docstring """
    prochain_mode = 2
    if the_fanart == '':
        the_fanart = iconimage
    entry_url = sys.argv[0]+"?url="+urllib.quote_plus(the_url)+\
        "&mode="+str(prochain_mode)+\
        "&name="+urllib.quote_plus(name)+\
        "&fanart="+urllib.quote_plus(str(the_fanart))+\
        "&fullName="+urllib.quote_plus(str(fullName))
    is_it_ok = True
    liz = xbmcgui.ListItem(name, iconImage=ADDON_IMAGES_BASEPATH+'default-folder.png', thumbnailImage=iconimage)
    liz.setInfo(\
        type="Video",\
        infoLabels={\
            "Title":urllib.unquote(name),\
            "Plot":'[B]'+urllib.unquote(name.lstrip())+'[/B]'+'[CR]'+plot.lstrip()\
        }\
    )
    if ADDON.getSetting('FanartEnabled') == 'true':
        if ADDON.getSetting('FanartEmissionsEnabled') == 'true':
            liz.setProperty('fanart_image', the_fanart)
        else:
            liz.setProperty('fanart_image', ADDON_FANART)
    is_it_ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=entry_url, listitem=liz, isFolder=True)
    return is_it_ok

def add_dir_saison(name, the_url, iconimage, saison, emission):
    """ function docstring """
    prochain_mode = 3
    entry_url = sys.argv[0]+"?url="+urllib.quote_plus(the_url)+\
        "&mode="+str(prochain_mode)+\
        "&name="+urllib.quote_plus(name)+\
        "&emission="+urllib.quote_plus(emission)+\
        "&fanart="+urllib.quote_plus(str(iconimage))+\
        "&season="+str(saison)+\
        "&fullName="+urllib.quote_plus(str(fullName))
    is_it_ok = True
    liz = xbmcgui.ListItem(name, iconImage=ADDON_IMAGES_BASEPATH+'default-folder.png', thumbnailImage=iconimage)
    liz.setInfo(\
        type="Video",\
        infoLabels={\
            "Title": urllib.unquote(name),\
            "Plot":'[B]'+emission+'[/B][CR]'+name\
        }\
    )
    if ADDON.getSetting('FanartEnabled') == 'true':
        if ADDON.getSetting('FanartEmissionsEnabled') == 'true':
            liz.setProperty('fanart_image', iconimage)
        else:
            liz.setProperty('fanart_image', ADDON_FANART)
    is_it_ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=entry_url, listitem=liz, isFolder=True)
    return is_it_ok

def add_link(name, the_url, iconimage, url_info, plot, duree, the_fanart):
    """ function docstring """
    is_it_ok = True
    entry_url = sys.argv[0]+"?url="+urllib.quote_plus(the_url)+\
        "&mode=4"+\
        "&name="+urllib.quote_plus(name)+\
        "&Info="+urllib.quote_plus(url_info)

    if plot != '':
        plot = '[B]'+plot.lstrip()+'[/B]'+'[CR]'+name.lstrip()
    else:
        plot = name.lstrip()

    liz = xbmcgui.ListItem(name, iconImage=ADDON_IMAGES_BASEPATH+"default-video.png", thumbnailImage=iconimage)
    liz.setInfo(\
        type="Video",\
        infoLabels={\
            "Title": name,\
            "Plot":plot,\
            "Duration":duree\
        }\
    )

    if the_fanart == ADDON_FANART:
        the_fanart = iconimage
    if ADDON.getSetting('FanartEnabled') == 'true':
        if ADDON.getSetting('FanartEmissionsEnabled') == 'true':
            if the_fanart != '':
                liz.setProperty('fanart_image', the_fanart)
            else:
                liz.setProperty('fanart_image', iconimage)
        else:
            liz.setProperty('fanart_image', ADDON_FANART)

    is_it_ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=entry_url, listitem=liz, isFolder=False)
    return is_it_ok

def set_content(content):
    """ function docstring """
    xbmcplugin.setContent(int(sys.argv[1]), content)
    return

def set_sorting_methods(mode):
    """ function docstring """
    # c.f.: https://github.com/notspiff/kodi-cmake/blob/master/xbmc/SortFileItem.h
    log('MODE:'+str(mode))
    if mode != None and mode != 1:
        if ADDON.getSetting('SortMethodTvShow') == '1':
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
    return

def debug_print(texte):
    """ function docstring """
    entry_url = sys.argv[0]+"?url="+urllib.quote_plus(TELEQUEBEC_BASE_URL)+\
        "&mode="+str(0)+\
        "&name="+urllib.quote_plus(texte)
    is_it_ok = True
    liz = xbmcgui.ListItem(texte, iconImage=ADDON_IMAGES_BASEPATH+'default-folder.png', thumbnailImage='')
    liz.setInfo(type="Video", infoLabels={"Title": texte})
    is_it_ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=entry_url, listitem=liz, isFolder=True)
    return is_it_ok

def log(msg):
    """ function docstring """
    if ADDON.getSetting('DebugMode') == 'true':
        xbmc.log('[%s - DEBUG]: %s' % (ADDON_NAME, msg))

# ---
log('--- init -----------------')
# ---

PARAMS = get_params()
url = None
name = None
emission = None
mode = None
url_info = None
categorie = None
season = 0
fullName = 0

try:
    url = urllib.unquote_plus(PARAMS["url"])
    log("PARAMS['url']:"+url)
except Exception:
    pass
try:
    name = urllib.unquote_plus(PARAMS["name"])
    log("PARAMS['name']:"+name)
except Exception:
    pass
try:
    emission = urllib.unquote_plus(PARAMS["emission"])
    log("PARAMS['emission']:"+emission)
except Exception:
    pass
try:
    mode = int(PARAMS["mode"])
    log("PARAMS['mode']:"+str(mode))
except Exception:
    pass
try:
    categorie = int(PARAMS["categorie"])
    log("PARAMS['categorie']:"+str(categorie))
except Exception:
    pass
try:
    url_info = int(PARAMS["Info"])
    log("PARAMS['Info']:"+str(url_info))
except Exception:
    pass
try:
    season = int(PARAMS["season"])
    log("PARAMS['season']:"+str(season))
except Exception:
    pass
try:
    fullName = int(PARAMS["fullName"])
    log("PARAMS['fullName']:"+str(fullName))
except Exception:
    pass
try:
    fanart = urllib.unquote_plus(PARAMS["fanart"])
    log("PARAMS['fanart']:"+fanart)
except Exception:
    fanart = ''
    pass

if mode == None or url == None or len(url) < 1:
    creer_menu_categories()
    set_content('episodes')

elif mode == 1:
    creer_liste_filtree(categorie, url)
    set_content('episodes')

elif mode == 2:
    creer_liste_videos(url, fanart)
    set_content('episodes')

elif mode == 3:
    creer_liste_episodes(url, season, fullName, fanart)
    set_content('episodes')

elif mode == 4:
    jouer_video(url, url_info)

elif mode == 6:
    creer_dossiers(url)
    #set_content('tvshows')
    set_content('episodes')

set_sorting_methods(mode)
xbmcplugin.endOfDirectory(int(sys.argv[1]))
