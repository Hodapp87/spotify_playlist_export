spotify_playlist_export
=======================

This is a Python script to export Spotify playlists to [XSPF](http://www.xspf.org/)
(XML Shareable Playlist Format) files.  As it relies on
[pyspotify](https://github.com/mopidy/pyspotify) which in turn relies on
[libspotify](https://developer.spotify.com/technologies/libspotify/), this
requires that you have a Spotify Premium account, and an API key in the form of
a ''spotify_appkey.key'' file in the working directory.

This will export one playlist per XSPF file. It optionally preserves the
playlist folders by placing the XSFP files in a directory structure that
mirrors the playlist folders.

Known issues:
- This has been tested only with Python 3.x so far.
- The script will occasionally fail because the Spotify API is returning None
instead of a proper object.
- This does not yet support the proxy login options that pyspotify exposes.
- These XSPF playlists are probably a bit useless on their own because they do
not include in any kind of external links or a MusicBrainz acoustic fingerprint.
- This does not do a great job sanitizing filenames, if you're prone to putting
weird characters in your playlist names.

You know the drill. Please do not use this tool for piracy.
