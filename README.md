# Uberserk - Lichess boards API client for MicroPython

Uberserk is a light version of berserk ported to MicroPython with enough functionality
to support play on custom chess boards.

This project is [rhgrant10/berserk](https://github.com/rhgrant10/berserk/) with modifications that allow it to run on MicroPython. Developed and tested using ESP32.

Some changes to MicroPython packages were needed as well so uberserk comes with its own datetime.py and urequests.py.

### MCU requirements
Uberserk requires a decently sized RAM, ESP32-WROOM do not cut it and ESP32-WROVER with SPI RAM are required.


### Changes to datetime.py
- line 1360:   `t, frac = divmod(t, 1)`
    -  1.0 -> 1 to prevent TypeError: can't convert float to int on line 1372
- line 1371 replace with try block as per https://github.com/smlng/pycayennelpp/issues/53
```
try:
    y, m, d, hh, mm, ss, weekday, jday, dst = converter(t)
except ValueError:
    y, m, d, hh, mm, ss, weekday, jday = converter(t)
```

- line 917 add `__new__` to tzinfo as per https://github.com/micropython/micropython-lib/pull/338:
```
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
```


Check datetime compatibility (reference for developers; the lib must be moved out of uberserk namespace first or imports below changed). No errors must be seen:
```
>>> ts=1612971162
>>> from datetime import datetime, timezone
>>> datetime.fromtimestamp(ts, timezone.utc)
```

### Changes to urequests.py
- implement iterator protocol for Response

### Changes to Berserk to port it to MicroPython
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
- Challenges

#### The following functionality of berserk is dropped:
- most of Account
- most of Games
- Bots
- Tournaments
- Broadcasts
- Simuls
- Studies

## Installation

Assuming you have MicroPython installed on your MCU and have it connected via a serial line over USB with device name /dev/tty.usbserial-0001:

First get to MicroPython REPL to create a directory for uberserk:
```
screen /dev/tty.usbserial-0001 115200
>>> import uos
>>> uos.mkdir('lib')
>>> uos.mkdir('lib/uberserk')
```
Then exit back to shell, free the serial device (killall screen, replace as needed) and copy over the files:
```
killall screen
git clone https://github.com/mkomon/uberserk.git
cd uberserk
rshell -p /dev/tty.usbserial-0001 cp uberserk/*.py /pyboard/lib/uberserk
```

## Usage
```
>>> import uberserk
>>> 
>>> AUTH_TOKEN = 'get-one-online'
>>> client = uberserk.Client(AUTH_TOKEN)
>>> account_info = client.account.get()

>>> account_info.keys()
dict_keys(['nbFollowers', 'completionRate', 'perfs', 'url', 'followable', 'language', 'count', 'patron', 'playing', 'id', 'following', 'username', 'online', 'nbFollowing', 'blocking', 'followsYou', 'playTime', 'createdAt', 'seenAt'])

>>> game_id = 'abcd123'
>>> stream = client.board.stream_game_state(game_id)
>>> for event in stream:
    ...
```

### Differences from Berserk
Uberserk behaves like Berserk, API responses are handled and formatted just like in Berserk. It may feel slower because it cannot use connection pooling for different requests and each API call opens a HTTPS connection. Streaming API is where uberserk differs notably: while generators that read from streaming APIs in Berserk are blocking in uberserk they do not block. This avoids the need to use threads and allows the generators be called from the main loop or any other loop.

#### Streaming API usage
```
for event in client.board.stream_game_state(game_id)
    if not event:
        # no new events for now
        utime.sleep_ms(500)
        continue
    # process event
    ...
```

After the condition (no new events) you can wait and `continue` to simulate blocking behavior of the generator, like in Berserk, or you can `break` and do other things before some event arrives and you run the loop again to check.

### Credits

- [Robert Grant](https://github.com/rhgrant10) for the original Berserk client [rhgrant10/berserk](https://github.com/rhgrant10/berserk/tree/master/berserk)
- CPython Developers for [datetime](https://github.com/micropython/micropython-lib/blob/master/datetime/datetime.py) package of [micropython-lib](https://github.com/micropython/micropython-lib/)
- Paul Sokolovsky for [urequests](https://github.com/micropython/micropython-lib/blob/master/urequests/urequests.py) package of [micropython-lib](https://github.com/micropython/micropython-lib/)
