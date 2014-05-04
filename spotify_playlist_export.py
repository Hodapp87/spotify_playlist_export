#!/usr/bin/env python

# spotify_playlist_export:
# This script uses pyspotify to log in to a user's Spotify account and export
# all of the playlists to XSPF (XML Shareable Playlist Format) files.
# (c) 2014 Chris Hodapp

import spotify

import threading
import xml.etree.ElementTree as ET
import sys, os, time

import argparse

def processContainer(plCont):
    """
    This walks a Spotify playlist container, and converts all the playlists
    found insode to XSPF (XML Shareable Playlist Format).
    It generates (name, folder, tree), tuples, where 'name' is the playlist's
    name, 'folder' is a tuple expressing the path to the playlist, and 'tree'
    is an ElementTree giving the XSPF.
    
    Arguments:
    plCont -- spotify.playlist_container object from which to start
    """
    folder = []
    count = len(plCont)
    for idx,pl in enumerate(plCont):
        print("Loading %d of %d..." % (idx + 1, count))
        if type(pl) is spotify.playlist.Playlist:
            _ = pl.load()
            tree = ET.ElementTree(generateXspf(pl))
            yield (pl.name, folder, tree)
        elif type(pl) is spotify.playlist_container.PlaylistFolder:
            if pl.type == spotify.playlist_container.PlaylistType.START_FOLDER:
                folder.append(pl.name)
                #recurseContainer(pl, level + 1, folder)
            elif pl.type == spotify.playlist_container.PlaylistType.END_FOLDER:
                folder.pop()
            else:
                print("Unknown playlist type %s, %s" % (type(pl), pl))
        elif type(pl) is int:
            print("Don't know what to do with int %d..." % (pl,))
        elif type(pl) is str:
            print("Don't know what to do with str %s..." % (pl,))
        else:
            print("Unknown playlist type %s, %s" % (type(pl), pl))

def generateXspf(playlist):
    """Turn a spotify.playlist.Playlist into an XSPF playlist.  This returns
    root node as an xml.etree.ElementTree.Element."""
    root = ET.Element('playlist')
    # getSubFn, given a root element, returns a function which adds a subelement
    # of that root element with the given name, and optional text. It returns
    # that subelement, but it can be ignored.
    def getSubFn(elem):
        def _getSub(name, text = None):
            sub = ET.SubElement(elem, name)
            if text is not None:
                sub.text = str(text)
            return sub
        return _getSub
    rootSub = getSubFn(root)
    root.set('version', '1')
    root.set('xmlns', 'http://xspf.org/ns/0/')

    # Get some playlist metadata:
    rootSub('title', playlist.name)
    # This might also sensibly be canonical_name.
    rootSub('creator', playlist.owner.display_name)
    if (playlist.description):
        rootSub('annotation', playlist.description)
    # TODO: This field could be turned into a real URL at open.spotify.com
    # rather than a Spotify short URI.
    rootSub('location', playlist.link.uri)
    # No 'date' field, annoyingly.

    # Get information for each track:
    trackList = rootSub('trackList')
    for track in playlist.tracks:
        trackSub = getSubFn(ET.SubElement(trackList, 'track'))
        trackSub('location', track.link.uri)
        # Is anything proper for 'identifier'? MusicBrainz?
        trackSub('title', track.name)
        trackSub('creator', ",".join([a.name for a in track.artists]))
        album = '%s - %s (%s)' % (track.album.artist.name, track.album.name, track.album.year)
        trackSub('album', album)
        # What do I do with other album metadata? Album art?
        trackSub('trackNum', track.index)
        trackSub('duration', track.duration)
        # TODO: Find a less clunky way to mark that a track is starred.
        if (track.starred):
            trackSub('annotation', 'Starred')
    return root

# Perhaps HTML escaping is a better option.
def sanitizeFilename(name):
    replace = (';', '/', '\\')
    for ch in replace:
        name = name.replace(ch, '-')
    return name

def main(argv):
    description = "Log in to a Spotify account given a username and password (you must have a Spotify Premium account, and spotify_appkey.key in the working directory), read all playlists, and export them to XSPF (XML Shareable Playlist Format) files, optionally preserving the structure of playlist folders."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-u", "--username", help="Spotify username")
    parser.add_argument("-p", "--password", help="Spotify password")
    parser.add_argument("-f", "--flat", action="store_true",
                        help="Do not make directories for playlist folders.")
    parser.add_argument("-d", "--dest", default='.',
                        help="Destination directory to store playlists (default is current).")
    args = parser.parse_args()

    # Log in to Spotify and get a session
    # Code from: http://pyspotify.mopidy.com/en/latest/quickstart/
    logged_in_event = threading.Event()
    def logged_in_listener(session, error_type):
        logged_in_event.set()
    session = spotify.Session()
    loop = spotify.EventLoop(session)
    loop.start()
    session.on(spotify.SessionEvent.LOGGED_IN, logged_in_listener)
    session.login(args.username, args.password)
    session.connection_state
    logged_in_event.wait()
    
    # TODO: Is there some better way to do this?
    print("Waiting to log in %s..." % (session.user,))
    while (session.connection_state != spotify.ConnectionState.LOGGED_IN):
        time.sleep(0.01)
    print("Logged in.")

    # Get the playlist container:
    _ = session.playlist_container.load()

    # Prepare directory for output:
    try:
        os.makedirs(args.dest)
    except FileExistsError:
        pass

    # Finally, start converting everything:
    for name, relPath, xspf in processContainer(session.playlist_container):
        # Create the necessary path for 'relPath'.
        path = args.dest
        if relPath and not args.flat:
            folders = [sanitizeFilename(f) for f in relPath]
            path = os.sep.join([path] + folders)
            try:
                os.makedirs(path)
            except FileExistsError:
                pass
        # Sanitize the name a bit:
        name = sanitizeFilename(name)
        filename = os.sep.join([path, name + '.xspf'])
        # Finally, write it out.
        xspf.write(filename, 'UTF-8', True)

main(sys.argv)
