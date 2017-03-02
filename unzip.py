from __future__ import print_function

import boto3
import os
import glob
import shutil
import urllib
import zipfile
import mimetypes

s3 = boto3.client('s3')
tmp = '/tmp'

# todo: handle invalid files (__MACOSX, .git, etc.)
def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    url = event['Records'][0]['s3']['object']['key'].encode('utf8')
    key = urllib.unquote_plus(url)

    s3_path = os.path.dirname(key)
    zip_name = os.path.basename(key)
    target = os.path.join(tmp, zip_name)

    print('bucket: ', bucket)
    print('url: ', url)
    print('key: ', key)
    print('s3_path: ', s3_path)
    print('target: ', target)

    try:
        print('Cleaning tmp directory: ' + tmp)
        empty_dir(tmp)

        print('Downloading zip file: ' + key + ' from bucket ' + bucket)
        s3.download_file(bucket, key, target)

        print('Unzipping: ' + target)
        unzip_and_upload(bucket, key, target)

        print('Deleting ' + key + ' from S3')
        s3.delete_object(Bucket=bucket, Key=key)

        return "Unzipped -> {}".format(key)
    except Exception as e:
        print(e)
        return 'Error'

    return 'Success'


# rest of the functions

def get_s3_destination_dir(bucket, key):
    # key = some/directory/gallery.zip

    # 1. Get directory name from zip name
    s3_path = os.path.dirname(key)
    zip_name = os.path.basename(key)
    name = os.path.splitext(zip_name)[0]

    # 2. test that s3:your-bucket/some/directory/gallery/* doesn't exist
    suffix = 0
    retry = True
    available_name = name

    while retry:
        path = os.path.join(s3_path, available_name)
        retry = s3_path_exists(bucket, path, key)
        if retry:
            suffix += 1
            available_name = name + str(suffix)

    return available_name

# tests if a folder exists on S3
def s3_path_exists(bucket, path, accepted_key):
    res = s3.list_objects(Bucket=bucket, Prefix=path)
    if ( res.has_key('Contents') and len(res.get('Contents')) > 0 ):
        for item in res.get('Contents'):
            if item['Key'] == accepted_key:
                continue;
            return True
    return False

def unzip_and_upload(bucket, key, target):
    # get the name of the destination directory on S3
    name = get_s3_destination_dir(bucket, key)

    # compute the s3 path
    s3_path = os.path.join(os.path.dirname(key), name)

    zfile = zipfile.ZipFile(target)
    namelist = zfile.namelist()
    for filename in namelist:
        if filename.startswith('__MACOSX'):
            continue

        # skip directories
        if filename.endswith('/'):
            continue

        fileobj = zfile.open(filename)

        # read mime type
        type, encoding = mimetypes.guess_type(filename)

        extra_args = {'ACL':'public-read'}
        if type is not None:
            extra_args['ContentType'] = type

        print('uploading to s3: ' + os.path.join(s3_path, filename + ' ['+str(type)+']'))
        s3.upload_fileobj(fileobj, bucket, os.path.join(s3_path, filename), ExtraArgs=extra_args)


def empty_dir(path):
    for dirpath, dirnames, filenames in os.walk(path):
        break
    for dir in dirnames:
        shutil.rmtree( os.path.join(path, dir) )
    for file in filenames:
        os.unlink( os.path.join(path, file) )

def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def list_filesize(filepath):
    if os.path.isfile(filepath):
        fileinfo = os.stat(filepath)
        return 'Size of ' + filepath + ' is ' + convert_bytes(fileinfo.st_size)
    return 'NOT A FILE'
