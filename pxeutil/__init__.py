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

__author__ = 'Nilson Lopes <noslin005@gmail.com>'

HOME_DIR = os.environ.get('HOME')
CONFIG_DIR = os.path.join(HOME_DIR, ".local/share/pxeutil")
MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
# TFTP_DIR = '/netshare/tftp'
TFTP_DIR = '/tmp'
BOOT_IMAGES_DIR = f"{TFTP_DIR}/images"
UEFI_PXE_DIR = f"{TFTP_DIR}/uefi"
BIOS_PXE_DIR = f"{TFTP_DIR}/bios"

TEMPLATE_DIR = '%s/templates' % MODULE_DIR
PXEIMAGES_DBFILE = '%s/pxeimages.yaml' % CONFIG_DIR

SUPPORTED_OS = ('redhat', 'fedora', 'ubuntu', 'rocky', 'almalinux', 'centos',
                'debian', 'grml', 'oraclelinux')


def ensure_config_dir_exists():
    try:
        path = pathlib.Path(CONFIG_DIR)
        path.mkdir(parents=True, exist_ok=True)
    except IOError as err:
        print(err)


def load_config():
    filename = PXEIMAGES_DBFILE
    try:
        with open(filename) as f:
            return yaml.load(f, Loader=SafeLoader) or {}
    except FileNotFoundError:
        print('%s not found. Creating New empty file' % PXEIMAGES_DBFILE)
        try:
            with open(filename, 'w') as f:
                f.write('')
        except IOError:
            print('Error while creating config file %s' % PXEIMAGES_DBFILE)
        return {}


def save_config(data: dict):
    filename = PXEIMAGES_DBFILE
    try:
        with open(filename, 'w') as f:
            yaml.dump(data, f, sort_keys=True, indent=4, encoding='utf-8')
    except IOError as err:
        print("Error while saving %s: \nError: %s" % (filename, str(err)))
        return False


def load_template(template_name):
    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
        t = env.get_template(template_name)
        return t
    except TemplateNotFound:
        print('Error: could not find template %s' % template_name)
        return


def format_mac(mac_addr: str):
    try:
        return str(EUI(mac_addr)).lower()
    except AddrFormatError:
        return


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


def create_pxe_image(os_name: str, version: str, kernel: str, initrd: str,
                     variant: str):
    ''' saves a pxe images'''

    image = {
        'os_name': os_name,
        'version': version,
        'kernel': kernel,
        'initrd': initrd
    }

    # read existing value
    data = load_config()

    # If we have an existing image, update it
    try:
        for img in data.get('pxeimages', []):
            if img.get('os_name') == os_name:
                img.update(image)
        if image not in data.get('pxeimages', []):
            data['pxeimages'].append(image)
    except KeyError:
        # handle when a new file is created from scratch
        data['pxeimages'] = []
        data['pxeimages'].append(image)

    # print(data)
    save_config(data=data)
    return data


def create_boot_menu(menu_name: str,
                     image_name: str,
                     boot_args: str = '',
                     comment: str = ''):
    ''' creates a boot menu using existing pxeimages
    '''
    # create menu from pxeimage
    menu = {
        'menu_name': menu_name,
        'image': image_name,
        'boot_args': boot_args,
        'comment': comment
    }

    boot_data = load_config()

    try:

        for img in boot_data.get('bootmenus', []):
            if img.get('menu_name') == menu_name:
                img.update(menu)

        if menu not in boot_data['bootmenus']:
            boot_data['bootmenus'].append(menu)
    except KeyError:
        boot_data['bootmenus'] = []
        boot_data['bootmenus'].append(menu)

    save_config(data=boot_data)
    return menu


def create_boot_file(menu_name, mac_addr: str, boot_mode: str = 'uefi'):
    assert boot_mode in ('uefi', 'legacy', 'ipxe')

    if boot_mode == 'uefi':
        template = 'grub.j2'
        filename = '/tmp/grub.cfg-01-%s' % mac_addr
    elif boot_mode == 'legacy':
        template = 'pxelinux.j2'
        filename = '/tmp/01-%s' % mac_addr
    elif boot_mode == 'ipxe':
        template = 'ipxe.j2'
        filename = '/tmp/mac-%s.ipxe' % mac_addr

    data = load_config()

    menu = next(
        (m for m in data['bootmenus'] if m.get('menu_name') == menu_name),
        None)

    if not menu:
        print('Menu %s does not exists' % menu_name)
        return

    image = next(
        (img for img in data['pxeimages'] if img['os_name'] == menu['image']),
        None)

    if not image:
        print('Can not find a pxe image for menu %s' % menu_name)
        return

    menu.update(image)
    variant = menu.get('variant')

    tftp_path = 'images/{}/{}/%s' % (variant) if variant else 'images/{}/{}'

    tftp_path = tftp_path.format(menu.get('os_name'), menu.get('version'))

    menu.update({'tftp_dir': tftp_path})

    print(menu)

    try:
        t = load_template(template)
        boot_file = t.render(menu)
        with open(filename, 'w') as f:
            f.write(boot_file)
    except Exception as err:
        print('%s' % err)
        return False


def import_pxe_files(kernel: str,
                     initrd: str,
                     os_name: str,
                     os_version: str,
                     variant: str = ''):

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

    create_pxe_image(os_name=os_name,
                     version=os_version,
                     kernel=kernel_name,
                     initrd=initrd_name,
                     variant=variant)


def menu():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='command')

    # import new pxe image
    import_menu = subparser.add_parser('import')
    import_menu.add_argument('-n',
                             '--os_name',
                             metavar='os_name',
                             required=True,
                             type=str,
                             choices=SUPPORTED_OS,
                             help='OS Distribuition Name')
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
                             dest='variant',
                             type=str,
                             choices=('server', 'workstation', 'desktop', ''),
                             help='OS Variant, ie. server')

    # create menus
    create_menu = subparser.add_parser('create')
    create_menu.add_argument('-n',
                             '--name',
                             metavar='menuname',
                             dest='menuname',
                             required=True,
                             help='Boot menu name')
    create_menu.add_argument('-i',
                             '--image',
                             metavar='image',
                             dest='image',
                             required=True,
                             help='Image ID')
    create_menu.add_argument('-a',
                             '--boot-args',
                             metavar='boot_args',
                             dest='boot_args',
                             required=True,
                             help='Boot arguments')

    # assign menu to hosts
    assign_menu = subparser.add_parser('assign')
    assign_menu.add_argument('-m',
                             '--mac',
                             metavar='mac',
                             type=format_mac,
                             required=True,
                             help='host MAC Address')
    assign_menu.add_argument('-n',
                             '--menu',
                             metavar='menu',
                             required=True,
                             help='PXE Menu to assign')
    assign_menu.add_argument('-b',
                             '--boot-mode',
                             metavar='bootmode',
                             dest='bootmode',
                             choices=('uefi', 'legacy', 'ipxe'),
                             default='uefi',
                             help='PXE Menu to assign')

    return parser.parse_args()


def main():
    args = menu()

    if args.command == 'import':
        ensure_config_dir_exists()
        import_pxe_files(os_name=args.name,
                         os_version=args.version,
                         kernel=args.kernel,
                         initrd=args.initrd,
                         variant=args.variant)

    elif args.command == 'create':
        create_boot_menu(menu_name=args.menuname,
                         image_name=args.image,
                         boot_args=args.boot_args)

    elif args.command == 'assign':
        create_boot_file(menu_name=args.menu,
                         mac_addr=args.mac,
                         boot_mode=args.bootmode)
