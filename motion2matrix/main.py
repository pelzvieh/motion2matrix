import configparser
import re
import sys
from pathlib import Path

from matrix_client import errors
from matrix_client.client import MatrixClient
from matrix_client.room import Room

_config_directories = ("/etc/motion", Path.home(), Path.cwd())
_config_filename = "matrix.conf"
_config_string_section = "matrix"
_config_string_username = "username"
_config_string_password = "password"
_config_string_url = "url"
_config_strings = (_config_string_username, _config_string_password, _config_string_url)

_config_values = {}


def _read_config() -> str:
    """

    :return: Error (if there's anything wrong with the configfile or NONE if everyhing is alright)
    :rtype: String
    """

    # Try to find a config file

    for path in _config_directories:
        configfile = (Path(path) / _config_filename).resolve()
        if configfile.is_file():
            break
    else:
        # looped, no configfile found
        configfile = None

    if not configfile:
        return "Unable to find configfile"

    _parser = configparser.ConfigParser()
    _parser.read(configfile)
    try:
        for value in _config_strings:
            _config_values[value] = _parser[_config_string_section][value]
            if _config_values[value] is None or len(_config_values[value]) == 0:
                return "Empty value for " + value
    except KeyError as key_error:
        missing_key = key_error.args[0]
        return missing_key + " not set!"


def _send_message(client: MatrixClient, the_room: Room, picture_filename: str, motion_message: str):
    """

    :param the_room: The room the message is being send to
    :type the_room: Room
    :param picture_filename: name of file containing a picture of the detected motion
    :type picture_filename: str
    :param motion_message: A message describing the type of event from motion
    :type motion_message: str
    :return:
    :rtype:

    Sends a motion notification including a picture to the room
    """

    with open(picture_filename, "rb") as picture_file:
        picture = picture_file.read()
    picture_url = client.upload(picture, "image/jpeg")

    the_room.send_image(picture_url, picture_filename)
    the_room.send_text(motion_message)


def motion2matrixmain():
    if len(sys.argv) != 4:
        print("Usage: {} <room(s)> <file path> <message>".format(sys.argv[0]))
        exit(1)

    the_rooms = re.split("[, ;]+", sys.argv[1].strip())
    the_picture_filename = sys.argv[2]
    the_message = sys.argv[3]

    error = _read_config()

    if error:
        print(error)
        exit(1)

    client = None
    try:
        client = MatrixClient(_config_values[_config_string_url])
        token = client.login(username=_config_values[_config_string_username],
                             password=_config_values[_config_string_password])

        for room_id in the_rooms:
            the_room = client.join_room(room_id)
            _send_message(client, the_room, the_picture_filename, the_message)

        client.logout()
        exit(0)
    except errors.MatrixRequestError as me:
        print(me.content)
        exit(1)


if __name__ == '__main__':
    motion2matrixmain()
