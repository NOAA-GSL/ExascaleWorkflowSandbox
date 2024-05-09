#! /bin/bash
#=============================
# Some cloud clusters' images
# come set up expecting to use
# modules at attached storage
# /apps. Run this script to 
# destroy this persistent 
# background assumption.
#=============================

sudo rm /etc/profile.d/modules.*
sudo rm /usr/share/Modules/init/profile.sh
sudo rm /usr/share/Modules/init/profile.csh
sudo yum reinstall -y environment-modules

# After these commands, source .bashrc or /etc/profile.d/modules.sh
# or log out and log back in to reload the profile.d scripts.
source ~/.bashrc

echo "You now need to log back in or source ~/.bashrc to setup modules environment!"
