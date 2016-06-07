# -*- coding: cp1252 -*-

""" -*- coding: utf-8 -*- """
#
# version 2.0.2 - By SlySen
# version 0.2.6 - By CB
#
# pylint...: --max-line-length 120
# vim......: set expandtab
# vim......: set tabstop=4
#
import os, time, urllib, urllib2, re, socket, sys, traceback, xbmcplugin, xbmcaddon, xbmcgui, xbmc, simplejson
if sys.version >= "2.5":
    from hashlib import md5 as _hash
else:
    from md5 import new as _hash


ADDON = xbmcaddon.Addon()
ADDON_CACHE_BASEDIR = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), ".cache")
ADDON_CACHE_TTL = float(ADDON.getSetting('CacheTTL').replace("0", ".5").replace("73", "0"))
ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_IMAGES_BASEPATH = ADDON.getAddonInfo('path')+'/resources/media/images/'
ADDON_FANART = ADDON.getAddonInfo('path')+'/fanart.jpg'
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_AFTER_CR = re.compile(r'\n.*')

TELEQUEBEC_VIDEO_SITE = 'zonevideo.telequebec.tv'
TELEQUEBEC_BASE_URL = 'http://'+TELEQUEBEC_VIDEO_SITE

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
            except StandardError:
                traceback.print_exc()
    except StandardError:
        return None
    return content

# Merci à l'auteur de cette fonction
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
        if entity[:2] == r'\u':
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
    data = re.sub(r'&#?x?(\w+);|\\\\u\d{4}', unescape_callback, data)
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
    check_for_internet_connection()
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
        add_dir_saison(nom_saison, URL, icon, nb_saisons, nom_emission)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    if nb_saisons == 0:
        creer_liste_episodes(URL, 1, FULLNAME, the_fanart)
    return nb_saisons

def creer_liste_supplement(link, nb_saisons):
    """ function docstring """
    main = re.compile('class="extrasEmission"(.+?)</section>', re.DOTALL).findall(link)
    for _ in main:
        nb_saisons = nb_saisons+1
        titre = rechercher_un_element('<h2.*?<span>(.+?)</span>', link)
        sub = rechercher_un_element('class="emissionHeader"(.+?)</div>', link)
        icon = rechercher_un_element('img src="(.+?)"', sub)
        nom_emission = rechercher_un_element('<h1>(.+?)</h1>', sub)
        if icon == "":
            icon = ADDON_IMAGES_BASEPATH+'default-folder.png'
        add_dir_saison(titre, URL, icon, nb_saisons, nom_emission)
    return nb_saisons

def creer_liste_episodes(the_url, saison, nom_complet, the_fanart):
    """ function docstring """
    container_saison = re.split('<div class="listItem floatContainer">', get_cached_content(the_url))
    if len(container_saison) < saison:
        debug_print('Probleme de scraper de saisons')
    else:
        if saison == 1:
            container_saison_str = ''.join(container_saison)
        else:
            container_saison_str = ''.join(container_saison[saison])

        liste = re.split('<div class="item', container_saison_str)
        media_url_list = []
        got_video = False
        for item in liste:
            sub2 = re.compile('<div class="info">(.+?)</div>', re.DOTALL).findall(item)
            if len(sub2) > 0:
                sub2 = sub2[0]
                url_episode = rechercher_un_element('href="(.+?)">', sub2)
                if url_episode is not None and len(url_episode) > 5:
                    got_video = True
                nom_emission = rechercher_un_element('<p(?:.+?)>(.+?)</p>', sub2)
                nom_episode = rechercher_un_element('<a(?:.+?)>(.+?)</a>', sub2)
                icon = rechercher_un_element('src="(.+?)"', item)
                duree = get_duration_in_seconds(rechercher_un_element('"infoSaison"(.+?)</p>', item))
                if duree == -1:
                    duree = ''

                # Pour eviter les duplication (surtout dans Populaires et Recents)
                try:
                    log('media_url_list.index:'+str(media_url_list.index(nom_emission+' : '+nom_episode)))
                except ValueError:
                    media_url_list.append(nom_emission+' : '+nom_episode)
                    if nom_complet == 1:
                        add_link(\
                            nom_emission+' : '+nom_episode,\
                            TELEQUEBEC_BASE_URL+url_episode,\
                            icon,\
                            '',\
                            get_nom_emission_2(),\
                            duree,\
                            the_fanart\
                        )
                    else:
                        add_link(\
                            nom_episode,\
                            TELEQUEBEC_BASE_URL+url_episode,\
                            icon,\
                            '',\
                            get_nom_emission_2(),\
                            duree,\
                            the_fanart\
                        )

        if got_video == False:
            xbmcgui.Dialog().ok(\
                ADDON_NAME,\
                ADDON.getLocalizedString(32120),\
                ADDON.getLocalizedString(32121)\
            )
            exit()

def get_duration_in_seconds(duree_block):
    """ function docstring """
    duree = rechercher_un_element(r'(\d+:\d+:\d+)', duree_block)
    if not duree:
        duree = rechercher_un_element(r'(\d+:\d+)', duree_block)
        if not duree:
            duree = 0
        else:
            d_entries = re.findall(r'(\d+):(\d+)', duree)
            duree = int(d_entries[0][0])*60+int(d_entries[0][1])
    else:
        # hh:mm:ss
        d_entries = re.findall(r'(\d+):(\d+):(\d+)', duree)
        duree = int(d_entries[0][0])*60*60+int(d_entries[0][1])*60+int(d_entries[0][2])

    if duree < 60:
        return -1
    else:
        return duree

def trouver_info_episode(the_url):
    """ function docstring """
    link = get_cached_content(the_url)
    icon = rechercher_un_element('<meta itemprop="image" content="(.+?)">', link)
    description = rechercher_un_element('<meta name="description" content="(.+?)>', link)
    return [icon, description]

def jouer_video(the_url):
    """ function docstring """
    check_for_internet_connection()
    link = get_cached_content(the_url)

    # Obtenir media_uid pure de l'émission
    media_uid = rechercher_un_element('mediaUID: \'Limelight_(.+?)\'', link)
    # <!-- Sly
    if media_uid == "":
        media_id = rechercher_un_element('mediaId: (.+?),', link)
        if media_id != "":
            media_metadata_json = get_cached_content('http://medias.api.telequebec.tv/api/v1/media/%s' % media_id)
            media_metadata_json = simplejson.loads(media_metadata_json)
            media_uid = media_metadata_json['media']['streamInfo']['sourceId']
    # -->

    # Obtenir JSON avec liens RTMP du playlistService
    video_json = simplejson.loads(\
        get_cached_content(\
            'http://production.ps.delve.cust.lldns.net/r/PlaylistService/media/%s/getPlaylistByMediaId' % media_uid\
        )\
    )

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
            # Générer un lien compatible pour librtmp
            # rtmp_url - play_path - swf_url
            url_final = '%s playPath=%s swfUrl=%s swfVfy=true' % (\
                stream_url[:stream_url.find('mp4')],\
                stream_url[stream_url.find('mp4'):],\
                'http://s.delvenetworks.com/deployments/flash-player/flash-player-5.10.1.swf?playerForm=Chromeless'\
            )

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
        for k in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[k].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param

def get_nom_emission_2():
    """ function docstring """
    try:
        nom_emission_2 = urllib.unquote_plus(PARAMS["emission"])
    except StandardError:
        nom_emission_2 = ''
    return nom_emission_2

def add_dir(name, url, mode, iconimage, categorie, nom_complet):
    """ function docstring """
    entry_url = sys.argv[0]+"?url="+urllib.quote_plus(url)+\
        "&mode="+str(mode)+\
        "&name="+urllib.quote_plus(name)+\
        "&categorie="+str(categorie)+\
        "&fullName="+urllib.quote_plus(str(nom_complet))
    is_it_ok = True
    liz = xbmcgui.ListItem(\
        urllib.unquote(name),\
        iconImage=ADDON_IMAGES_BASEPATH+'default-folder.png',\
        thumbnailImage=iconimage\
    )
    liz.setInfo(\
        type="Video",\
        infoLabels={\
            "Title": urllib.unquote(name),\
            "plot":\
                '[B]'+urllib.unquote(name.replace('-- ', ''))+'[/B]'+'[CR]'+\
                ADDON.getAddonInfo('id')+' v.'+ADDON.getAddonInfo('version')\
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
        "&fullName="+urllib.quote_plus(str(FULLNAME))
    is_it_ok = True
    liz = xbmcgui.ListItem(name, iconImage=ADDON_IMAGES_BASEPATH+'default-folder.png', thumbnailImage=iconimage)

    if ADDON.getSetting('EmissionNameInPlotEnabled') == 'true':
        plot = '[B]'+urllib.unquote(name.lstrip())+'[/B]'+'[CR]'+plot.lstrip()
    else:
        plot = plot.lstrip()

    liz.setInfo(\
        type="Video",\
        infoLabels={\
            "Title":urllib.unquote(name),\
            "Plot":plot\
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
        "&fullName="+urllib.quote_plus(str(FULLNAME))
    is_it_ok = True
    liz = xbmcgui.ListItem(name, iconImage=ADDON_IMAGES_BASEPATH+'default-folder.png', thumbnailImage=iconimage)

    if ADDON.getSetting('EmissionNameInPlotEnabled') == 'true':
        plot = '[B]'+emission+'[/B][CR]'+name
    else:
        plot = name

    liz.setInfo(\
        type="Video",\
        infoLabels={\
            "Title": urllib.unquote(name),\
            "Plot":plot\
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
        if ADDON.getSetting('EmissionNameInPlotEnabled') == 'true':
            plot = '[B]'+plot.lstrip()+'[/B]'+'[CR]'+name.lstrip()
        else:
            plot = name.lstrip()
    else:
        plot = name.lstrip()

    liz = xbmcgui.ListItem(\
        remove_any_html_tags(name), iconImage=ADDON_IMAGES_BASEPATH+"default-video.png", thumbnailImage=iconimage\
    )
    liz.setInfo(\
        type="Video",\
        infoLabels={\
            "Title":remove_any_html_tags(name),\
            "Plot":remove_any_html_tags(plot, False),\
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

def is_network_available():
    """ function docstring """
    try:
        # see if we can resolve the host name -- tells us if there is a DNS listening
        host = socket.gethostbyname(TELEQUEBEC_VIDEO_SITE)
        # connect to the host -- tells us if the host is actually reachable
        srvcon = socket.create_connection((host, 80), 2)
        srvcon.close()
        return True
    except socket.error:
        return False

def check_for_internet_connection():
    """ function docstring """
    if ADDON.getSetting('NetworkDetection') == 'false':
        return

    if is_network_available() == False:
        xbmcgui.Dialog().ok(\
            ADDON_NAME,\
            ADDON.getLocalizedString(32112),\
            ADDON.getLocalizedString(32113)\
        )
        exit()
    return

def remove_any_html_tags(text, crlf=True):
    """ function docstring """
    text = RE_HTML_TAGS.sub('', text)
    text = text.lstrip()
    if crlf == True:
        text = RE_AFTER_CR.sub('', text)
    return text

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
URL = None
NAME = None
EMISSION = None
MODE = None
URL_INFO = None
CATEGORIE = None
SEASON = 0
FULLNAME = 0
FANART = None

try:
    URL = urllib.unquote_plus(PARAMS["url"])
    log("PARAMS['url']:"+URL)
except StandardError:
    pass
try:
    NAME = urllib.unquote_plus(PARAMS["name"])
    log("PARAMS['name']:"+NAME)
except StandardError:
    pass
try:
    EMISSION = urllib.unquote_plus(PARAMS["emission"])
    log("PARAMS['emission']:"+EMISSION)
except StandardError:
    pass
try:
    MODE = int(PARAMS["mode"])
    log("PARAMS['mode']:"+str(MODE))
except StandardError:
    pass
try:
    CATEGORIE = int(PARAMS["categorie"])
    log("PARAMS['categorie']:"+str(CATEGORIE))
except StandardError:
    pass
try:
    URL_INFO = int(PARAMS["Info"])
    log("PARAMS['Info']:"+str(URL_INFO))
except StandardError:
    pass
try:
    SEASON = int(PARAMS["season"])
    log("PARAMS['season']:"+str(SEASON))
except StandardError:
    pass
try:
    FULLNAME = int(PARAMS["fullName"])
    log("PARAMS['fullName']:"+str(FULLNAME))
except StandardError:
    pass
try:
    FANART = urllib.unquote_plus(PARAMS["fanart"])
    log("PARAMS['fanart']:"+FANART)
except StandardError:
    FANART = ''

if MODE == None or URL == None or len(URL) < 1:
    creer_menu_categories()
    set_content('episodes')

elif MODE == 1:
    creer_liste_filtree(CATEGORIE, URL)
    set_content('episodes')

elif MODE == 2:
    creer_liste_videos(URL, FANART)
    set_content('episodes')

elif MODE == 3:
    creer_liste_episodes(URL, SEASON, FULLNAME, FANART)
    set_content('episodes')

elif MODE == 4:
    jouer_video(URL)

elif MODE == 6:
    creer_dossiers(URL)
    #set_content('tvshows')
    set_content('episodes')

set_sorting_methods(MODE)
xbmcplugin.endOfDirectory(int(sys.argv[1]))

if MODE is not 4 and ADDON.getSetting('DeleteTempFiFilesEnabled') == 'true':
    PATH = xbmc.translatePath('special://temp')
    FILENAMES = next(os.walk(PATH))[2]
    for i in FILENAMES:
        if ".fi" in i:
            os.remove(os.path.join(PATH, i))

