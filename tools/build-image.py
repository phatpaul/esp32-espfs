#!/usr/bin/env python

import os
import shutil
import subprocess
import sys

ESPFS_IMAGEROOTDIR = sys.argv[1]

BUILD_DIR = os.environ.get('BUILD_DIR')
CONFIG_ESPFS_PREPROCESS_FILES = os.environ.get('CONFIG_ESPFS_PREPROCESS_FILES')
CONFIG_ESPFS_CSS_MINIFY_UGLIFYCSS = os.environ.get('CONFIG_ESPFS_CSS_MINIFY_UGLIFYCSS')
CONFIG_ESPFS_HTML_MINIFY_HTMLMINIFIER = os.environ.get('CONFIG_ESPFS_HTML_MINIFY_HTMLMINIFIER')
CONFIG_ESPFS_JS_CONVERT_BABEL = os.environ.get('CONFIG_ESPFS_JS_CONVERT_BABEL')
CONFIG_ESPFS_JS_MINIFY_BABEL = os.environ.get('CONFIG_ESPFS_JS_MINIFY_BABEL')
CONFIG_ESPFS_JS_MINIFY_UGLIFYJS = os.environ.get('CONFIG_ESPFS_JS_MINIFY_UGLIFYJS')
CONFIG_ESPFS_UGLIFYCSS_PATH = os.environ.get('CONFIG_ESPFS_UGLIFYCSS_PATH}') or 'uglifycss'
CONFIG_ESPFS_HTMLMINIFIER_PATH = os.environ.get('CONFIG_ESPFS_HTMLMINIFIER_PATH') or 'html-minifier'
CONFIG_ESPFS_BABEL_PATH = os.environ.get('CONFIG_ESPFS_BABEL_PATH') or 'babel'
CONFIG_ESPFS_UGLIFYJS_PATH = os.environ.get('CONFIG_ESPFS_UGLIFYJS_PATH') or 'uglifyjs'

os.chdir(BUILD_DIR)
os.environ["PATH"] += os.pathsep + str(os.path.join(BUILD_DIR, 'bin'))

if CONFIG_ESPFS_PREPROCESS_FILES == 'y':
    build = os.path.join(BUILD_DIR, 'espfs')
    shutil.rmtree(str(build), ignore_errors=True)
    for root, _, files in os.walk(ESPFS_IMAGEROOTDIR):
        dest = os.path.relpath(root, ESPFS_IMAGEROOTDIR)
        if dest == '.':
            dest = build
        else:
            dest = os.path.join(build, dest)
        if not os.path.isdir(dest):
            os.mkdir(str(dest))
        for filename in files:
            source = os.path.join(root, filename)
            destfile = os.path.join(dest, filename)
            _, ext = os.path.splitext(source)
            if ext == '.css' and CONFIG_ESPFS_CSS_MINIFY_UGLIFYCSS == 'y':
                with open(str(destfile), 'w') as f:
                    subprocess.check_call([CONFIG_ESPFS_UGLIFYCSS_PATH, str(source)], stdout=f)
            elif ext in ['.html', '.htm'] and CONFIG_ESPFS_HTML_MINIFY_HTMLMINIFIER == 'y':
                with open(str(destfile), 'w') as f:
                    subprocess.check_call([CONFIG_ESPFS_HTMLMINIFIER_PATH,
                        '--collapse-whitespace', '--remove-comments',
                        '--use-short-doctype', '--minify-css true',
                        '--minify-js', 'true', str(source)], stdout=f)
            elif ext == '.js' and (CONFIG_ESPFS_JS_CONVERT_BABEL == 'y' or \
                    CONFIG_ESPFS_JS_MINIFY_BABEL == 'y' or \
                    CONFIG_ESPFS_JS_MINIFY_UGLIFYJS == 'y'):
                with open(str(destfile), 'w') as f:
                    if CONFIG_ESPFS_JS_CONVERT_BABEL == 'y' and CONFIG_ESPFS_JS_MINIFY_BABEL == 'y':
                        subprocess.check_call([CONFIG_ESPFS_BABEL_PATH, '--presets',
                            '@babel/preset-env,minify', str(source)], stdout=f)
                    elif CONFIG_ESPFS_JS_CONVERT_BABEL == 'y' and CONFIG_ESPFS_JS_MINIFY_UGLIFYJS == 'y':
                        babel = subprocess.check_call([CONFIG_ESPFS_BABEL_PATH, '--presets',
                            '@babel/preset-env', str(source)], stdout=subprocess.PIPE)
                        subprocess.check_call([CONFIG_ESPFS_UGLIFYJS_PATH], stdin=babel.stdout, stdout=f)
                    elif CONFIG_ESPFS_JS_CONVERT_BABEL == 'y':
                        subprocess.check_call([CONFIG_ESPFS_BABEL_PATH, '--presets',
                            '@babel/preset-env', str(source)], stdout=f)
                    elif CONFIG_ESPFS_JS_MINIFY_BABEL == 'y':
                        subprocess.check_call([CONFIG_ESPFS_BABEL_PATH, '--presets',
                            'minify', str(source)], stdout=f)
                    elif CONFIG_ESPFS_JS_MINIFY_UGLIFYJS == 'y':
                        with open(str(source), 'r') as infile:
                            subprocess.check_call([CONFIG_ESPFS_UGLIFYJS_PATH], stdin=infile, stdout=f)
            else:
                shutil.copy2(str(source), str(dest))
    ESPFS_IMAGEROOTDIR = build

os.chdir(str(ESPFS_IMAGEROOTDIR))

filelist = []
for root, _, files in os.walk(ESPFS_IMAGEROOTDIR):
    path = os.path.relpath(root, ESPFS_IMAGEROOTDIR)
    filelist.append(path)
    for filename in files:
        filelist.append(os.path.join(path, filename))

espfs_image_path = os.path.join(BUILD_DIR, 'espfs_image.bin')
with open(str(espfs_image_path), 'wb') as f:
    mkespfsimage = subprocess.Popen(['mkespfsimage'], stdin=subprocess.PIPE, stdout=f)
    mkespfsimage.communicate(('\n'.join(filelist) + '\n').encode('utf-8'))

os.chdir(BUILD_DIR)
#os.makedirs('include', exist_ok=True)
# python 2.7 doesn't understand exist_ok
path = 'include'
try: 
    os.makedirs(path)
except OSError:
    if not os.path.isdir(path):
        raise
subprocess.check_call(['xxd', '-i', 'espfs_image.bin', 'include/espfs_image_bin.h'])
