#!/bin/bash
# récupérer les séquences pour un tas d'utilisateurs


# Liste des usernames
# example:
# usernames=( "riri" "fifi" "loulou")
usernames=( "someone_having_nice_pictures" "someone_else" "oh_look_a_these_usernames" )

# check env variables are valid
if [ -f "secrets_variables.sh" ]; then
  source "secrets_variables.sh"
  if [ "$MAPILLARY_DEV_TOKEN" = "MLY|blahblah_replace_it" ]; then
    echo "Erreur : La variable MAPILLARY_DEV_TOKEN doit être modifiée pour que le script fonctionne."
    echo "Veuillez remplacer la valeur par défaut \"MLY|blahblah_replace_it\" par votre propre token de développement Mapillary."
    exit 1
  fi
else
  echo "Erreur : Le fichier secrets_variables.sh n'a pas été trouvé."
  exit 1
fi

# Boucle sur la liste des usernames
for username in "${usernames[@]}"; do
  # Lancer la commande pour chaque username

echo "---------- utilisateur: $username"

  if [ ! -f "out_$username.json" ]; then
    bash find_user_id.sh $username
  fi
   # Vérifier si le fichier sequences_$username.txt existe
  if [ ! -f "sequences_$username.txt" ]; then
    python3 get_sequences_of_username.py --username="$username" --dev_token="$MAPILLARY_DEV_TOKEN" --max_sequence=9999
  else
    echo "le fichier sequences txt existe pour $username"
  fi
  # Lancer la commande pour chaque username
  if [ ! -f "script_bash_get_sequences_for_user_$username.sh" ]; then
  python3 text_array_to_download_script.py --username=$username --dev_token="$MAPILLARY_DEV_TOKEN"
  fi

done
echo "---------- finished getting users ------------"