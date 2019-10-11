#! /usr/bin/env python3

import exiftool
import json
import sys
import progressbar
from pathlib import Path


# Copies metadata from the sidecar JSON into the file EXIF
# Copies: GPS data, rating, and albums and keywords (as tags)

def run(root):
    with exiftool.ExifTool() as et:
        def gps_opts(latitude, longitude):
            lat_ref = 'N' if latitude > 0 else 'S'
            long_ref = 'E' if longitude > 0 else 'W'
            flags = [
                'GPSLatitude=%f' %
                abs(latitude),
                'GPSLatitudeRef=%s' %
                lat_ref,
                'GPSLongitude=%f' %
                abs(longitude),
                'GPSLongitudeRef=%s' %
                long_ref]
            foo = map(lambda x: ('-EXIF:%s' % x), flags)
            return list(foo)

        def title_opts(title):
            return ["-XMP:Caption=%s" % title]

        def tag_opts(tags):
            return list(map(lambda x: "-XMP:TagsList='%s'" % x, tags))

        def rating_opts(rating):
            rating_map = {0: 0, 1: 1, 2: 25, 3: 50, 4: 74, 5: 99}
            return [
                '-XMP:Rating=%i' %
                rating,
                '-XMP:RatingPercent=%i' %
                rating_map[rating]]

        def exec_opts(opts, img):
            try:
                et.execute_json(*(opts + [img]))
                raise RuntimeError
            except ValueError:
                pass

        source_path = Path(root).resolve()

        images_files = [e for e in source_path.iterdir() if not e.suffix == '.json']
        number_of_image_files = len(images_files)

        bar = progressbar.ProgressBar(maxval=number_of_image_files)
        bar.start()
        num_processed = 0

        for image_file in images_files:  # get first NOT JSON file (image, supose)

            json_file = image_file.with_suffix('.json')
            with json_file.open(mode='r') as data_file:
                data = json.load(data_file)
                opts = []
                if data['latitude'] is not None and data[
                    'longitude'] is not None:
                    opts += gps_opts(float(data['latitude']),
                                     float(data['longitude']))
                opts += tag_opts(data['keywords'])
                opts += tag_opts(data['albums'])
                opts += rating_opts(int(data['rating'] or 0))
                opts += title_opts(data['title'])

                if len(opts) != 0:
                    exec_opts(opts +
                              ['-overwrite_original_in_place', '-P'], str(image_file))

                num_processed += 1
                bar.update(num_processed)


# Usage: ./set_exif.py <output_dir>
if __name__ == '__main__':
    run(sys.argv[1])
