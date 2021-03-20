# Uberserk - Lichess boards API client for MicroPython

Uberserk is a light version of berserk ported for MicroPython with enough functionality
to support play on custom chess boards.

This project is [rhgrant10/berserk](https://github.com/rhgrant10/berserk/tree/master/berserk) with modifications that allow it to run on MicroPython. Developed and tested using ESP32.

Some changes to MicroPython packages were needed as well so uberserk comes with its own datetime.py and (my)urequests.py.

### MCU requirements
Uberserk requires a decently sized RAM, ESP32-WROOM do not cut it and ESP32-WROVER with SPI RAM are required.

### Changes to datetime.py
- line 1360:   `t, frac = divmod(t, 1)`
    -  1.0 -> 1 to prevent TypeError: can't convert float to int on line 1372
- line 1371:
```try:  # fix per https://github.com/smlng/pycayennelpp/issues/53
            y, m, d, hh, mm, ss, weekday, jday, dst = converter(t)
        except ValueError:
            y, m, d, hh, mm, ss, weekday, jday = converter(t)
```

Check datetime compatibility. No errors must be seen:
```
>>> ts=1612971162
>>> from datetime import datetime
>>> from datetime import timezone
>>> datetime.fromtimestamp(ts, timezone.utc)
```

### Changes to urequests.py
- line 29: add `self.raw.setblocking(False)`
    - REST APIs work without it but streaming APIs would block

### Changes to Berserk to port to MicroPython
- replace all formatted strings with .format() or %-based string formatting
- remove dependency on json.JSONDecoder, ndjson
- remove dependency on requests.Session
- remove dependency on deprecated
- do without the params argument on requests.request
- bring in code of raise_for_status() (from https://github.com/psf/requests/blob/master/requests/models.py) and avoid using HTTPError()

#### The following functionality of berserk is kept:
- basic of Account
  - only get(), get_preferences()
- Board
- basic of Games
  - only get_ongoing()
- Users
- Teams

#### The following functionality of berserk is dropped:
- most of Account
- most of Games
- Bots
- Challenges
- Tournaments
- Broadcasts
- Simuls
- Studies

### Installation

Assuming you have MicroPython installed on your MCU and have it connected via a serial line over USB with device name /dev/tty.usbserial-0001:

First get to MicroPython REPL to create a directory for uberserk:
```
screen /dev/tty.usbserial-0001 115200
>>> import uos
>>> uos.mkdir('lib/uberserk')
>>> ^a d
```
Then exit back to shell, free the serial device (killall screen, replace as needed) and copy over the files:
```
killall screen
git clone ...
cd uberserk
rshell -p /dev/tty.usbserial-0001 cp datetime.py myrequests.py /pyboard/lib
rshell -p /dev/tty.usbserial-0001 cp uberserk/*.py /pyboard/lib/uberserk
```

### Usage
```
>>> import uberserk
>>> 
>>> OAUTH_TOKEN = 'get-one-online'
>>> client = uberserk.Client(OAUTH_TOKEN)
>>> account_info = client.account.get()

>>> account_info.keys()
dict_keys(['nbFollowers', 'completionRate', 'perfs', 'url', 'followable', 'language', 'count', 'patron', 'playing', 'id', 'following', 'username', 'online', 'nbFollowing', 'blocking', 'followsYou', 'playTime', 'createdAt', 'seenAt'])

>>> game_id = 'abcd123'
>>> stream = client.board.stream_game_state(game_id)
>>> for event in stream:
    ...
```


### Credits

- [rhgrant10/berserk](https://github.com/rhgrant10/berserk/tree/master/berserk) for the original Berserk client


