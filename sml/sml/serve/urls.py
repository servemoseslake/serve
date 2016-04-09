from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'login$', 'sml.serve.views.login', name='login'),
    url(r'logout$', 'sml.serve.views.logout', name='logout'),

    url(r'appointment/(?P<appointment_id>\d+)$', 'sml.serve.views.appointment', name='appointment'),
    url(r'appointment/(?P<appointment_id>\d+)/start$', 'sml.serve.views.start_appointment', name='start_appointment'),
    url(r'appointment/(?P<appointment_id>\d+)/reset$', 'sml.serve.views.reset_appointment', name='reset_appointment'),
    url(r'appointment/(?P<appointment_id>\d+)/cancel$', 'sml.serve.views.cancel_appointment', name='cancel_appointment'),
    url(r'appointment/new$', 'sml.serve.views.new_appointment', name='new_appointment'),

    url(r'calendar/appointments$', 'sml.serve.views.get_calendar_appointments', name='get_calendar_appointments'),
    url(r'calendar$', 'sml.serve.views.view_calendar', name='view_calendar'),

    url(r'client/search$', 'sml.serve.views.search_clients', name='search_clients'),
    url(r'client/list$', 'sml.serve.views.list_clients', name='list_clients'),
    url(r'client/(?P<client_id>\d+)/save$', 'sml.serve.views.save_client', name='save_client'),
    url(r'client/(?P<client_id>\d+)$', 'sml.serve.views.view_client', name='view_client'),

    url(r'client/comment$', 'sml.serve.views.get_comment', name='get_comment'),
    url(r'client/(?P<client_id>\d+)/intent/(?P<intent_id>\d+)$', 'sml.serve.views.view_intent', name='view_intent'),
    url(r'intent/(?P<intent_id>\d+)/form$', 'sml.serve.views.generate_intent_form', name='generate_intent_form'),

    url(r'client/(?P<client_id>\d+)/phone/(?P<phone_id>\d+)/delete$', 'sml.serve.views.delete_phone', name='delete_phone'),    
    url(r'client/(?P<client_id>\d+)/phone/add$', 'sml.serve.views.add_phone', name='add_phone'),    

    url(r'client/(?P<client_id>\d+)/address/save$', 'sml.serve.views.save_address', name='save_address'),    
    url(r'client/(?P<client_id>\d+)/homeless/save$', 'sml.serve.views.save_homeless', name='save_homeless'),    

    url(r'client/(?P<client_id>\d+)/dependent/add$', 'sml.serve.views.add_dependent', name='add_dependent'),    
    url(r'client/(?P<client_id>\d+)/dependent/(?P<dependent_id>\d+)/delete$', 'sml.serve.views.delete_dependent', name='delete_dependent'),    

    url(r'client/(?P<client_id>\d+)/reference/(?P<reference_id>\d+)/delete$', 'sml.serve.views.delete_reference', name='delete_reference'),
    url(r'client/(?P<client_id>\d+)/reference/add$', 'sml.serve.views.add_reference', name='add_reference'),

    url(r'client/(?P<client_id>\d+)/finances/add$', 'sml.serve.views.add_finance', name='add_finance'),
    url(r'client/(?P<client_id>\d+)/finances/(?P<finance_id>\d+)/delete', 'sml.serve.views.delete_finance', name='delete_finance'),

    url(r'client/(?P<client_id>\d+)/conviction/add$', 'sml.serve.views.add_conviction', name='add_conviction'),

    url(r'client/(?P<client_id>\d+)/assignment/add$', 'sml.serve.views.add_assignment', name='add_assignment'),
    url(r'client/(?P<client_id>\d+)/assignment/(?P<assignment_id>\d+)/complete$', 'sml.serve.views.complete_assignment', name='complete_assignment'),
    url(r'client/(?P<client_id>\d+)/assistance/add$', 'sml.serve.views.add_assistance', name='add_assistance'),
    url(r'client/(?P<client_id>\d+)/assistance/(?P<assistance_id>\d+)/save$', 'sml.serve.views.save_assistance', name='save_assistance'),

    url(r'client/(?P<client_id>\d+)/church/save$', 'sml.serve.views.save_church', name='save_church'),
    url(r'client/(?P<client_id>\d+)/employment/save$', 'sml.serve.views.save_employment', name='save_employment'),

    url(r'client/(?P<client_id>\d+)/comment/add$', 'sml.serve.views.add_comment', name='add_comment'),
    url(r'client/(?P<client_id>\d+)/document/add$', 'sml.serve.views.add_document', name='add_document'),

    url(r'^$', 'sml.serve.views.index', name='index'),
]
