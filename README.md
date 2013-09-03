BanHammer-ng
============

BanHammer-ng is a system to push rules to border routers (using BGP) and Zeus Load Balancers to block IPs/network using a web interface.


@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@8C8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@CCCOO:cCOCoO@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@CoCCCc:ooooOOCCO88OC8@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@C:cooc:cc:cCOOOCOCCoCCCCO@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@O:c::::ccccoCOOOOOOOOOOOCOCoOC@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@8Ococ::::cccccCCCOOOOOOOOOOOOOCOCOOo@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@88cooc:::cccc:oCCCCOOOOOOOOOOOOOOOCoCOOoC@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@cocc:.:c:cccoCCCCCOOOOOOOOOOOOOOOCoCooOOOO@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@Ccc:c::c:ccooCCCCCOOOOOOOOOOOOOOOOOOCocoCOOO@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@cco::ccccoccooCCCCCCCOOOOOOOOOOOOOOOOCCooCC8@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@:::c:ccocooooccoCCCCCCCOOOOOOOOCCOOOOOOCCooo8@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@oO8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@::cc::oooooooooCCCCCCCCOOCCCCCCOOOOOOOOCCoCO8@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@O8888OOCO8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@8cccccooCooooooooCCCCCCoCCCCCOOOOOOOOCCOOCoO@8@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@C8O88:CO8OOOO8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@8@@@@@@@@@@@@@ccccoCCoooooooooCCooooooCCCOOOOOOOOOCCOCocO@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@C8888oooocc:cO8OOOCO@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@OCOO8CCCC@@@@@@@@@@@c:cccooocccccooooooooooooCCOCCOOOOOOOooCoo@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@O8@@@8:CCoCoCCoc:cCCCccooO@@@@@@@@@@@@@@@@@@@@@@@@@@@8cCOOOOOOo8ooCC@@@@@@@8oCCoccc:ccocccccccccoooooooooCOCCCCCcccc:c@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@COO88@:8CocooCoCCoCcCCoCoCCooCO@@@@@@@@@@@@@@@@@@@@CoCCCooCCCCOo8OCCCCC8@@@@@C:oooccc::cocccccccccccccooooooCCCc:cc:COCO@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@cOOOO8cccoCCCCooooCCOCoOCOOOCCCCCCoo8CCOo8@@@@@@8cCCCoooooCCCCOOccoCOCooooC@@8ocC::cc.::c:cooocccccccccccocccocc:::oCOO88@@@@@@
@@@@@@@@@@@@@@@@@@@@@OcOOOOO:ccc:..::coCCCCCC:OcCCCO88OOCCo:CCCocCCOOOOCCoooCoCooooc.ccc::::oO8CccOCcOcoco::::..::ccooccccooocccc::::::::ccco8@@@@@@@@
@@@@@@@@@@@@@@@@@@@@o8OCOCo.coooccccco:.:oOCoCcooCCCoCoCCoocCCo:8OOOOoCCCOCCooc:...:......::..oO8@8o:ococccc::ccccc.::cocoooocooc:::cc::cc:o@@@@@@@@@@
@@@@@@@@@@@@@@@@@@oOOCoocc:::::cccccccccc::o:ocoooCooooooooOCC.cOooooCc..:::::::::::::.....::::CCOoc:::ccc:.:C@C@@@@8c:::::cccc:c::c:::c:cO@@@@@@@@@@@
@@@@@@@@@@@@@@@8o8OCoooo.cCOc::cc:.:::c:c:c::ccocooooooooo:88O:ccoooccc...:::::::::...... :c::oCoOc@O..:c:cO@@@@@@@@@@@o::::::::::::c::cO8@@@@@@@@@@@@
@@@@@@@@@@@@@@@@oOoc::O:oooooCo::ccc:::coo..:::ccccooococccCo:.ccccccc........::......... :c:.CCCoOCCCOoc8@@@@@@@@@@@@@@@oc::::::cccccC8@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@o::::o.cc:::::.::::::::::.:.:::::c::cc::coc:.:::::::.............C8OCoo.c::.CoO:oooCooCC@@@@@@@@@@@@@@@@@Oc:co@@@@8@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@:::::::::::::::::::::::.:.......::::..:o....:.::..............::.cCoooc...:8c..:ooooC8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@O::::::::cc:........c:::............ .::.:..............coooo.:::..:oooooc:...::.:c8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@8:::::c...:::::.:::c::::........... ....:...............CoCCCo..::..:ooooooocc:coCO@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@:::..c::.::::::cc::::::......:.........occc:............ooCoCc..::..:oooCCo:@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@::..:::ccccccccccc::.:..:::::::......c::cccc.....:......:cCoCC:..:::.cCoCCo@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@c...:.::::.......::.::.:::::::::::.....::cc...c:ooc:...:.:oCoCo..:::..c@C8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@:.........::::::.::.:.:::::...o8O@Cc::::::.:.....coo:..:..CooCcoC:.:oCO8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@:......::::::::.::..:c:.:C@@@@@@@@@@COOO8O:o:.::..oCo:....:8Oc@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@o....::::::::.::::oO@@@@@@@@@@@@@@@@@@@OoCCooo:::..:Coc:..:::o@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@C....::::::::oO@@@@@@@@@@@@@@@@@@@CO8ocCococooc...::.cOo@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@c:...::cO@@@@@@@@@@@@@@@@@@@@@@@@@@oCooc::ccccc:o::::.c@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@c:coC8@@@@@@@@@@@@@@@@@@@@@@@8O@8COCo:ooc:.::cc@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@OOOO:OCcc:::::c::o@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@Ocoo::::coo:cooo@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@COOocc:...:co:O@@88@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@Cococc::cc:cc@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@Cc::::ccoo888@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@Occc::ccoo8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@8@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@OCCooCO@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


Installation
------------

1. Rename `BanHammer/blacklist/fixtures/initial_data.json.orig` to `BanHammer/blacklist/fixtures/initial_data`
2. Follow [playdoh installation instructions](http://playdoh.readthedocs.org/en/latest/getting-started/installation.html)
3. Run celeryd `python manage.py celeryd`

Scoring and notification script (optional)
------------------------------------------

If you have a SIEM, maybe ArcSight, you can have BanHammer suggest you via email which IP you should block.
What you need to do is to run commands like `./manage.py new_event --attackerAddress=\'${attackerAddress}\' --eventId=${eventId} --severity=7 --rulename=\'Marketplace CSP Violation\'`
to feed BanHammer with your data.
To use this feature, you need to load the external rules provided by Emerging Threats and Dshield `./manage.py update_third_party_rules`

The settings for the score and notifications are in the blacklist_config table.

Maintenance tasks
-----------------

* Update third party rules for scoring: `$ python manage.py update_third_party_rules`
* Clean expired blacklists from ZLBs: `$ python manage clean_blacklists`
* Update data from ZLBs: `$ python manage update_zlbs`
* Decrease score of offenders as time passes (e.g. set up a cron task to execute every hour) `$ python manage decrease_scores`

Run the tests
-------------

`$ python manage.py test BanHammer/blacklist/tests/tests_*.py`

License
-------
This software is licensed under the [New BSD License][BSD]. For more
information, read the file ``LICENSE``.

[BSD]: http://creativecommons.org/licenses/BSD/
