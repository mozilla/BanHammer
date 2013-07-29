from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from BanHammer.blacklist.views import blacklist as views_blacklist
from BanHammer.blacklist.views import offender as views_offender
from BanHammer.blacklist.views import setting as views_setting
from BanHammer.blacklist.views import whitelistip as views_whitelistip

from funfactory.monkeypatches import patch
patch()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views_blacklist.index, name='blacklist_index'),
    url(r'^blacklist/$', views_blacklist.index, name='blacklist_index'),
    url(r'^blacklist/show_expired$',
        views_blacklist.index,
        {'show_expired': True},
        name='blacklist_index'),
    url(r'^blacklist/new/bgp_block$',views_blacklist.new_bgp_block, name='blacklist_new_bgp'),
    url(r'^blacklist/new/bgp_block/(\d+)$',views_blacklist.new_bgp_block, name='blacklist_new_bgp'),
    url(r'^blacklist/delete/$', views_blacklist.delete, name='blacklist_delete'),
    url(r'^offenders$', views_offender.index, name='offender_index'),
    url(r'^offenders/show_suggested$',
        views_offender.index,
        {'show_suggested': True},
        name='offender_index'),
    url(r'^offender/(\d+)$', views_offender.show, name='offender_show'),
    url(r'^offender/(\d+)/delete$', views_offender.delete, name='offender_delete'),
    url(r'^offender/(\d+)/edit', views_offender.edit, name='offender_edit'),
    url(r'^settings$', views_setting.list, name='settings_index'),
    url(r'^whitelistip$', views_whitelistip.index, name='whitelistip_index'),
    url(r'^whitelistip/new$', views_whitelistip.new, name='whitelistip_new'),
    url(r'^whitelistip/(\d+)/edit$', views_whitelistip.edit, name='whitelistip_edit'),
    url(r'^whitelistip/(\d+)/delete$', views_whitelistip.delete, name='whitelistip_delete'),

    # Example:
    #(r'', include(urls)),
    
    # Generate a robots.txt
    (r'^robots\.txt$', 
        lambda r: HttpResponse(
            "User-agent: *\n%s: /" % 'Allow' if settings.ENGAGE_ROBOTS else 'Disallow' ,
            mimetype="text/plain"
        )
    )

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)

## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
