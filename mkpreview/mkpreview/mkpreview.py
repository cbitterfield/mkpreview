#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Library Imports
#

# Required
import os
import sys
import shutil
import argparse
import time
from datetime import datetime

# Add this module's location to syspath
sys.path.insert(0, os.getcwd())

# Program Specific library imports
import ffmpeg
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image
from wand.display import display as Display
import hashlib
from database import Database
from __init__ import __version__
from __init__ import __email__
from __init__ import __author__
from definitions import COLORS
from definitions import VIDEO_EXTENSIONS
from definitions import TABLE
import random
import string



__prog_name__ = os.path.basename(__file__)
__short_name__ = os.path.splitext(__prog_name__)[0]
__console_size_ = shutil.get_terminal_size((80, 20))[0]
__timestamp__ = time.time()
__run_datetime__ = datetime.fromtimestamp(__timestamp__)  # Today's Date

# Global Variables for Testing
# Test and Debugging Variables
# These are applied to all functions and classes
# These settings override the command line if set to TRUE
# Set to NONE to have no effect
# If set to True or False, it will override the CLI

DEBUG = False
DRYRUN = None
VERBOSE = False
QUIET = None

# Global Variables # set defaults here.
if DEBUG:
    tmp = globals().copy()
    [print(k, '  :  ', v, ' type:', type(v)) for k, v in tmp.items() if
     not k.startswith('_') and k != 'tmp' and k != 'In' and k != 'Out' and not hasattr(v, '__call__')]

FFMPEG = ""
FFPROBE = ""


## Functions
def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.hexdigits
    letters = letters.lower()
    numbers = string.digits
    return ''.join(random.choice(letters + numbers) for i in range(stringLength))


def md5Checksum(filename):
    with open(filename, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()



def video_info(**kwargs):
    """ Retrieve Video Information and return a dictionary with all variables


        Settings:
        ---------
        REQUIRED = filename


        Parameters:
        ----------
        filename = filename

        Raises:
        ------
        Exception
            If filename does not exist or is not a file

        Returns:
        --------
            SUCCESS, file_info(dict)

        Example:
        --------
        SUCCESS, info = video_info(filename=file)

    """
    global DEBUG
    global FFPROBE

    REQUIRED = list(['filename'])
    MAX_PARAMS = 1
    SUCCESS = True

    filename=kwargs.get('filename',None)
    local_info = dict()


    # Check for requirement parameters
    if DEBUG:
        print(REQUIRED, len(REQUIRED))
    if DEBUG:
        print(kwargs, len(kwargs))
    if len(REQUIRED) <= len(kwargs) <= MAX_PARAMS:
        for required in REQUIRED:
            if required not in kwargs:
                SUCCESS = False
                raise Exception("The parameter {0} is required".format(required))

    else:
        SUCCESS = False
        raise Exception('parameters required {0} parameters received {1}'.format(len(REQUIRED), len(kwargs)))

    if DEBUG:
        print('Success Flag, {0}, arguments {1}'.format(SUCCESS, kwargs))
    # Code to execute here
    # Test Filename
    if not os.path.isfile(filename): SUCCESS = False
    if SUCCESS:
        # Get Video Information
        probe_args = {'pretty': None,
                      'select_streams': 'v:0',
                      'show_entries': "stream=bit_rate,height,width,codec_long_name,display_aspect_ratio,avg_frame_rate,bit_rate,max_bit_rate,nb_frames : stream_tags= : stream_disposition= :format=duration,size :format_tags= "

                      }

        info = ffmpeg.probe(filename, cmd=FFPROBE, **probe_args)
        if DEBUG: print(info)
        local_info['codec_long_name'] = info['streams'][0]['codec_long_name']
        local_info['video_width'] = info['streams'][0]['width']
        local_info['video_height'] = info['streams'][0]['height']
        local_info['video_aspect'] = info['streams'][0]['display_aspect_ratio'] if "display_aspect_ratio" in \
                                                                                   info['streams'][0] else None
        v1, v2 = info['streams'][0]['avg_frame_rate'].split('/')
        local_info['video_frame_rate'] = str(int(int(v1) / int(v2)))
        local_info['video_bit_rate'] = info['streams'][0]['bit_rate']
        local_info['video_frames'] = info['streams'][0]['nb_frames']
        local_info['video_duration'] = info['format']['duration']
        local_info['video_size'] = info['format']['size']

        return SUCCESS, local_info

    else:

        return SUCCESS, {'status', 'fail'}

    # End Program Functions and Classes

# Setup Function for the application


def setup(configuration):
    global DEBUG
    global VERBOSE
    global DRYRUN
    global QUIET
    global myDB
    global COLORS
    global TABLE
    global VIDEOS
    global DRYRUN
    global HWACCEL

    # Set Globals if needed
    DEBUG = configuration.debug if configuration.debug else DEBUG
    VERBOSE = configuration.verbose if configuration.verbose else VERBOSE
    DRYRUN = configuration.dryrun if configuration.dryrun else DRYRUN
    QUIET = configuration.quiet if configuration.quiet else QUIET

    # Do some quick testing on colors.

    if configuration.colors:
        print('Available Colors are:')
        print('{}'.format("=" * 40))
        for color in COLORS:
            print(color)
        sys.exit(0)

    if not configuration.in_file:
        print('Missing Video File')
        print('Configuration: {}'.format(configuration))
        sys.exit(1)

    if not configuration.dbfile:
        configuration.dbfile = os.getcwd() + "/default.db"

    # Assign DB Name
    myDB = Database(configuration.dbfile)

    if not os.path.isfile(configuration.dbfile) or configuration.create_newdb:
        if DEBUG: print('Database {} created'.format(configuration.dbfile))
        # Create New database file
        myDB.create(overwrite=False)
        myDB.connect()
        myDB.createTable(table='preview',overwrite=False,fields=TABLE['preview'],unique=(['filename','md5']))
        myDB.close()
    else:
        # Make sure we have a table
        myDB.connect()
        if not myDB.isTable(table='preview'):
            myDB.createTable(table='preview',overwrite=False,fields=TABLE['preview'],unique=(['filename','md5']))
            myDB.sqlExecute("""PRAGMA journal_mode=WAL;""")
        myDB.close()

    VIDEOS = list()
    if os.path.isfile(configuration.in_file):
        VIDEOS.append(configuration.in_file)

    elif os.path.isdir(configuration.in_file):
        with os.scandir(configuration.in_file) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.split('.', 1)[1] in VIDEO_EXTENSIONS:
                    full_name = os.path.join(configuration.in_file, entry.name)
                    VIDEOS.append(full_name)

        VIDEOS.sort()
    else:
        print('No Valid Input presented {}'.format(configuration.in_file))

    if DEBUG: print(VIDEOS)

    # Find and define FFMPEG Tools.
    FFLOCATIONS = ['/opt/local/bin', '/usr/local/bin', '/usr/bin']
    for FF in FFLOCATIONS:
        FFMPEG = os.path.join(FF, 'ffprobe')
        FFPROBE = os.path.join(FF, 'ffprobe')
        if os.path.isfile(FFMPEG) and os.path.isfile(FFPROBE):
            return

    # Set HWAccels
    if configuration.hwaccel == 'cuda':
        HWACCEL = {'hwaccel': 'cuda'}
    elif configuration.hwaccel == 'videotoolbox':
        HWACCEL = {'hwaccel': 'videotoolbox'}
    else:
        HWACCEL = None
    return

    # Set Hardware Acceleration

    # Program Functions and Classes
    #
    # Apply the following to all when possible
    #
    # def function(**kwargs)






def getCLIparams(cli_args):
    if DEBUG:
        print('CLI Params {0}'.format(cli_args))
    parser = argparse.ArgumentParser(None)
    parser.prog = __prog_name__
    parser.description = "This program will create a video preview file of a given video"
    parser.epilog = """The filename of the output will be the edge_id-md5-originalBaseName.png.
    If the edge_id and md5 are unset the filename will be the original base name.png
    """


# Defaults for all programs
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s ' + __version__)

    # For different kinds of output, provide a choice

    parser.add_argument('-v', '--verbose',
                        help='Turn on verbose output',
                        action='store_true',
                        required=False,
                        dest='verbose',
                        default=VERBOSE
                        )

    parser.add_argument('-dr', '--dryrun',
                        help='Dryrun enabled no changes will occur',
                        action='store_true',
                        required=False,
                        dest='dryrun',
                        default=False
                        )

    parser.add_argument('-d', '--debug',
                        help='Turn on Debugging Mode',
                        action='store_true',
                        required=False,
                        dest='debug',
                        default=DEBUG
                        )

    parser.add_argument('-q', '--quiet',
                        help='No output is produced',
                        action='store_true',
                        required=False,
                        dest='quiet',
                        default=DEBUG
                        )

    parser.add_argument('-w', '--tile-width',
                        help='Tile width - Tiles are sqaure',
                        type=int,
                        action='store',
                        required=False,
                        dest='tile_width',
                        default='320'
                        )

    parser.add_argument('-r', '--tile-rows',
                        help='Number of rows for a preview',
                        action='store',
                        type=int,
                        required=False,
                        dest='tile_rows',
                        default='6'
                        )

    parser.add_argument('-c', '--tile-cols',
                        help='Number of columns for a preview',
                        action='store',
                        type=int,
                        required=False,
                        dest='tile_cols',
                        default='5'
                        )

    parser.add_argument('-b', '--tile-backgrond',
                        help='Tile Background Color',
                        action='store',
                        required=False,
                        dest='tile_bk_color',
                        default='black'
                        )

    parser.add_argument('-p', '--tile-foreground',
                        help='Tile Pen Color',
                        action='store',
                        required=False,
                        dest='tile_fg_color',
                        default='white'
                        )

    parser.add_argument('-i', '--input',
                        help='Video input, can by a file or directory. If directory, it will not be recursive',
                        type=str,
                        action='store',
                        required=False,
                        dest='in_file'
                        )

    parser.add_argument('-e', '--edge-id',
                        help='Edge Id of video, if set the filename will start with the edge_id',
                        type=str,
                        action='store',
                        required=False,
                        dest='edge_id'
                        )

    parser.add_argument('-o', '--output-dir',
                        help='Where to put the finished files',
                        type=str,
                        action='store',
                        required=False,
                        dest='out_dir',
                        default=os.getcwd()
                        )

    parser.add_argument('-m', '--md5',
                        help='Add the MD5 of the file to the filename',
                        action='store_true',
                        required=False,
                        dest='md5file',
                        default=False
                        )

    parser.add_argument('-s', '--store-db-file',
                        help='Store the video information in  SQLI3te file',
                        type=str,
                        action='store',
                        required=False,
                        dest='dbfile',
                        default=os.getcwd()
                        )

    parser.add_argument('-create-new-db',
                        help='Create a new database file',
                        action='store_true',
                        required=False,
                        dest='create_newdb',
                        default=False
                        )

    parser.add_argument('-override',
                        help='save image with this filename override all other possible choices',
                        type=str,
                        action='store',
                        required=False,
                        dest='override'
                        )

    parser.add_argument('-colors',
                        help='Display List of Available Colors',
                        action='store_true',
                        required=False,
                        dest='colors',
                        default=False
                        )

    parser.add_argument('-studio-id',
                        help='Replace the Studio ID with the EdgeID',
                        action='store',
                        required=False,
                        dest='studio_id',
                        default=None
                        )

    parser.add_argument('-hwaccel',
                        help='Enable Hardware acceleration for videotoolbox or cuda',
                        action='store',
                        choices=['cuda', 'videotoolbox'],
                        required=False,
                        dest='hwaccel',
                        default=None
                        )

    parse_out = parser.parse_args(cli_args)

    return parse_out


def main():
    CONFIG = getCLIparams(None)
    setup(CONFIG)

    myDB.connect()
    for video in VIDEOS:
        banner_info = dict()

        if not QUIET: print('Processing File {file}'.format(file=video))
        if not QUIET: print('Preview is {rows} rows x {cols} cols @ {width} width px'.format(rows=CONFIG.tile_rows,
                                                                                             cols=CONFIG.tile_cols,
                                                                                             width=CONFIG.tile_width))
        if not QUIET: print('Background Color is set to {color}'.format(color=CONFIG.tile_bk_color))

        SUCCESS, banner_info = video_info(filename=video)

        if not SUCCESS: return 1

        if CONFIG.md5file and not DRYRUN:
            md5value = md5Checksum(video)
            banner_info['md5'] = md5value
        elif CONFIG.md5file:
            banner_info['md5'] = "13227ada4af540092b7c5821c9ff321a"
            md5value = randomString(stringLength=32)
            banner_info['md5'] = md5value

        banner_info['filename'] = video
        banner_info['basename'] = os.path.basename(video)
        banner_info['dirname'] = os.path.dirname(video)

        if CONFIG.edge_id and CONFIG.studio_id:
            # Change the filename for display
            num_id = [str(i) for i in list(os.path.basename(banner_info['basename'].rsplit('.', 1)[0])) if i.isdigit()]
            banner_info['edge_id'] = CONFIG.edge_id + "".join(num_id)
        else:
            banner_info['edge_id'] = None

        output_filename = CONFIG.out_dir + "/"

        if CONFIG.md5file:
            output_filename += str(md5value) + "_"

        output_filename += os.path.basename(video).split('.')[0]

        if CONFIG.override:
            output_filename = CONFIG.out_dir + "/" + CONFIG.override

        if banner_info['edge_id']:
            output_filename = CONFIG.out_dir + "/" + banner_info['edge_id']

        if not QUIET and SUCCESS: print('Video Information: {info}'.format(info=banner_info))
        if not QUIET and SUCCESS: print('Output Filename = {output}'.format(output=output_filename))

        # calculate iables
        tile_rows = CONFIG.tile_rows
        tile_cols = CONFIG.tile_cols
        num_tiles = tile_rows * tile_cols
        tile_width = CONFIG.tile_width
        tile_bk_color = CONFIG.tile_bk_color
        video_frames = banner_info['video_frames']
        tile_mod = int(int(video_frames) / num_tiles)
        tile_expr = "not(mod(n," + str(tile_mod) + "))"
        tile_layout = str(tile_rows) + "x" + str(tile_cols)

        # Setup Preview Filters
        filter_select = {
                    'filter_name' : 'select',
            'expr': tile_expr
        }
        filter_scale = {
            'filter_name': 'scale',
            'w': tile_width,
            'h': '-1'

        }
        filter_tile = {'filter_name': 'tile',
                       'layout': tile_layout,
                       'padding': '4',
                       'margin': '4',
                       'color': tile_bk_color
                       }

        input_args = {
            'loglevel': '+panic',
            'hide_banner': None,
            'r': '10'
        }

        if HWACCEL: input_args.update(HWACCEL)

        # Create first image
        if not DRYRUN:
            try:
                out, err = (
                    ffmpeg
                        .input(video, **input_args)
                        .filter(**filter_select)
                        .filter(**filter_scale)
                        .filter(**filter_tile)
                        .output(output_filename + '.jpg', vframes=1, format='image2', vcodec='mjpeg', threads=1)
                        .overwrite_output()
                        .run(cmd=FFMPEG, capture_stdout=True)
                )
            except Exception as error:
                banner_info['comments'] = error

        else:
            with Image() as blank_img:
                blank_img.blank(2045, 1155, background=CONFIG.tile_bk_color)
                blank_img.save(filename=output_filename + '.jpg')

        # Get the size of the image
        with Image(filename=output_filename + '.jpg') as img:
            if DEBUG: print(img.size)
            image_width, image_height = img.size
            resize_width = int(round(image_width * 1.05))
            border_width = int((resize_width - image_width) / 2 * - 1)
            resize_height = int(round(image_height * 1.25))
            border_height = ((resize_height - image_height) * -1) - border_width

            img.background_color = tile_bk_color
            img.gravity = 'north'
            img.extent(
                width=resize_width,
                height=resize_height,
                x=border_width, y=border_height
            )

            img.save(filename=output_filename + '.tmp.jpg')

        if DEBUG: print('Image Border width {0} and height {1}'.format(border_width,border_height))

        # Create Banner Image
        if CONFIG.edge_id:
            message="Part Number: {EDGEID}\n".format(EDGEID=banner_info['edge_id'])
        else:
            message=""
        message += """{MP4NAME}
        {video_width} x {video_height} format {ASPECT}
        codec {codec_long_name}
        size {video_size}
        runtime {runtime} framerate {video_frame_rate}
        """.format(MP4NAME=banner_info['basename'],
                   video_height=banner_info['video_height'],
                   video_width=banner_info['video_width'],
                   ASPECT=banner_info['video_aspect'],
                   codec_long_name=banner_info['codec_long_name'],
                   video_size=banner_info['video_size'],
                   runtime=banner_info['video_duration'],
                   video_frame_rate=banner_info['video_frame_rate']

                   )
        if VERBOSE and not QUIET: print(message)

        with Drawing() as draw:
            draw.stroke_color = Color('White')
            draw.stroke_width = 1
            draw.font = 'helvitica'
            draw.font_size = 20
            draw.text_kerning = 2
            draw.fill_color = Color(CONFIG.tile_fg_color)
            with Image(filename=output_filename + '.tmp.jpg') as img:
                draw.draw(img)
                img.annotate(message, draw, 10, 30)
                img.save(filename=output_filename + '.jpg')

        os.remove(output_filename + '.tmp.jpg')

        if VERBOSE and not QUIET:
            im = Display(output_filename + '.jpg')
            im.show()

        myDB.insertORupdate(table='preview', key_field='filename', key_value=video, data=banner_info)
        myDB.commit()
    myDB.close()

    print('End of Program')

    return 0



if __name__ == "__main__":

    main()
