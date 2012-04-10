General
=======

* Everything listening to network is running under [apparmor](https://wiki.ubuntu.com/AppArmor).
* Only mandatory services are running: ssh, apache, redis (localhost only), collectd (localhost only)
* All user provided input is validated against predefined allowed values.

php.ini
=======

```
; restrict all file operations to /var/www
open_basedir = "/var/www"
register_globals = Off
ignore_user_abort = Off
expose_php = Off

; limits
memory_limit = 32M
max_input_nesting_level = 12
max_input_time = 15
max_execution_time = 30

; error reporting
display_errors = Off
display_startup_errors = Off

; file uploads
file_uploads = On
upload_max_filesize = 1M
max_file_uploads = 2

enable_dl = Off
allow_url_fopen = Off
allow_url_include = Off
```

apache2
=======

* [mod_security](http://www.modsecurity.org/)
* libapache2-mod-apparmor and AAHatName directives for static files directories, index.php, json.php, upload.php
* Apache2 apparmor profile allows only specific file access per hat. For example, only upload.php is allowed to write anything. No script is allowed to read anything outside */var/www* and PHP libraries directory.
