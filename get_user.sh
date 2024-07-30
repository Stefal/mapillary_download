#!/bin/bash
# lancement de la récupération des identifiants de séquences
# exemple:
# bash get_user.sh binerf 102718865306727

source secrets_variables.sh

export username=$1
export num_user=$2
echo "télécharger la séquence pour l'utilisateur $username, $num_user"
bash curl_land.sh "$username" "$num_user" > "out_${username}.json"

echo "séquences récupérées:"
num_sequences=$(grep -o -w 'image_id' "out_${username}.json" | wc -l)
#
if (( num_sequences > 0 ))
then
    echo "Séquences trouvées: (${num_sequences}). Noice."
    python3 get_sequences_of_username.py --username="$username" --max_sequence="$num_sequences" --dev_token="$MAPILLARY_DEV_TOKEN"
    python3 text_array_to_download_script.py --username="$username" --dev_token="$MAPILLARY_DEV_TOKEN"
##
else
    echo "Aucune séquence trouvée (${num_sequences}) ! Pas d'autres actions à entreprendre."
#    cat "out_${username}.json"
fi


