import json
import requests
# lit un json listant les id de photo de chaque séquence et va
# chercher la séquence par API.

import argparse

def parse_args(argv =None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', type=str, help='Username to get the sequences id of')
    parser.add_argument('--dev_token', type=str, help='Your mapillary developer token')
    parser.add_argument('--max_sequence', type=str, help='Username to get the sequences id of')

    global args
    args = parser.parse_args(argv)
    print(args)



# Initialisation de la liste pour stocker les réponses
responses = []
sequences = []

def get_image_data_from_sequences():
    username = args.username
    input_file = "out_"+username+".json"


    # Chargement du fichier JSON d'entrée
    with open(input_file, "r") as file:
        input_data = json.load(file)

    # Itération sur les noeuds pour collectionner les image_ids
    nodelist = input_data["data"]["fetch__User"]["feed"]["nodes"]
    print( 'séquences : ', len(nodelist))
    image_ids = [node["image_id"] for node in nodelist]
    print(image_ids)

    dev_token = args.dev_token

    # Préparation de la tête d'autorisation pour toutes les futures requêtes
    header = {"Access-Token": dev_token}

    ii=0
    limit_requests = 1000000000
#     limit_requests = 5 # pour tester
    # Boucle sur chaque image_id pour interroger l'API Mapillary
    for image_id in image_ids:
        ii+=1
        if limit_requests >= ii and image_id:
            params = {"id": image_id, "fields": "id,sequence"}
            request_url = "https://graph.mapillary.com/" + str(image_id)+"?access_token="+dev_token+"&fields=id,sequence"
            # print("requete: "+request_url)

            response = requests.get(request_url)

            # Analyse de la réponse
            parsed_response = {}
            if response.ok and response.status_code == 200:
                raw_response = response.json()

                parsed_response["id"] = raw_response["id"]
                parsed_response["sequence"] = raw_response["sequence"]
                sequences.append(parsed_response["sequence"])

                print("séquence trouvée: "+str(ii)+"/"+args.max_sequence+" : "+raw_response["sequence"])
            else:
                print(response)

            responses.append(parsed_response)

def persist_files():
    # Sauvegarde des nouveaux résultats dans le fichier output.json
    output_file = "sequences_"+args.username+".json"

    with open(output_file, "w") as file:
        json.dump(responses, file)

    sequence_filename = "sequences_"+args.username+".txt"
    with open(sequence_filename, "w") as file:
        json.dump(sequences, file)
        print('fichier sauvegardé: '+sequence_filename)


parse_args()
get_image_data_from_sequences()
persist_files()

# si la requete donne moins du max de noeuds on prévoit d'en relancer une nouvelle pour avoir la suite
