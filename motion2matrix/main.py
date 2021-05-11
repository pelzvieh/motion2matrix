import configparser
import logging
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Union

import aiofiles
import aiofiles.os
import asyncio
import magic
from nio import (
    AsyncClientConfig,
    AsyncClient, UploadError, UploadResponse, Response, ErrorResponse, JoinError, LoginError, JoinResponse)

_config_directories = ("/etc/motion", Path.home(), Path.cwd())
_config_filename = "matrix.conf"
_config_string_section = "matrix"
_config_string_username = "username"
_config_string_password = "password"
_config_string_url = "url"
_config_strings = (_config_string_username, _config_string_password, _config_string_url)

_config_values = {}

DataT = Union[bytes, Iterable[bytes]]

logger = logging.getLogger("motion2matrix")


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


async def _send_message(client: AsyncClient, room_id: str, picture_filename: str, motion_message: str,
                        motion_link: str):
    """

    :param room_id: The ID of the room the message is being send to
    :type room_id: str
    :param picture_filename: name of file containing a picture of the detected motion
    :type picture_filename: str
    :param motion_message: A message describing the type of event from motion
    :type motion_message: str
    :return:
    :rtype:

    Sends a motion notification including a picture to the room
    """

    # 'application/pdf' "image/jpeg"
    mime_type = magic.from_file(picture_filename, mime=True)
    if not mime_type.startswith("image/"):
        logger.debug(
            f"Image file {picture_filename} does not have an image mime type. "
            "Should be something like image/jpeg. "
            f"Found mime type {mime_type}. "
            "This image is being dropped and NOT sent."
        )
        return
    async with aiofiles.open(picture_filename, "r+b") as f:
        resp, decryption_keys = await client.upload(
            data_provider=f,
            content_type=mime_type,
            filename=os.path.basename(picture_filename),
            encrypt=True,
        )

    if isinstance(resp, UploadError):
        logger.warning(f"Upload failed with {resp}")
        return

    if isinstance(resp, UploadResponse):
        logger.debug(f"Result of upload is {resp}")

    content = {
        "body": picture_filename,  # descriptive title
        "msgtype": "m.image",
        "file": {
            "url": resp.content_uri,
            "key": decryption_keys["key"],
            "iv": decryption_keys["iv"],
            "hashes": decryption_keys["hashes"],
            "v": decryption_keys["v"],
        },
    }

    resp = await client.room_send(
        room_id=room_id, message_type="m.room.message", content=content
    )
    if isinstance(resp, ErrorResponse):
        logger.warning(f"Message to {room_id} failed with {resp}")

    content_html = {
        "body": f"{motion_message} Mehr...",
        "msgtype": "m.text",
        "format": "org.matrix.custom.html",
        "formatted_body": f"<p>{motion_message}</p><p><small><a href=\"{motion_link}\">Mehr...</a></small></p>",

    }

    resp = await client.room_send(
        room_id=room_id, message_type="m.room.message", content=content_html
    )
    if isinstance(resp, ErrorResponse):
        logger.warning(f"Message to {room_id} failed with {resp}")


async def _parseandpost():
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        logger.error("Usage: {} <room(s)> <file path> <message> [<additional url>]".format(sys.argv[0]))
        return

    the_rooms = re.split("[, ;]+", sys.argv[1].strip())
    the_picture_filename = sys.argv[2]
    the_message = sys.argv[3]
    if len(sys.argv) == 5:
        the_additional_link = sys.argv[4]
    else:
        the_additional_link = None

    error = _read_config()

    if error:
        logger.error(f"Error reading config: {error}")
        return

    client = None
    try:
        # Configuration options for the AsyncClient
        client_config = AsyncClientConfig(
            max_limit_exceeded=0,
            max_timeouts=0,
            store_sync_tokens=True,
            encryption_enabled=False,
        )
        client = AsyncClient(homeserver=_config_values[_config_string_url],
                             user=_config_values[_config_string_username],
                             config=client_config,
                             ssl=True
                             )
        resp = await client.login(password=_config_values[_config_string_password])
        if isinstance(resp, LoginError):
            logger.error(f"Could not login: {resp}")
            return
        await client.sync(30000, True)
        for room_id in the_rooms:
            resp = await client.join(room_id=room_id)
            if isinstance(resp, JoinError):
                logger.warning(f"Failed to join {room_id}: {resp}")
                continue
            if isinstance(resp, JoinResponse):
                internal_room_id = resp.room_id
                await _send_message(client, internal_room_id, the_picture_filename, the_message, the_additional_link)

        await client.sync(3000, True)
        await client.logout()
        return
    finally:
        await client.close()


def motion2matrixmain():
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", '', sys.argv[0])
    asyncio.get_event_loop().run_until_complete(_parseandpost())


if __name__ == '__main__':
    motion2matrixmain()
