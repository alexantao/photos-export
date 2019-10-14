#! /usr/bin/env python3

import json
from pathlib import Path

import progressbar
import os
import sys
import sqlite3
import glob
from argparse import ArgumentParser

# Digikam format
# edited_id original_id 2

# Determine the ID of an image in the Digikam database


def image_id(db, name):
    c = db.cursor()
    c.execute('SELECT * FROM Images WHERE name=?', name)
    rows = c.fetchall()
    if len(rows) != 1:
        raise RuntimeError('Too many matches for "%s": %i' % (name, len(rows)))
    return rows[0]['id']


def run(digikam_dir, photos_dir):
    db_path = Path(digikam_dir).resolve() / 'digikam4.db'
    photos_path = Path(photos_dir).resolve()

    try:
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    except Exception as dberror:
        print(f'Error connecting to DIGIKAM DB: {dberror}')
        sys.exit(1)

    images_files = [e for e in photos_path.iterdir() if not e.suffix == '.json']
    num_processed = 0

    bar = progressbar.ProgressBar(maxval=len(images_files))
    bar.start()

    for photo_file in images_files:

        json_file = photo_file.with_suffix('.json')

        with json_file.open(mode='r') as data_file:
            data = json.load(data_file)
            derived_from = data['derived_from']
            if derived_from is not None:
                edited_id = image_id(db, photo_file.name)

                possible_originals = photo_file.glob(photos_path / (derived_from + ".*"))

                possible_originals_json = [
                    item for item in possible_originals if item.suffix != '.json']

                if len(possible_originals_json) != 1:
                    raise RuntimeError(
                        'Ambiguous match: %s', possible_originals_json)
                original_id = image_id(db, possible_originals_json[0])
                c = db.cursor()
                c.execute(
                    'INSERT INTO ImageRelations VALUES (?, ?, ?)', [
                        edited_id, original_id, 2])
    db.commit()
    db.close()


# Usage: ./group_version.py <digikam_dir> <photos_dir>
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'digikam_library',
        help='Path where your DIGIKAM Library is located')
    parser.add_argument(
        'photos_dir',
        help='Path to where the photos were exported.')

    try:
        args = parser.parse_args()
    except Exception as error:
        print("Argument error: ", error)
        sys.exit(2)

    run(args.digikam_library, args.photos_dir)
