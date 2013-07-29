BanHammer-ng
============

BanHammer-ng is a system to push rules to border routers (using BGP) and Zeus Load Balancers to block IPs/network using a web interface.

Installation
------------

1. Rename `BanHammer/blacklist/fixtures/initial_data.json.orig` to `BanHammer/blacklist/fixtures/initial_data`
2. Follow [playdoh installation instructions](http://playdoh.readthedocs.org/en/latest/getting-started/installation.html)

Scoring and notification script (optional)
------------------------------------------

If you have a SIEM, maybe ArcSight, you can have BanHammer suggest you via email which IP you should block.
What you need to do is to run commands like `./manage.py new_event --attackerAddress=\'${attackerAddress}\' --eventId=${eventId} --severity=7 --rulename=\'Marketplace CSP Violation\'`
to feed BanHammer with your data.
To use this feature, you need to load the external rules provided by Emerging Threats and Dshield `./manage.py update_third_party_rules`

The settings for the score and notifications are in the blacklist_config table.

Run the tests
-------------

`$ python manage.py test BanHammer/blacklist/tests/*.py`

License
-------
This software is licensed under the [New BSD License][BSD]. For more
information, read the file ``LICENSE``.

[BSD]: http://creativecommons.org/licenses/BSD/
