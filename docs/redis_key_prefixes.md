Cache
-----

* Prefix: cache:
* Durability: should have expiration time set. 
* Might disappear at any time.

data files
----------

* Prefix: data:X, data:X-mtime, data:X-hash (all three are mandatory)
* data:X-mtime: unix timestamp
* Should have expiration time set for each key

pubsub
------

* Prefix: pubsub:
* For datafiles, pubsub:data:filename.json
* Data files notifications: {"hash": hash, "mtime": <unix timestamp>}

php session
-----------

* Prefix: phpsession:
* With SSE default PHP session handling doesn't work (SSE script blocks all other session_start requests).
* Default redis timeout is very high (86400 seconds).

```
    session.save_handler = redis
    session.save_path = "tcp://localhost:6379?prefix=phpsession:&timeout=2"

```

statistics
----------

* Prefix: stats:
* Public via "Server stats page" - it's not recommended to add anything private, or anything that adds huge number of keys to this prefix.

Per user stats
--------------

* Prefix: stats:ip:<ip> - per IP statistics - these are only visible to visitors from specific IP address
* Prefix: stats:session:<php session key> - per session statistics - these are only visible to visitors with specific session key
* Should have expiration time, for example 3 months, refreshed on every update.
