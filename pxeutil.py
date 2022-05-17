#!/usr/bin/env python3

import argparse
import os
import pathlib
import shutil

import jinja2
import yaml
from jinja2.exceptions import TemplateNotFound
from netaddr import EUI
from netaddr.core import AddrFormatError
from yaml.loader import SafeLoader

# TFTP_DIR = '/netshare/tftp'
TFTP_DIR = '/tmp'
BOOT_IMAGES_DIR = f"{TFTP_DIR}/images"
UEFI_PXE_DIR = f"{TFTP_DIR}/uefi"
BIOS_PXE_DIR = f"{TFTP_DIR}/uefi"

TEMPLATE_DIR = 'templates'
PXEIMAGES_DBFILE = 'db/pxeimages.yaml'
BOOTMENU_DBFILE = 'db/bootmenus.yaml'


def load_config(filename: str):
    try:
        with open(filename) as f:
            return yaml.load(f, Loader=SafeLoader) or {}
    except FileNotFoundError:
        return {}


def save_config(filename: str, data: dict):
    try:
        with open(filename, 'w') as f:
            yaml.dump(data, f, sort_keys=True, indent=4, encoding='utf-8')
    except IOError as err:
        print("Error while saving %s: \nError: %s" % (filename, str(err)))
        return False


def copy_file(source, destination):
    if not os.path.isfile(source):
        return

    dest = pathlib.Path(destination)
    if not dest.exists():
        dest.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy(source, dest.as_posix())
    except IOError as err:
        print('Error while copying %s to %s' % (source, dest.as_posix()))
        print(err)


def create_pxe_image(name, version, kernel, initrd):
    ''' saves a pxe images
    '''
    tftp_path = 'image/{}/{}/{}'

    image_id = "%s%s" % (name, version)
    image = {
        'name': name,
        'version': version,
        'id': image_id,
        'kernel': tftp_path.format(name, version, kernel),
        'initrd': tftp_path.format(name, version, initrd)
    }

    # read existing value
    data = load_config(PXEIMAGES_DBFILE)

    # If we have an existing image, update it
    try:
        for img in data.get('pxeimages', []):
            if img.get('id') == image_id:
                img.update(image)
        if image not in data.get('pxeimages', []):
            data['pxeimages'].append(image)
    except KeyError:
        # handle when a new file is created from scratch
        data['pxeimages'] = []
        data['pxeimages'].append(image)

    # print(data)
    save_config(filename=PXEIMAGES_DBFILE, data=data)
    return data


def create_boot_menu(menu_name: str,
                     image_id: str,
                     boot_args: str = '',
                     comment: str = ''):
    ''' creates a boot menu using existing pxeimages
    '''

    pxedata = load_config(PXEIMAGES_DBFILE)
    pxeimage = {}
    try:
        for img in pxedata['pxeimages']:
            if img.get('id') == image_id:
                pxeimage = img
                break
    except KeyError:
        print('create pxeimages first and then create boot menu')
        return {}

    # create menu from pxeimage
    menu = {
        'menu_name': menu_name,
        'kernel': pxeimage.get('kernel'),
        'initrd': pxeimage.get('initrd'),
        'boot_args': boot_args,
        'comment': comment
    }

    boot_data = load_config(PXEIMAGES_DBFILE)

    try:
        for img in boot_data.get('bootmenus', []):
            if img.get('menu_name') == menu_name:
                img.update(menu)

        if menu not in boot_data['bootmenus']:
            boot_data['bootmenus'].append(menu)
    except KeyError:
        boot_data['bootmenus'] = []
        boot_data['bootmenus'].append(menu)

    save_config(PXEIMAGES_DBFILE, data=boot_data)
    return menu


def load_template(template_name):
    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
        t = env.get_template(template_name)
        return t
    except TemplateNotFound:
        print('Error: could not find template %s' % template_name)
        return


def create_boot_file(menu: dict, mac_addr: str, boot_mode: str = 'uefi'):
    assert boot_mode in ('uefi', 'legacy')

    if boot_mode == 'uefi':
        template = 'grub.j2'
        filename = '/tmp/grub.cfg-01-%s' % mac_addr
    elif boot_mode == 'legacy':
        template = 'pxelinux.j2'
        filename = '/tmp/01-%s' % mac_addr

    try:
        t = load_template(template)
        boot_file = t.render(menu)
        with open(filename, 'w') as f:
            f.write(boot_file)
    except Exception as err:
        print('%s' % err)
        return False


def format_mac(mac_addr: str):
    try:
        return str(EUI(mac_addr)).lower()
    except AddrFormatError:
        return


def import_pxe_files(kernel, initrd, os_name, os_version, variant=''):
    assert variant in ('', 'server')

    if variant:
        image_path = os.path.join(BOOT_IMAGES_DIR, os_name, variant,
                                  os_version)
    else:
        image_path = os.path.join(BOOT_IMAGES_DIR, os_name, os_version)

    destination = pathlib.Path(image_path).as_posix()

    # copy kernel and initrd file
    for f in (kernel, initrd):
        copy_file(f, destination=destination)

    kernel_name = pathlib.Path(kernel).name
    initrd_name = pathlib.Path(initrd).name

    create_pxe_image(name=os_name,
                     version=os_version,
                     kernel=kernel_name,
                     initrd=initrd_name)


def menu():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='command')

    # import new pxe image
    import_menu = subparser.add_parser('import')
    import_menu.add_argument('-n',
                             '--name',
                             metavar='name',
                             required=True,
                             type=str,
                             help='OS name')
    import_menu.add_argument('-v',
                             '--version',
                             metavar='version',
                             required=True,
                             help='OS version')
    import_menu.add_argument('-k',
                             '--kernel',
                             metavar='kernel',
                             type=pathlib.Path,
                             required=True,
                             help='Kernel file')
    import_menu.add_argument('-i',
                             '--initrd',
                             metavar='initrd',
                             type=pathlib.Path,
                             required=True,
                             help='initrd file')
    import_menu.add_argument('-t',
                             '--variant',
                             metavar='variant',
                             type=str,
                             default='',
                             help='OS Variant, ie. server')

    # #
    # create_menu = subparser.add_parser('create')
    # assign_menu = subparser.add_parser('assign')

    return parser.parse_args()


if __name__ == '__main__':
    # name = 'rocky'
    # version = '8.6'
    # kernel = 'vmlinuz'
    # initrd = 'initrd.img'
    # boot_args = ('inst.repo=https://download.rockylinux.org'
    #              '/pub/rocky/8/BaseOS/x86_64/os/ ip=dhcp')

    # mac = format_mac('3C:EC:EF:F3:29:BE')

    # create_pxe_image(name=name, version=version,
    # kernel=kernel, initrd=initrd)
    # menu = create_boot_menu(menu_name='rocky8sda',
    #                         image_id='rocky8.6',
    #                         boot_args=boot_args)
    # create_boot_file(menu=menu, mac_addr=mac, boot_mode='uefi')

    args = menu()

    if args.command == 'import':
        import_pxe_files(os_name=args.name,
                         os_version=args.version,
                         kernel=args.kernel,
                         initrd=args.initrd,
                         variant=args.variant)
