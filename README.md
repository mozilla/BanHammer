BanHammer-ng is a system to push rules to border routers (using BGP) and Zeus Load Balancers to block IPs/network using a web interface.

Installation
============

1. Rename `BanHammer/settings/local.py.orig` to vBanHammer/settings/local.py` and modify it to your needs
2. Rename `BanHammer/blacklist/fixtures/initial_data.json.orig` to `BanHammer/blacklist/fixtures/initial_data`
3. Follow [playdoh installation instructions](http://playdoh.readthedocs.org/en/latest/getting-started/installation.html)

Scoring and notification script (optional)
==========================================

If you have a SIEM, maybe ArcSight, you can have BanHammer suggest you via email which IP you should block.
What you need to do is to run commands like `./manage.py new_event --attackerAddress=\'${attackerAddress}\' --eventId=${eventId} --severity=7 --rulename=\'Marketplace CSP Violation\'`
to feed BanHammer with your data.

The settings for the score and notifications are in the blacklist_config table.