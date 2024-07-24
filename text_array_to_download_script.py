import os

input_file = 'input_file'

import argparse
def parse_args(argv =None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--dev_token', type=str, help='Your mapillary access token')
    parser.add_argument('--username', type=str, help='Username to get the sequences id of')

    global args
    args = parser.parse_args(argv)



if __name__ == '__main__':
    print("Construction du script bash de récupération des images de chaque séquences pour Mapillary_download (https://github.com/Stefal/mapillary_download.git)")

    parse_args()

    username=args.username
    input_file = f"sequences_{username}.txt"

    if not args.dev_token:
        print(f"Erreur : Le token de développeur de mapillary manque, vérifiez le fichier de variables secretes. Arrêt du script.")
        exit(1)

    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        print(f"Erreur : Le fichier '{input_file}' n'a pas été trouvé. Arrêt du script.")
        exit(1)
    else:
        print(f"Fichier '{input_file}' trouvé.")


    output_file = f"script_bash_get_sequences_for_user_{username}.sh"

    access_token = "--access_token='"+args.dev_token+"' "
    format_string = "/usr/bin/python3 mapillary_download.py {} --sequence_id={}\n"


    with open(output_file, "w") as output:
        with open(input_file, "r") as input_handle:
            content = input_handle.read()
            sequences = eval(content)
            for seq in sequences:
                full_cmd = f"/usr/bin/python3 mapillary_download.py {access_token} --sequence_id='{seq}' --username={username}\n"
                output.write(full_cmd)

    print(output_file)

    print(f"\n Script Bash généré avec succès.")
    print(f"Lancez le pour récupérer les photos de l'utilisateur {username}: \n bash {output_file}")

