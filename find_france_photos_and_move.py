###
# Filtrage de photos situées en France dans un dossier contenant des séquences de photo géolocalisées
# Rechercher et déplacer automatiquement les photos géolocalisées dans une certaine bounding box et les déplacer dans le dossier de destination.
#
# utilisation:
# python find_france_photos_and_move.py --source_dir /chemin/du/répertoire/source --destination_dir /chemin/du/répertoire/destination
#
###
import argparse
import os
import shutil
import exifread

# Définition du rectangle entourant la France métropolitaine et un peu autour
france_bbox: tuple[float, float, float, float] = (42.0, -5.0, 51.0, 10.0)  # (lat_min, lon_min, lat_max, lon_max)
# Définition du rectangle entourant la France métropolitaine et un peu autour
france_bbox: tuple[float, float, float, float] = (42.0, -5.0, 51.0, 10.0)  # (lat_min, lon_min, lat_max, lon_max)

# Définition du rectangle entourant la Guadeloupe
guadeloupe_bbox: tuple[float, float, float, float] = (15.8, -61.8, 17.3, -59.3)

# Définition du rectangle entourant la Martinique
martinique_bbox: tuple[float, float, float, float] = (14.3, -61.3, 15.1, -59.3)

# Définition du rectangle entourant la Guyane française
guyane_bbox: tuple[float, float, float, float] = (2.0, -54.5, 6.5, -51.5)

# Définition du rectangle entourant La Réunion
reunion_bbox: tuple[float, float, float, float] = (-21.3, 55.2, -20.8, 55.8)

# Définition du rectangle entourant Mayotte
mayotte_bbox: tuple[float, float, float, float] = (-13.0, 45.0, -12.5, 45.5)

# Définition du rectangle entourant Saint-Pierre-et-Miquelon
spm_bbox: tuple[float, float, float, float] = (46.7, -56.2, 47.1, -55.6)

# Définition du rectangle entourant les îles de Saint-Martin et Saint-Barthélemy
stm_sbh_bbox: tuple[float, float, float, float] = (18.0, -64.5, 18.5, -62.5)

# Définition du rectangle entourant Wallis-et-Futuna
wf_bbox: tuple[float, float, float, float] = (-13.3, -176.2, -13.1, -175.8)

# Définition du rectangle entourant la Nouvelle-Calédonie
nc_bbox: tuple[float, float, float, float] = (-22.5, 165.5, -18.5, 169.5)

# Définition du rectangle entourant la Polynésie française
pf_bbox: tuple[float, float, float, float] = (-27.5, -140.0, -7.5, -134.0)

# Définition du rectangle entourant les Terres australes et antarctiques françaises
taaf_bbox: tuple[float, float, float, float] = (-49.5, 68.5, -37.5, 77.5)

# Chemin du répertoire source
source_dir: str = '/home/cipherbliss/Téléchargements/FIBRELAND/TEST_IN_FR/'

# Chemin du répertoire destination
destination_dir: str = '/home/cipherbliss/Téléchargements/FIBRELAND/IN_FRANCE/'
sequence_folder: str = 'principale_sequence'
count_files_all: int = 0
count_files_moved: int = 0
# Crée le répertoire destination si il n'existe pas
if not os.path.exists(destination_dir):
    os.makedirs(destination_dir)


# Fonction pour déplacer un fichier si il est dans le rectangle de la France
def move_file_if_in_france(filepath, sequence_folder):
    global count_files_all
    global count_files_moved

    # Ouvre le fichier image et lit les informations EXIF
    latitude, longitude = get_gps_info(filepath)

    if latitude and longitude:
        print(f'Latitude: {latitude}, Longitude: {longitude}')
        if are_lat_lon_in_france(latitude, longitude):
            move_file_in_destination(filepath, sequence_folder)
    else:
        print('Informations GPS non trouvées')


def move_file_in_destination(filepath, sequence_folder):
    global count_files_moved
    # Déplace le fichier dans le sous-répertoire "photos_in_france"
    dest_subdir = os.path.join(destination_dir, sequence_folder,
                               os.path.basename(os.path.dirname(filepath)))
    if not os.path.exists(dest_subdir):
        os.makedirs(dest_subdir)
    shutil.move(filepath, os.path.join(dest_subdir, filepath))
    count_files_moved += 1
    print(f"Moved {filepath} to {dest_subdir}")
    return True

def are_lat_lon_in_france(gps_lat, gps_lon):
    """
    recherche d'une zone du territoire français


    France métropolitaine : 551 695 km²
    Terres australes et antarctiques françaises : 432 000 km²
    Guyane française : 83 534 km²
    Nouvelle-Calédonie : 18 575 km²
    Polynésie française : 4 167 km²
    La Réunion : 2 512 km²
    Martinique : 1 128 km²
    Guadeloupe : 1 628 km²
    Mayotte : 374 km²
    Saint-Pierre-et-Miquelon : 242 km²
    Wallis-et-Futuna : 142 km²
    Saint-Martin et Saint-Barthélemy : 53 km²


    :param gps_lat:
    :param gps_lon:
    :return:
    """
    global france_bbox, guyane_bbox, nc_bbox, pf_bbox, reunion_bbox, guadeloupe_bbox, martinique_bbox, mayotte_bbox, spm_bbox, stm_sbh_bbox, wf_bbox, taaf_bbox

    print("lat lon :", gps_lat, gps_lon)

    if (france_bbox[0] <= gps_lat <= france_bbox[2] and france_bbox[1] <= gps_lon <= france_bbox[3]):
        return "France métropolitaine"
    elif (taaf_bbox[0] <= gps_lat <= taaf_bbox[2] and taaf_bbox[1] <= gps_lon <= taaf_bbox[3]):
        return "Terres australes et antarctiques françaises"
    elif (guyane_bbox[0] <= gps_lat <= guyane_bbox[2] and guyane_bbox[1] <= gps_lon <= guyane_bbox[3]):
        return "Guyane française"
    elif (reunion_bbox[0] <= gps_lat <= reunion_bbox[2] and reunion_bbox[1] <= gps_lon <= reunion_bbox[3]):
        return "La Réunion"
    elif (wf_bbox[0] <= gps_lat <= wf_bbox[2] and wf_bbox[1] <= gps_lon <= wf_bbox[3]):
        return "Wallis-et-Futuna"
    elif (stm_sbh_bbox[0] <= gps_lat <= stm_sbh_bbox[2] and stm_sbh_bbox[1] <= gps_lon <= stm_sbh_bbox[3]):
        return "Saint-Martin et Saint-Barthélemy"
    elif (spm_bbox[0] <= gps_lat <= spm_bbox[2] and spm_bbox[1] <= gps_lon <= spm_bbox[3]):
        return "Saint-Pierre-et-Miquelon"
    elif (mayotte_bbox[0] <= gps_lat <= mayotte_bbox[2] and mayotte_bbox[1] <= gps_lon <= mayotte_bbox[3]):
        return "Mayotte"
    elif (martinique_bbox[0] <= gps_lat <= martinique_bbox[2] and martinique_bbox[1] <= gps_lon <= martinique_bbox[3]):
        return "Martinique"
    elif (guadeloupe_bbox[0] <= gps_lat <= guadeloupe_bbox[2] and guadeloupe_bbox[1] <= gps_lon <= guadeloupe_bbox[3]):
        return "Guadeloupe"

    elif (pf_bbox[0] <= gps_lat <= pf_bbox[2] and pf_bbox[1] <= gps_lon <= pf_bbox[3]):
        return "Polynésie française"
    elif (nc_bbox[0] <= gps_lat <= nc_bbox[2] and nc_bbox[1] <= gps_lon <= nc_bbox[3]):
        return "Nouvelle-Calédonie"
    else:
        return None # "Hors de France"


def get_gps_info(filepath):
    with open(filepath, 'rb') as f:
        tags = exifread.process_file(f)
        gps_info = {}

        # Recherche les informations GPS dans les informations EXIF

        # print("clés exif ", tags.keys())
        for tag in tags.keys():
            if tag.startswith('GPS'):
                gps_info[tag] = tags[tag]

        # Extraction des informations de latitude et de longitude
        gps_latitude = convert_rational_to_float(gps_info.get('GPS GPSLatitude'))
        gps_longitude = convert_rational_to_float(gps_info.get('GPS GPSLongitude'))

        if gps_latitude and gps_longitude:
            return gps_latitude, gps_longitude
        else:
            return None, None


def convert_rational_to_float(rational):
    return float(rational.values[0].num) / float(rational.values[0].den)





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source_dir', default='/home/cipherbliss/Téléchargements/FIBRELAND/TEST_IN_FR/', help='Chemin du répertoire source')
    parser.add_argument('--destination_dir', default='/home/cipherbliss/Téléchargements/FIBRELAND/IN_FRANCE/', help='Chemin du répertoire destination')
    parser.add_argument('--sequence_folder', default='principale_sequence', help='Nom du dossier de séquence')
    args = parser.parse_args()

    # Parcourt tous les fichiers dans le répertoire source et ses sous-répertoires
    for root, dirs, files in os.walk(args.source_dir):
        for filename in files:
            # Vérifie si le fichier est une image
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif')):
                filepath = os.path.join(root, filename)
                move_file_if_in_france(filepath, sequence_folder)

    print('fichiers se situant en france déplacés: ', count_files_moved, ' / ', count_files_all)