from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from BanHammer.blacklist.views import blacklist as views_blacklist
from BanHammer.blacklist.views import offender as views_offender

from funfactory.monkeypatches import patch
patch()

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views_blacklist.index, name='blacklist_index'),
    url(r'^blacklist/$', views_blacklist.index, name='blacklist_index'),
    url(r'^blacklist/show_expired$', views_blacklist.index, {'show_expired': True}, name='blacklist_index'),
    url(r'^blacklist/post/$',views_blacklist.post, name='blacklist_post'),
    url(r'^blacklist/delete/$', views_blacklist.delete, name='blacklist_delete'),
    url(r'^offenders$', views_offender.list, name='offender_index'),
    url(r'^offender/(\d+)$', views_offender.show, name='offender_show'),
    url(r'^offender/(\d+)/edit$',views_offender.edit, name='offender_edit'),
    url(r'^offender/new$',views_offender.create, name='offender_new'),
    url(r'^offender/delete$', views_offender.delete, name='offender_delete'),
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
