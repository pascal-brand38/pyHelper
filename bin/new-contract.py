'''
Regedit in
    HKEY_CLASSES_ROOT
        *
            shell
                Nouveau Contrat
                    Command
default is
    C:\msys64\msys2_shell.cmd -mingw64 -c 'python dev/pascal-brand38/pyHelper/bin/new-contract.py --blank-contract=mon-contrat.pdf --old-contract="$0" "--dir-contract=$1"'  "%1" "%w"
%1 is the full filename of the old contract we right-click on
%w is the directory  

# TODO: does not work with accent
#       requires htmlencode

mkdir -p dev/pascal-brand38
cd dev/pascal-brand38
git clone git@github.com:pascal-brand38/pyHelper.git
git clone https://github.com/pascal-brand38/pyHelper.git

source ~/dev/pascal-brand38/pyHelper/install.sh
python3 -m pip install git+https://github.com/pascal-brand38/pyHelper.git

'''

import sys
import re
import os
import getopt
from pyHelper import pdfReaderHelper, pdfWriterHelper
import subprocess
import html
import datetime

def usage():
    print('*** ERREUR ***')
    print('new-contract.py [--blank-contract=<>] [--dir-contract=<>] [--old-contract=]')

def replace_backslash(arg):
    return arg.replace('\\', '').replace('C:','XXX')

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def get_immediate_files(a_dir, start):
    return [name for name in os.listdir(a_dir)
            if (os.path.isfile(os.path.join(a_dir, name)) and (name.startswith(start))) ]

def unescape(s):
    try:
        res = html.unescape(s)
    except:
        res = s
    return res

def get_args(argv):
    print(argv)
    
    try:
        opts, args = getopt.getopt(argv,"h:", [
            "blank-contract=",
            "dir-contract=",
            "old-contract=",
            "root-contract=",
            "who=",
            "from=",
            "to=",
            "priceday=",
            "nbdays=",
            "services=",
            "total=",
            "accompte=",
            "date_accompte=",
            "solde=",
        ])
    except getopt.GetoptError as e:
        usage()
        raise e


    get_args._blank_contract = ''
    get_args._dir_contract = ''
    get_args._old_contract = ''
    get_args._root_contract = ''
    get_args._who = ''
    get_args._from = ''
    get_args._to= ''
    get_args._priceday = ''
    get_args._nb_days = ''
    get_args._services = '0€'
    get_args._total = ''
    get_args._accompte = '0'
    get_args._date_accompte = ''
    get_args._solde = ''

    # get arguments
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("--blank-contract"):
            get_args._blank_contract = unescape(arg)
        elif opt in ("--dir-contract"):
            get_args._dir_contract = unescape(arg)
        elif opt in ("--old-contract"):
            get_args._old_contract = unescape(arg)
        elif opt in ("--root-contract"):
            get_args._root_contract = unescape(arg)
        elif opt in ("--who"):
            get_args._who = unescape(arg)
        elif opt in ("--from"):
            get_args._from = unescape(arg)
        elif opt in ("--to"):
            get_args._to= unescape(arg)
        elif opt in ("--priceday"):
            get_args._priceday = unescape(arg)
        elif opt in ("--nbdays"):
            get_args._nb_days = unescape(arg)
        elif opt in ("--services"):
            get_args._services = unescape(arg)
        elif opt in ("--total"):
            get_args._total = unescape(arg)
        elif opt in ("--accompte"):
            get_args._accompte = unescape(arg)
        elif opt in ("--date_accompte"):
            get_args._date_accompte = unescape(arg)
        elif opt in ("--solde"):
            get_args._solde = unescape(arg)

    if get_args._dir_contract != "":
        get_args._root_contract = get_args._dir_contract + '\\..\\'
    if get_args._dir_contract == "":
        # check for the contract dir given get_args._who
        cat_name = re.sub(' /.*', '', get_args._who)
        candidates = []
        subdirs = get_immediate_subdirectories(get_args._root_contract)
        for subdir in subdirs:
            if re.sub(' .*', '', subdir) == cat_name:
                candidates = candidates + [ subdir ]
        if len(candidates) == 1:
            get_args._dir_contract = get_args._root_contract + '\\' + candidates[0]
            print("Répertoire du contrat: ", get_args._dir_contract)
    
    if get_args._dir_contract == "":
            raise Exception('ERREUR: Impossible de déduire le nom du répertoire du contrat')

    if get_args._old_contract == "":
        files = get_immediate_files(get_args._dir_contract, '20')
        get_args._old_contract = get_args._dir_contract + '\\' + files[len(files)-1]
    
def main(argv):
    get_args(argv)
    # read old contract
    old_pdf = pdfReaderHelper(open(get_args._old_contract, "rb"))
    dict_old_pdf = old_pdf.get_form_fields_in_list(['/Tx', '/Btn']) # returns a python dictionary

    # replace new dates,...
    dict_old_pdf['Date darrivée'] = get_args._from
    dict_old_pdf['Date de départ'] = get_args._to
    dict_old_pdf['Nombre de jours'] = get_args._nb_days
    dict_old_pdf['Tarif Journalier'] = get_args._priceday + '€'
    dict_old_pdf['Total du séjour avec services'] = get_args._total + '€'
    dict_old_pdf['Acompte de 30  à la réservation'] = get_args._accompte + '€'
    dict_old_pdf['versé le'] = get_args._date_accompte
    dict_old_pdf['Le solde de la pension sera versé le jour de larrivée soit'] = get_args._solde + '€'
    dict_old_pdf['Services soins santé arrivéedépart dimanche'] = get_args._services

    # clear dictionnary
    key_to_clear = [
        'Heure', 'Heure_2',   # arrival and departure time
        'Date', 'Nom', 'Date_2', 'Nom_2',       # Puce / vermifuge
    ]

    try:
        for key in key_to_clear:
            dict_old_pdf.pop(key)
    except:
        pass

    # for key in dict_old_pdf:
    #     print(key, '   -----   ', dict_old_pdf[key])

    # read new contract
    new_pdf = pdfReaderHelper(open(get_args._root_contract + '\\' + get_args._blank_contract, "rb"))

    # write new contract at correct place
    output = pdfWriterHelper()

    # Add all pages
    for p in new_pdf.pages:
        output.add_page(p)

    # update fields
    output.update_page_form_field_values(output.pages[0], dict_old_pdf)
    output.update_page_form_field_values(output.pages[1], dict_old_pdf)
    basename = os.path.basename(get_args._old_contract)
    if get_args._from == '':
        prefix = 'nouveau - '
    else:
        d = datetime.datetime.strptime(get_args._from, '%d/%m/%Y')
        prefix = datetime.datetime.strftime(d, '%Y - %m - %d') + ' - '

    #new_filename = re.sub('[0-9]{4} - [0-9]{2}', prefix, basename)  # TODO: may have the day!
    new_filename = basename
    new_filename = re.sub('^[0-9]*[a-z]? - ', '', new_filename)
    new_filename = re.sub('^[0-9]*[a-z]? - ', '', new_filename)
    new_filename = re.sub('^[0-9]*[a-z]? - ', '', new_filename)
    if new_filename == basename:
        new_filename = 'nouveau - ' + get_args._blank_contract
    else:
        new_filename = prefix + new_filename
    new_filename = get_args._dir_contract + '/' + new_filename

    if os.path.exists(new_filename):
        raise Exception('ERREUR: le contrat ' + new_filename + ' existe déjà')
    outputStream = open(new_filename, "wb")
    output.write(outputStream)
    outputStream.close()
    print('Le contrat ' + new_filename + ' a été crée')
    subprocess.Popen([
        'explorer',
        get_args._dir_contract
        ])
    subprocess.Popen([      # Popen does not wait - call waits
        'C:\Program Files\Tracker Software\PDF Viewer\PDFXCview.exe',
        new_filename
        ])


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
        print('')
        print('******************************')
        print('******** CONTRAT CREE ********')
        print('******************************')
        print('')

    except Exception as e:
        print('++++++++ Exceptions')
        print(e)
        print('')
        print('*********************************')
        print('******** ERREUR DETECTEE ********')
        print('*********************************')
        print('')
        input('Appuyer sur "Entrée" pour terminer')
