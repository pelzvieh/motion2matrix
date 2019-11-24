# motion2matrix
Cloned from zabbix2matrix (https://github.com/mnowiasz/zabbixmatrix), a small python script s
uitable as on_event_start/on_picture_save scripts
from the room surveillance package named motion (https://github.com/Motion-Project/motion).
The script is going to post a picture on each motion event.

To use it you have to do perform the following steps:

1. Register a new matrix account (or use an existing one). You can even
do this by curl (https://www.matrix.org/docs/guides/client-server-api)
2. Invite the account to the channels (public/private, whatever) where
you'd like to receive the motion notifications
3. Enter your credentials (including the URL to the homserver where you've
registered the matrix account) in a file named matrix.conf (see matrix.conf.example).
This file should go to the motion config directory (/etc/motion/)
4. Check the repo out as user motion and install motion2matrix by pip:
`pip install --user .` 
5. Configure motion to use the script: `/var/lib/motion/.local/bin/motion2matrix` 
(YMMV on your installation)
6. The scripts expects parameters ... (to be documented)
7. `Send to` is the ID (or alias) 
of the matrix channel(s) where you want to receive alerts. You can add more than one, seperated
by whitespaces or colons. However, you *have* to make sure that the created matrix user is able to
join the channel (by inviting it first). 

Have fun :-)

