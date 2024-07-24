import requests, json
import argparse
from urllib.parse import quote

def parse_args(argv =None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--access_token', type=str, help='Your mapillary access token')
    parser.add_argument('--username', type=str, help='Username to get the sequences id of')
    parser.add_argument('--pictures', type=str, help='Limit of pictures to fetch')

    global args
    args = parser.parse_args(argv)


if __name__ == '__main__':
    parse_args()

    if args.access_token == None:
        print('please provide the access_token')
        exit()

    mly_key = args.access_token
    creator_username = args.username
    max_img= args.pictures

    url = f'https://graph.mapillary.com/images?access_token={mly_key}&creator_username={creator_username}&limit={max_img}&fields=id,sequence'

    response = requests.get(url)

    if response.status_code == 200:
       json = response.json()

       # tri des séquences uniques
       sequences_ids = [obj['sequence'] for obj in json['data']]
       unique_ids = list(set(sequences_ids))
       print(unique_ids)
    else:
       print(response)
