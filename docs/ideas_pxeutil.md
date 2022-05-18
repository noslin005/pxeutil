# Ideas for `pxeutil` cli

### Importing Kernel and Initrd

```bash
pxeutil import --name centos --version 7 --kernel /mnt/images/pxeboot/vmlinuz \
  --initrd /mnt/images/pxeboot/initrd.img

# Import the kernel and initrd,
# creates a nfs share and copy the content of the iso to this share
pxeutil import --name grml --version 2022.05.06 \
  --kernel /mnt/images/pxeboot/vmlinuz \
  --initrd /mnt/images/pxeboot/initrd.img \
  --copy /mnt
```

### Add PXE Template
```bash
pxeutil create --uefi  --image centos --tag 'CentOS_7_nvme0' \
  --args "inst.repo=http://10.12.17.6/os/centos/7/ inst.ks=http://10.12.17.6/os/centos/ks/centos-nvme.ks ip=dhcp"

pxeutil create --uefi --image centos --tag 'CentOS_7_sda' \
  --args "inst.repo=http://10.12.17.6/os/centos/7/ inst.ks=http://10.12.17.6/os/centos/ks/centos-sda.ks ip=dhcp"
```

### Assign PXE Image to Host
```bash
pxeutil assign --host '3CECEFF329BE' --image 'CentOS_7_nvme0'
```

### Deassign an image from a host 

```bash
pxeutil remove --host '3CECEFF329BE'
```