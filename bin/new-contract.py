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

def usage():
    print('*** ERREUR ***')
    print('new-contract.py [--blank-contract=<>] [--dir-contract=<>] [--old-contract=]')
    raise Exception('ERREUR DE CONFIGURATION - APPELER PASCAL')

def get_args(argv):
    # for a in argv:
    #     print(a)

    try:
        opts, args = getopt.getopt(argv,"h:",["blank-contract=", "dir-contract=", "old-contract="])
    except getopt.GetoptError:
        usage()

    # get arguments
    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("--blank-contract"):
            get_args._blank_contract = arg
            # print('get_args._blank_contract = ' + get_args._blank_contract)
        elif opt in ("--dir-contract"):
            get_args._dir_contract = arg
            # print('get_args._dir_contract = ' + get_args._dir_contract)
        elif opt in ("--old-contract"):
            get_args._old_contract = arg
            # print('get_args._old_contract = ' + get_args._old_contract)

    get_args._new_contract = get_args._dir_contract + '\\..\\' + get_args._blank_contract
    
def main(argv):
    get_args(argv)

    # read old contract
    old_pdf = pdfReaderHelper(open(get_args._old_contract, "rb"))
    dict_old_pdf = old_pdf.get_form_fields_in_list(['/Tx', '/Btn']) # returns a python dictionary

    # clear dictionnary with old booking dates and prices...
    key_to_clear = [
        'Date darrivée',
        'Heure',
        'Date de départ',
        'Heure_2',
        'Nombre de jours',
        'Tarif Journalier',
        'Services soins santé arrivéedépart dimanche',
        'Total du séjour avec services',
        'Acompte de 30  à la réservation',
        'versé le',
        'Le solde de la pension sera versé le jour de larrivée soit'
    ]
    for key in key_to_clear:
        dict_old_pdf.pop(key)

    # for key in dict_old_pdf:
    #     print(key, '   -----   ', dict_old_pdf[key])

    # read new contract
    new_pdf = pdfReaderHelper(open(get_args._new_contract, "rb"))

    # write new contract at correct place
    output = pdfWriterHelper()

    # Add all pages
    for p in new_pdf.pages:
        output.add_page(p)

    # update fields
    output.update_page_form_field_values(output.pages[0], dict_old_pdf)
    output.update_page_form_field_values(output.pages[1], dict_old_pdf)
    basename = os.path.basename(get_args._old_contract)
    new_filename = re.sub('[0-9]+ - [0-9]+', 'nouveau', basename)
    if new_filename == basename:
        new_filename = 'nouveau - ' + get_args._blank_contract
    new_filename = get_args._dir_contract + '/' + new_filename

    if os.path.exists(new_filename):
        raise Exception('ERREUR: le contrat ' + new_filename + ' existe déjà')
    outputStream = open(new_filename, "wb")
    output.write(outputStream)
    outputStream.close()
    print('Le contrat ' + new_filename + ' a été crée')


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
        print('')
        print('******************************')
        print('******** CONTRAT CREE ********')
        print('******************************')
        print('')
        input('Appuyer sur "Entrée" pour terminer')
    except Exception as e:
        print(e)
        print('')
        print('*********************************')
        print('******** ERREUR DETECTEE ********')
        print('*********************************')
        print('')
        input('Appuyer sur "Entrée" pour terminer')
