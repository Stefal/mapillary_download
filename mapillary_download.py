import requests
from requests.adapters import HTTPAdapter
from requests.adapters import Retry
import json
import os
import concurrent.futures
import argparse
from datetime import datetime
import writer
from model import PictureType
import sys

session = requests.Session()
retries_strategies = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429,502, 503, 504],
    )
session.mount('https://', HTTPAdapter(max_retries=retries_strategies))

def parse_args(argv =None):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('access_token', type=str, help='Your mapillary access token')
    parser.add_argument('--sequence_ids', type=str, nargs='*', help='The mapillary sequence id(s) to download')
    parser.add_argument('--image_ids', type=int, nargs='*', help='The mapillary image id(s) to get their sequence id(s)')
    parser.add_argument('--destination', type=str, default='data', help='Path destination for the images')
    parser.add_argument('--image_limit', type=int, default=None, help='How many images you want to download')
    parser.add_argument('--overwrite', default=False, action='store_true', help='overwrite existing images')
    parser.add_argument("-v", "--version", action="version", version="release 1.7")
    args, remaining_args = parser.parse_known_args(argv)
    #args = parser.parse_args(argv)
    if args.sequence_ids is None and args.image_ids is None:
        parser.error("Please enter at least one sequence id or image id")
    args.sequence_ids = [id.strip() for id in args.sequence_ids]
    for unknown_arg in remaining_args:
        if len(unknown_arg) > 18:
            #this arg seems to be a sequence id.
            args.sequence_ids.append(unknown_arg.strip())
    return args

def download(url, filepath, metadata=None):   
    #print(asizeof.asizeof(image)/1024, "MB")
    with open(str(filepath), "wb") as f:
        r = session.get(url, stream=True, timeout=6)
        image = write_exif(r.content, metadata)
        f.write(image)
    print("{} downloaded".format(filepath))


def get_single_image_data(image_id, mly_header):
    req_url = 'https://graph.mapillary.com/{}?fields=creator,thumb_original_url,altitude,make,model,camera_type,captured_at,compass_angle,geometry,exif_orientation,sequence'.format(image_id)
    r = session.get(req_url, headers=mly_header)
    data = r.json()
    print(data)
    return data


def get_image_data_from_sequences(sequences_id, mly_header):
    for i,sequence_id in enumerate(sequences_id):
        url = 'https://graph.mapillary.com/image_ids?sequence_id={}'.format(sequence_id)
        r = requests.get(url, headers=header)
        data = r.json()
        image_ids = data['data']
        total_image = len(image_ids)
        print("{} images in sequence {} of {}  - id : {}".format(total_image, i+1, len(sequences_id), sequence_id))
        print('getting images data')
        for x in range(0, total_image):
            image_id = image_ids[x]['id']
            image_data = get_single_image_data(image_id, mly_header)
            image_data['sequence_id'] = sequence_id
            yield image_data


def get_image_data_from_sequences__future(sequences_id, mly_header):
    for i,sequence_id in enumerate(sequences_id):
        url = 'https://graph.mapillary.com/image_ids?sequence_id={}'.format(sequence_id)
        r = requests.get(url, headers=header)
        data = r.json()
        if data.get('data') == []:
            print("Empty or wrong sequence {} of {} - id : {}".format(i+1, len(sequences_id), sequence_id))
            continue
        image_ids = data['data']
        total_image = len(image_ids)
        print("{} images in sequence {} of {}  - id : {}".format(total_image, i+1, len(sequences_id), sequence_id))
        print('getting images data')

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {}
            for x in range(0, total_image):
                image_id = image_ids[x]['id']
                future_to_url[executor.submit(get_single_image_data, image_id, mly_header)] = image_id
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                image_data = future.result()
                image_data['sequence_id'] = sequence_id
                #print(image_data)
                yield image_data


def write_exif(picture, img_metadata):
    '''
    Write exif metadata
    '''
    #{'thumb_original_url': 'https://scontent-cdg4-2.xx.fbcdn.net/m1/v/t6/An9Zy2SrH9vXJIF01QkBODyUbg7XSKfwL48UwHyvihSwvECGjVbG0vSw9uhxe2-Dq-k2eUcigb83buO6zo-7eVbykfp5aQIe1kgd-MJr66nU_H-o_mwBLZXgVbj5I_5WX-C9c6FxJruHkV962F228O0?ccb=10-5&oh=00_AfDOKD869DxL-4ZNCbVo8Rn29vsc0JyjMAU2ctx4aAFVMQ&oe=65256C25&_nc_sid=201bca',
    #  'captured_at': 1603459736644, 'geometry': {'type': 'Point', 'coordinates': [2.5174596904057, 48.777089857534]}, 'id': '485924785946693'}
    
    with writer.Writer(picture) as image:
        image.add_artist(img_metadata)
        image.add_camera_make(img_metadata)
        image.add_camera_model(img_metadata)
        image.add_datetimeoriginal(img_metadata)
        image.add_lat_lon(img_metadata)
        image.add_altitude(img_metadata)
        image.add_direction(img_metadata)
        image.add_img_projection(img_metadata)
        image.apply()
        updated_image = image.get_Bytes()

    return updated_image


if __name__ == '__main__':
    
    args = parse_args()
    sequence_ids= args.sequence_ids if args.sequence_ids is not None else []
    images_ids = args.image_ids
    access_token = args.access_token
    images_data = []
    header = {'Authorization' : 'OAuth {}'.format(access_token)}

    if images_ids:
        for image_id in images_ids:
            image_data = get_single_image_data(image_id, header)
            if 'error' in image_data:
                print("data : ", image_data)
                print("something wrong happened ! Please check your image id and/or your connection")
                sys.exit()
            else:
                sequence_ids.append(image_data.get('sequence'))

    #for i,image_data in enumerate(get_image_data_from_sequences(sequence_ids, header)):
    for i,image_data in enumerate(get_image_data_from_sequences__future(sequence_ids, header)):
        if args.image_limit is not None and i >= args.image_limit:
            break
        if 'error' in image_data:
            print("data : ", image_data)
            print("something wrong happened ! Please check your token and/or your connection")
            sys.exit()
        images_data.append(image_data)
    #sys.exit()

    print('downloading.. this process will take a while. please wait')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        for i,image_data in enumerate(images_data):
            # create a folder for each unique sequence ID to group images by sequence
            path_destination = os.path.join(args.destination, image_data['sequence_id'])
            if not os.path.exists(path_destination):
                os.makedirs(path_destination)
            date_time_image_filename = datetime.utcfromtimestamp(int(image_data['captured_at'])/1000).strftime('%Y-%m-%d_%HH%Mmn%Ss%f')[:-3] + '.jpg'
            path = os.path.join(path_destination, date_time_image_filename)
            img_metadata = writer.PictureMetadata(
                    capture_time = datetime.utcfromtimestamp(int(image_data['captured_at'])/1000),
                    artist = image_data['creator']['username'],
                    camera_make = image_data['make'],
                    camera_model = image_data['model'],
                    longitude = image_data['geometry']['coordinates'][0],
                    latitude = image_data['geometry']['coordinates'][1],
                    picture_type = PictureType("equirectangular") if image_data.get('camera_type') == 'spherical' or image_data.get('camera_type') == 'equirectangular' else PictureType("flat"),
                    direction = image_data['compass_angle'],
                    altitude = image_data['altitude'],
            )
            #print("metadata: ", img_metadata)
            #print("path: ", image_data)
            image_exists = os.path.exists(path)
            if not args.overwrite and image_exists:
                print("{} already exists. Skipping ".format(path))
                continue
            executor.submit(download, url=image_data['thumb_original_url'], filepath=path, metadata=img_metadata)
            #download(url=image_data['thumb_original_url'], filepath=path, metadata=img_metadata)
