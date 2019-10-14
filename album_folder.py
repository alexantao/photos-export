#! /usr/bin/env python3

import json
import progressbar
import sys
import time
import datetime
from pathlib import Path
import collections
from argparse import ArgumentParser
from shutil import copyfile

# the files generated before
SYSTEM_FILES = ["albums.json", "folders.json"]


# Source_dir : passed as parameter, where your photos are located
# output_dir : directory under where all albums will be created
def run(source_dir, output_dir, verbose):
    def vprint(x):
        if verbose:
            print(x)

    source_path = Path(source_dir).resolve()
    if not source_path.is_dir():
        print(f'Source directory not found: {source_dir}')
        sys.exit(1)

    output_path = Path(output_dir).resolve()
    if not output_path.is_dir():
        output_path.mkdir(parents=True)

    # Let's print some statistics
    num_of_missing = 0
    num_of_albuns = 0
    num_of_copied = 0
    num_of_moved = 0
    num_of_json = 0

    number_of_json_files = int(
        collections.Counter(p.suffix for p in source_path.glob('[!albums,!folders]*.json'))['.json'])

    bar = progressbar.ProgressBar(maxval=number_of_json_files)

    # load albums and folders data file
    albums_path = Path(source_dir, SYSTEM_FILES[0])
    folders_path = Path(source_dir, SYSTEM_FILES[1])

    try:
        albums_file = open(albums_path)
        albums_dict = json.load(albums_file)

        folders_file = open(folders_path)
        folders_dict = json.load(folders_file)
    except BaseException:
        print(f'Error loading Albums or Folders system file. Please, run those scripts first.')
        sys.exit(1)

    bar.start()
    for json_file in source_path.glob('[!albums,!folders]*.json'):
        num_of_json += 1
        bar.update(num_of_json)

        with json_file.open(mode='r') as data_file:
            json_data = json.load(data_file)
            album_counter = 1

            # This is the physical exported file
            file_exported_name = json_data['uuid']

            # This is the ORIGINAL file name COM PATH
            file_original_path = Path(json_data['path'])

            # the file must be located with the json file, copied from extract_photos.py
            image_source = source_path / file_exported_name
            image_source = image_source.with_suffix(file_original_path.suffix.lower())

            # Some photos do no have any albums included in. So, on those cases,
            # we have just to copy to destination dir.
            # Those photos whose have albums, will be treated later
            # number of albums, to copy to various albums
            number_of_albums = len(json_data['albums'])

            if not image_source.is_file():  # sourcefile missing... does nothing
                vprint(f'Missing File: {image_source}')
                num_of_missing += 1
                continue

            if number_of_albums == 0:
                # destination without album
                image_destination = output_path / file_original_path.name

                if image_destination.is_file():  # if dest file exists, if assumes name with suffix
                    image_destination = (output_path / file_exported_name).with_suffix(file_original_path.suffix)

                # move the file to ROOT of output_dir
                vprint(f'Moving : {image_source} -> {image_destination}')
                image_source.replace(image_destination)
                num_of_moved += 1
            else:  # this is where the photo is included in some album
                # get the list of all albums UUIDs the photo is included
                for album_id in json_data['albums']:
                    album_name = albums_dict[album_id][0]
                    # replace Albums chars "/" with "_". Path object may
                    # interpret it as par of a path
                    album_name = album_name.replace("/", '_')

                    # get the folder path for the album
                    folder_id = albums_dict[album_id][1]
                    if folder_id == "" or folder_id == ".":  # ex.: TopLevelFolders, removed in albums_data.py
                        album_folder = "."  # set to root of output_dir
                    else:
                        album_folder = folders_dict[folder_id][1]

                    album_full_path = output_path / album_folder / album_name

                    if not album_full_path.exists():
                        # Create the album on destination directory
                        album_full_path.mkdir(exist_ok=True, parents=True)
                        num_of_albuns += 1

                    image_destination = album_full_path / file_original_path.name
                    if image_destination.is_file():  # if dest file exists, if assumes exported name
                        image_destination = (album_full_path / file_exported_name).with_suffix(
                            file_original_path.suffix)

                    if album_counter == number_of_albums:
                        vprint(f'Moving : {image_source} -> {image_destination}')
                        # this is the last album, so, move the file
                        image_source.replace(image_destination)
                        num_of_moved += 1
                    else:
                        vprint(f'Copying: {image_source} -> {image_destination}')
                        copyfile(image_source, image_destination)
                        album_counter += 1
                        num_of_copied += 1

    vprint(f'Total files to process: {number_of_json_files}')
    vprint(f'JSON files: {num_of_json}')
    vprint(f'Number of missing files: {num_of_missing}')
    vprint(f'Total albums created: {num_of_albuns}')
    vprint(f'Total files moved: {num_of_moved}')
    vprint(f'Total files duplicated to albuns: {num_of_copied}')


# Usage: ./album_folder <source_dir> <output_dir>
# Copies all files from source_dir to a folder-based map structure in output_dir
# Useful for programs like Plex, who expect a folder-based structure for pictures
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Turn on processing of each file')
    parser.add_argument(
        'source_dir',
        help='Path of where the .json and photos were exported')
    parser.add_argument(
        'output_dir',
        help='Path to where the albums and the files will be created/moved')

    try:
        args = parser.parse_args()
    except Exception:
        sys.exit(2)

    start_time = time.time()
    run(args.source_dir, args.output_dir, args.verbose)
    end_time = time.time()

    print(f'\n-----  Time of processing: {datetime.timedelta(seconds=end_time - start_time)}  -----')
