# aws-lambda-unzip

A Python Lambda function to uncompress a zip file from S3 in the same location as the original file.

## Trigger configuration

- Bucket: [choose your S3 bucket]
- Trigger type: S3
- Event type: Object Created (All)
- Suffix: zip

## How it works

1. The `/tmp` directory is emptied. 
2. The zip file is downloaded to `/tmp`.
3. A directory is created with the name of the zip file (without the extension). If the same path on S3 already exists, a number will be appended to this name and incremented until the same S3 path is found available.
4. While iterating on the files in the zip file, each file is created on disk in the specified directory, then uploaded to S3 and immediately deleted to optimize the available disk space.

**Note that the container running the function is limited to having 500 MB disk space. No check are currently made to the zip file to check the filesize.**

## Todo list

- Check if there's enough disk space to download the zip file.
- Make sure that the ContentType property is valid.
