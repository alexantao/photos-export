#! /usr/bin/env python3

#     This script reads ans stores all Albums sensitive  information
#  from Photos.app, used to store a Album on the right Folder it should go
#  Generates a JSON file of the information to be used later
#
import json
from pathlib import Path
import sys
import sqlite3

# SOME CONSTANTS USED
ALBUM_TABLE = "RKAlbum"
FOLDER_TABLE = "RKFolder"

UUID_FIELD = "uuid"
NAME_FIELD = "name"
TRASH_FIELD = "isInTrash"
MODELID_FIELD = "modelId"

FOLDER_FIELD = "folderUuid"
ROOT_FOLDER = "TopLevelAlbums"


# Ignore all albuns inside these folders. consider only user created
IGNORED_FOLDERS_ALBUNS = [
    'LibraryFolder',
    'TopLevelAlbums',
    'MediaTypesSmartAlbums',
    'TopLevelSlideshows',
    'TrashFolder']
JSON_FILENAME = "albums.json"


def run(lib_dir, output_dir):
    main_db_path = Path(lib_dir).resolve() / 'database' / 'photos.db'

    main_db = sqlite3.connect(main_db_path)
    main_db.row_factory = sqlite3.Row

    # Get all albums information
    album_table = main_db.cursor()
    album_table.execute('SELECT * FROM ' + ALBUM_TABLE + ' WHERE ' + TRASH_FIELD + '=0')

    # will store uuid -> [name, folder]
    db_album_dict = {}

    # let's test each album
    for album in iter(album_table.fetchone, None):

        album_name = album[NAME_FIELD]
        album_uuid = album[UUID_FIELD]
        album_folder = album[FOLDER_FIELD]
        album_folder = album_folder.replace(ROOT_FOLDER, "")

        # add to dictionary
        if album_name is not None:
            db_album_dict[album_uuid] = [album_name, str(Path(album_folder))]

    # print_dict(db_album_dict)

    #  mount and store final JSON on file
    json_dump = json.dumps(db_album_dict)
    json_file = Path(output_dir) / JSON_FILENAME
    json_file.open(mode='w')
    json_file.write_text(json_dump)


# Usage: ./folder_structure.py <photo_library> <output_dir>
if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
