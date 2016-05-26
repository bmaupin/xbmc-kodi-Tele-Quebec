
import os
import sys

import xbmc
import xbmcgui
import xbmcvfs
from xbmcaddon import Addon

addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo('name')
addon_cache_basedir = os.path.join(xbmc.translatePath(addon.getAddonInfo('path')),".cache")

if sys.argv[1].lower() == "full":
    print "["+addon_name+"TELEQUEBEC] deleting full cache"
    for root, dirs, files in os.walk(addon_cache_basedir):
        for file in files:
            xbmcvfs.delete( os.path.join( root, file ) )
    xbmcgui.Dialog().ok(addon.getAddonInfo( 'name' ), "Clean Cache...", "Success")

