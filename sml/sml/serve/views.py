import json

from time import mktime
from string import Template
from functools import partial
from datetime import datetime, timedelta, date

from django.shortcuts import render_to_response, redirect
from django.http import JsonResponse
from django.core.urlresolvers import reverse

from django.contrib.auth import logout as user_logout, login as user_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate

from .models import Appointment, Client, Phone, Address, Dependent, Homeless, \
    Employment, Reference, Conviction, Comment, Church, Finance, Assignment, \
    Assistance, Document

from .models import Sex, Consideration, State, HomelessLocation, HomelessCause, \
    DependentRelation, Termination, ReferenceCategory, ConvictionCategory, \
    CommentCategory, Connection, AssistanceCategory, AssignmentCategory, Frequency, \
    AppointmentReasonCategory, AppointmentReferralCategory, FinanceCategory


class MissingDataError (Exception):

    def __init__(self, message):
        self.message = message


def form_field(request, field, friendly, required=True, message='is required'):

    value = request.POST.get(field, None)
    if not value and required:
        raise MissingDataError('{} {}'.format(friendly, message))
    return value.strip() if value else None


def form_field_list(request, field, friendly, required=True, message='is required'):

    value = request.POST.getlist(field)
    if not value and required:
        raise MissingDataError('{} {}'.format(friendly, message))
    return value if value else []


def standard_context(request):
    return {
        'now': datetime.now(),
        'user': request.user
    }


def has_form_error(request):
    return True if request.session.has_key('form_error') else False    


def form_error(request, error=None):
    if error:
        request.session['form_error'] = error
    else:
        error = request.session.get('form_error', None)
        if error:
            del request.session['form_error']
        return error


def login(request):
   if request.method == 'POST':
       username, password = request.POST['username'], request.POST['password']
       user = authenticate(username=username, password=password)

       if user is not None and user.is_active:
           user_login(request, user)
           return redirect('index') 

   return render_to_response('login.template', {})


def logout(request):
    user_logout(request)
    return redirect('index') 


@login_required
def index(request):
    context = standard_context(request)

    today = context['now'].date()
    yesterday = today - timedelta(days=1)
    cutoff = today - timedelta(days=30)

    appointments = Appointment.objects.filter(start__contains=today).order_by('start')
    assignments = Assignment.objects.filter(due__contains=today, completed=False)
    assignments_late = Assignment.objects.filter(due__range=(cutoff, yesterday), completed=False).order_by('-due')

    clients = Client.objects.count()

    context.update({
       'appointments': appointments,
       'assignments_today': assignments,
       'assignments_late': assignments_late,
       'client_count': clients,
    })

    return render_to_response('summary.template', context)


@login_required
def appointment(request, appointment_id):
    context = standard_context(request)

    appointment = Appointment.objects.get(pk=appointment_id)

    context.update({
        'appointment': appointment
    }) 

    if appointment.client:
        now = context['now']
        client = appointment.client
        queryset = Appointment.objects.filter(client=client).filter(start__lt=now).order_by('-start')
        prior = queryset[0] if queryset else None

        context.update({
            'client': client,
            'prior': prior,
        })
  
    return render_to_response('select-appointment.template', context)


@login_required
def start_appointment(request, appointment_id): 

    # TODO: Should be a POST

    appointment = Appointment.objects.get(pk=appointment_id)

    if not appointment.client:
        client = Client.create(
            appointment.last_name, 
            appointment.first_name, 
            appointment.birthdate
        )
        client.save()

        if appointment.phone:
            Phone.create(
                appointment.phone,
                client,
                True
            ).save()

        appointment.client = client

    appointment.canceled = False
    appointment.seen_by = request.user
    appointment.save()
   
    return redirect('view_client', client_id=appointment.client.pk)
   

@login_required
def reset_appointment(request, appointment_id):

    appointment = Appointment.objects.get(pk=appointment_id)
    appointment.canceled = False
    appointment.seen_by = None
    appointment.save()

    return redirect('index')
 

@login_required
def cancel_appointment(request, appointment_id):
   
    # TODO: Should be a POST

    appointment = Appointment.objects.get(pk=appointment_id)
    appointment.seen_by = None
    appointment.canceled = True
    appointment.save()

    return redirect('index')


@login_required
def new_appointment(request):

    if request.method == 'POST' and not has_form_error(request):
        try:
            last_name = form_field(request, 'last_name', 'Last Name')    
            first_name = form_field(request, 'first_name', 'First Name')
            birthdate = form_field(request, 'birthdate', 'Birth Date')
            start = form_field(request, 'start', 'Appointment Time')
            phone = form_field(request, 'phone', 'Phone Number', required=False)
            client = form_field(request, 'client', 'Client', required=False)
            reason = form_field(request, 'reason', 'Appointment Reason')
            referral = form_field(request, 'referral', 'Appointment Referral')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('new_appointment')

        reason = AppointmentReasonCategory.objects.get(pk=reason)
        referral = AppointmentReferralCategory.objects.get(pk=referral)

        appointment = Appointment.create(last_name, first_name, birthdate, start, referral, reason, request.user, phone) 

        if client:
            appointment.client = Client.objects.get(pk=client)

        appointment.save()
        return redirect('index')

    context = standard_context(request)
    context.update({
        'reason_choices': AppointmentReasonCategory.objects.all().order_by('name'),
        'referral_choices': AppointmentReferralCategory.objects.all().order_by('name')        
    })
 
    if has_form_error(request):
        context.update({'error': form_error(request)})
    elif 'client' in request.GET:
        client = request.GET['client']
        client = Client.objects.get(pk=client)
        context['client'] = client
    
    return render_to_response('schedule-appointment.template', context)


@login_required
def view_calendar(request):
    context = standard_context(request)
    return render_to_response('calendar.template', context)


@login_required
def get_calendar_appointments(request):
    # See: https://github.com/Serhioromano/bootstrap-calendar

    now = datetime.now()
    late = timedelta(hours=1)

    start = int(request.GET['from']) / 1000
    start = datetime.fromtimestamp(start)
    end = int(request.GET['to']) / 1000
    end = datetime.fromtimestamp(end)

    epoch = datetime.fromtimestamp(0)

    def appointment_meta(a):
        if a.canceled:
            return 'canceled', 'event-warning'
        if not a.canceled and not a.seen_by and a.start + late < now:
            return 'no-show', 'event-special'
        if not a.canceled and a.seen_by:
            return 'seen', 'event-success'
        return 'scheduled', 'event-info'

    def convert_datetime(dt):
        dt = mktime(dt.timetuple()) + dt.microsecond / 1e6
        return int(dt * 1000)

    appointments = [ 
        {
          'id': a.pk,
          'title': '{}, {} ({})'.format(a.last_name, a.first_name, appointment_meta(a)[0]),
          'url': reverse('appointment', args=[a.pk]),
          'class': appointment_meta(a)[1],
          'start': convert_datetime(a.start),
          'end': convert_datetime(a.end)
        } 
        for a in Appointment.objects.filter(start__range=[start, end])
    ]

    payload = {
        'success': 1,
        'result': appointments
    }

    return JsonResponse(payload)


@login_required
def search_clients(request):
    # See: https://github.com/biggora/bootstrap-ajax-typeahead

    if request.is_ajax():
       query = request.GET['query']

       last = Client.objects.filter(last_name__iexact=query).count()
       first = Client.objects.filter(first_name__iexact=query).count()
       phone = Phone.objects.filter(number=query).count()
       dependents = Dependent.objects.filter(name__iexact=query).count()

       if ' ' in query:
           parts = query.split(' ', maxsplit=1)
           full = Client.objects.filter(first_name__iexact=parts[0], last_name__iexact=parts[1]).count() 
       else:
           full = 0
 
       options = [
         {'id': 'last|{}'.format(query), 'name': query, 'type': 'Last Name', 'matches': last },
         {'id': 'first|{}'.format(query), 'name': query, 'type': 'First Name', 'matches': first },
         {'id': 'full|{}'.format(query), 'name': query, 'type': 'Full Name', 'matches': full },
         {'id': 'phone|{}'.format(query), 'name': query, 'type': 'Phone Number', 'matches': phone},
         {'id': 'dependents|{}'.format(query), 'name': query, 'type': 'Dependent', 'matches': dependents}
       ]

       return JsonResponse(options, safe=False)


@login_required
def get_comment(request):

    if request.is_ajax():
        comment_id = request.GET['id']
        queryset = Comment.objects.filter(pk=comment_id)
        comment = queryset[0] if queryset else None

        return render_to_response('fragment/details/comment.template', {'comment': comment})


@login_required
def add_comment(request, client_id):

    if request.method == 'POST':
        try:
            created = form_field(request, 'comment_created', 'Comment Created')
            content = form_field(request, 'comment_content', 'Comment Content')
            category = form_field(request, 'comment_category', 'Comment Category')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        Comment.create(category, content, request.user, client).save()

    return redirect('view_client', client_id=client_id)


@login_required
def list_clients(request):

    client_field_lookup = {
        'last': (lambda n: {'last_name__iexact': n}, ('last_name', 'first_name', 'birthdate')),
        'first': (lambda n: {'first_name__iexact': n}, ('first_name', 'last_name', 'birthdate')),
        'full': (lambda n: {'last_name__iexact': n.split(' ')[1], 'first_name__iexact': n.split(' ')[0]}, ('last_name', 'first_name', 'birthdate')),
        'dependents': (lambda n: {'dependents__name__iexact': n}, ('last_name', 'first_name', 'birthdate')),
    }

    phone_field_lookup = {
        'phone': (lambda n: {'number': n}, ('number', 'client__last_name', 'client__first_name')),
    }

    if request.is_ajax():
        request_name, request_type = request.GET['name'], request.GET['type']

        if request_type in client_field_lookup:
            transformer, order = client_field_lookup[request_type]
            parameters = transformer(request_name)
            clients = Client.objects.filter(**parameters).order_by(*order)
        elif request_type in phone_field_lookup:
            transformer, order = phone_field_lookup[request_type]
            parameters = transformer(request_name)
            phones = Phone.objects.filter(**parameters).order_by(*order)
            clients = [phone.client for phone in phones]

        return render_to_response('fragment/lists/clients.template', {'clients': clients})


@login_required
def view_client(request, client_id):

    now = datetime.now()
    today = now.today()

    client = Client.objects.get(pk=client_id)
    context = standard_context(request)
    context.update({
        'client': client,
        'now': now,
        'today': today,
    })

    context.update({
        'frequencies': Frequency.objects.all().order_by('name'),
        'address_states': State.objects.all().order_by('name'),
        'sexes': Sex.objects.all().order_by('name'),
        'considerations': Consideration.objects.all().order_by('name'),
        'dependent_relations': DependentRelation.objects.all().order_by('name'),
        'homeless_locations': HomelessLocation.objects.all().order_by('name'),
        'homeless_causes': HomelessCause.objects.all().order_by('name'),
        'employment_reasons': Termination.objects.all().order_by('name'),
        'reference_choices': ReferenceCategory.objects.all().order_by('name'),
        'conviction_choices': ConvictionCategory.objects.all().order_by('name'),
        'church_connection_choices': Connection.objects.all().order_by('name'),
        'comment_category_choices': CommentCategory.objects.all().order_by('name'),
        'assistance_category_choices': AssistanceCategory.objects.all().order_by('name'),
        'assignment_category_choices': AssignmentCategory.objects.all().order_by('name')
    })

    context.update({
        'appointments_upcoming': Appointment.objects.filter(client=client).filter(start__gte=now),
        'appointments_past': Appointment.objects.filter(client=client).filter(start__lt=now),
    })

    if has_form_error(request):
        context.update({'error': form_error(request)})

    return render_to_response('client.template', context)


@login_required
def save_client(request, client_id):

    if request.method == 'POST':
        try:
            last = form_field(request, 'last', 'Last Name')
            first = form_field(request, 'first', 'First Name')
            sex = form_field(request, 'sex', 'Sex')
            birthdate = form_field(request, 'birthdate', 'Birth Date')
            consideration = form_field(request, 'consideration', 'Special Consideration')
            caution = form_field(request, 'caution', '', required=False)
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        if client:
            client.last_name = last
            client.first_name = first
            client.sex = Sex.objects.get(pk=sex)
            client.birthdate = birthdate
            client.consideration = Consideration.objects.get(pk=consideration)
            client.caution = False if not caution else True
            client.save()

            for appointment in client.appointments.all():
                appointment.last_name = client.last_name
                appointment.first_name = client.first_name
                appointment.birthdate = client.birthdate
                appointment.caution = client.caution
                appointment.save()

    return redirect('view_client', client_id=client_id)

@login_required
def delete_phone(request, client_id, phone_id):

    if request.method == 'POST':
        Phone.objects.filter(pk=phone_id).delete()

    return redirect('view_client', client_id=client_id)


@login_required
def add_phone(request, client_id):

    if request.method == 'POST':
        try:
            number = form_field(request, 'phone_number', 'Phone Number') 
            primary = form_field(request, 'phone_primary', '', required=False)
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None
        queryset = Phone.objects.filter(number=number, client__pk=client_id)
        phone = queryset[0] if queryset else None
        primary = True if primary and primary.lower() == 'on' else False

        if client and not phone:
            existing_primaries = Phone.objects.filter(primary=True, client__pk=client_id)

            if primary:
                for record in existing_primaries:
                    record.primary = False
                    record.save()

            phone = Phone.create(number, client, True if primary or not existing_primaries else False)
            phone.save()
        else:
            form_error(request, 'Phone number exists for client')
                   
    return redirect('view_client', client_id=client_id)


@login_required
def save_address(request, client_id):

    if request.method == 'POST':
        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        if not client:
            return redirect('view_client', client_id=client_id)

        if Homeless.objects.filter(client=client, started__isnull=False, ended__isnull=True).exists():
            form_error(request, 'Client has current home address. Please complete move-out!')
            return redirect('view_client', client_id=client_id)

        try:
            street = form_field(request, 'street', 'Street')
            street_number = form_field(request, 'street_number', '', required=False)
            city = form_field(request, 'city', 'City')
            state = form_field(request, 'state', 'State')
            zip = form_field(request, 'zip', 'Zip Code')
            moved_in = form_field(request, 'moved_in', 'Move-in Date')
            moved_out = form_field(request, 'moved_out', '', required=False)
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Address.objects.filter(client=client)
        current = queryset.filter(moved_in__isnull=False, moved_out__isnull=True)

        if current.exists():
            address = current[0]
            address.update(street, street_number, city, State.objects.get(pk=state), zip, moved_in, moved_out)
            address.save()
        else: 
            Address.create(
                street=street, 
                number=street_number,
                city=city,
                state=State.objects.get(pk=state),
                zip=zip,
                moved=moved_in,
                client=client
            ).save()

    return redirect('view_client', client_id=client_id)


@login_required
def save_homeless(request, client_id):

    if request.method == 'POST':
        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        if not client:
            return redirect('view_client', client_id=client_id)

        if Address.objects.filter(client=client, moved_in__isnull=False, moved_out__isnull=True).exists():
            form_error(request, 'Client has current home address. Please complete move-out!')
            return redirect('view_client', client_id=client_id)

        try:
            city = form_field(request, 'city', 'Homeless City')
            location = form_field(request, 'location', 'Homelessness Location')
            started = form_field(request, 'started', 'Homelessness Start Date')
            ended = form_field(request, 'ended', '', required=False)
            cause = form_field(request, 'cause', 'Homelessness Cause')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Homeless.objects.filter(client=client)
        current = queryset.filter(started__isnull=False, ended__isnull=True)

        location = HomelessLocation.objects.get(pk=location)
        cause = HomelessCause.objects.get(pk=cause)

        if current.exists():
            homeless = current[0]
            homeless.update(location, city, started, ended, cause)
            homeless.save()
        else:
            Homeless.create(
                location=location, 
                city=city, 
                started=started,
                cause=cause, 
                client=client
            ).save()

    return redirect('view_client', client_id=client_id)


@login_required
def add_dependent(request, client_id):

    if request.method == 'POST':
        try:
            name = form_field(request, 'dependent_name', 'Dependent Name')
            birthdate = form_field(request, 'dependent_birthdate', 'Dependent Birth Date')
            relation = form_field(request, 'dependent_relation', 'Dependent Relationship')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None
        queryset = Dependent.objects.filter(name=name, client__pk=client_id)
        dependent = queryset[0] if queryset else None

        if client and not dependent:
            dependent = Dependent.create(name, birthdate, DependentRelation.objects.get(pk=relation), client)
            dependent.save()
        else:
            form_error(request, 'Dependent already exists for client')

    return redirect('view_client', client_id=client_id)


@login_required
def delete_dependent(request, client_id, dependent_id):

    if request.method == 'POST':
        Dependent.objects.filter(pk=dependent_id).delete()

    return redirect('view_client', client_id=client_id)


@login_required
def save_church(request, client_id):

    if request.method == 'POST':
        try:
            name = form_field(request, 'church_name', 'Church Name')
            attendence = form_field(request, 'church_attendence', 'Church Attendence')
            connection = form_field(request, 'church_connection', 'Church Connection')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        attendence = Frequency.objects.get(pk=attendence)
        connection = Connection.objects.get(pk=connection)

        Church.objects.filter(client=client).delete()
        Church.create(name, attendence, connection, client).save()

    return redirect('view_client', client_id=client_id)


@login_required
def save_employment(request, client_id):

    if request.method == 'POST':
        try:
            name = form_field(request, 'employment_name', 'Employer')
            role = form_field(request, 'employment_role', 'Employee Role')
            start = form_field(request, 'employment_start', 'Employee Join Date')
            end = form_field(request, 'employment_end', '', required=False)
            reason = form_field(request, 'employment_reason', '', required=False)
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        current = Employment.objects.filter(client=client, name=name, start__isnull=False, end__isnull=True)
        reason = Termination.objects.get(pk=reason)

        if current.exists():
            employment = current[0]
            employment.update(name, start, end, role, reason)
            employment.save()
        else:
            Employment.create(
                name, 
                start, 
                end, 
                role, 
                reason, 
                client
            ).save()

    return redirect('view_client', client_id=client_id)


@login_required
def delete_reference(request, client_id, reference_id):

    if request.method == 'POST':
        Reference.objects.filter(pk=reference_id).delete()

    return redirect('view_client', client_id=client_id)


@login_required
def add_reference(request, client_id):

    if request.method == 'POST':
        try:
            name = form_field(request, 'reference_name', 'Reference Name')
            position = form_field(request, 'reference_position', 'Reference Position')
            contact = form_field(request, 'reference_contact', 'Reference Contact')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        queryset = Reference.objects.filter(name=name, client=client)

        if queryset.exists():
            form_error(request, '{} exists as a reference for {}.'.format(name, client.full_name))
            return redirect('view_client', client_id=client_id)

        position = ReferenceCategory.objects.get(pk=position)

        Reference.create(name, position, contact, client).save()

    return redirect('view_client', client_id=client_id)


@login_required
def add_conviction(request, client_id):

    if request.method == 'POST':
        try:
            classification = form_field(request, 'conviction_classification', 'Conviction Type')
            when = form_field(request, 'conviction_date', 'Conviction Date')
            officer = form_field(request, 'conviction_officer', 'Conviction Correction Officer')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None
        classification = ConvictionCategory.objects.get(pk=classification)

        Conviction.create(classification, when, officer, client).save()

    return redirect('view_client', client_id=client_id)


@login_required
def add_assignment(request, client_id):

    if request.method == 'POST':
        try:
            category = form_field(request, 'assignment_category', 'Assignment Category')
            started = form_field(request, 'assignment_started', 'Assignment Date')
            due = form_field(request, 'assignment_due', 'Assignment Due Date')
            completed = form_field(request, 'assignment_completed', '', required=False)
            details = form_field(request, 'assignment_details', 'Assignment Details')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None
        category = AssignmentCategory.objects.get(pk=category)

        Assignment.create(category, details, started, due, completed, request.user, client).save()

    return redirect('view_client', client_id=client_id)


@login_required
def complete_assignment(request, client_id, assignment_id):

    if request.method == 'POST':
        queryset = Assignment.objects.filter(pk=assignment_id)
        assignment = queryset[0] if queryset else None

        if 'complete' in request.POST and assignment:
            assignment.completed = True
            assignment.abandoned = False
            assignment.save()
        elif 'abandon' in request.POST and assignment:
            assignment.completed = False
            assignment.abandoned = True
            assignment.save()

        queryset = Assistance.objects.filter(assignment=assignment.pk, issued=None, blocked=True)

        for request in queryset:
            request.blocked = False
            request.rejected = False
            request.save()

    return redirect('view_client', client_id=client_id)


@login_required
def add_assistance(request, client_id):

    if request.method == 'POST':
        try:
            category = form_field(request, 'category', 'Assistance Category')
            value = form_field(request, 'value', 'Assistance Value')
            started = form_field(request, 'started', 'Assistance Date')
            details = form_field(request, 'details', 'Assistance Details')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        client = Client.objects.get(pk=client_id)

        Assistance.create(
            value, 
            started, 
            details, 
            AssistanceCategory.objects.get(pk=category), 
            client, 
            request.user
        ).save()
        

    return redirect('view_client', client_id=client_id)

@login_required
def save_assistance(request, client_id, assistance_id):

    if request.method == 'POST':
        queryset = Assistance.objects.filter(pk=assistance_id)
        assistance = queryset[0] if queryset else None

        if 'issue' in request.POST:
            assistance.issued = datetime.today()
            assistance.blocked = False
            assistance.rejected = False
            assistance.save()
        elif 'block' in request.POST:
            assistance.issued = None
            assistance.blocked = True
            assistance.rejected = False
            assistance.assignment = None
            assistance.save()
        elif 'reject' in request.POST:
            assistance.issued = None
            assistance.blocked = False
            assistance.rejected = True
            assistance.assignment = None
            assistance.save()
        elif 'assign' in request.POST:
            try:
                assignment = form_field(request, 'assistance_assignment', '', required=False)
            except MissingDataError as error:
                form_error(request, error.message)
                return redirect('view_client', client_id=client_id)

            assignment = Assignment.objects.get(pk=assignment) if assignment != 'NONE' else None
            assistance.assignment = assignment
            assistance.save()

    return redirect('view_client', client_id=client_id)


@login_required
def add_comment(request, client_id):

    if request.method == 'POST':
        try:
            category = form_field(request, 'comment_category', 'Comment Category')
            content = form_field(request, 'comment_content', 'Comment Content')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        if content.strip() == '':
            form_error(request, 'Comment must not be empty')
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        category = CommentCategory.objects.get(pk=category)

        Comment.create(
            category=category,
            content=content,
            author=request.user, 
            client=client
        ).save()


    return redirect('view_client', client_id=client_id)


@login_required
def save_finances(request, client_id):

    if request.method == 'POST':
        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        body = request.body.decode()
        payload = json.loads(body) 

        if 'income' in payload and 'expenses' in payload:
            Finance.objects.filter(client=client).delete()
            
            income = FinanceCategory.objects.get(name='Income')
            expense = FinanceCategory.objects.get(name='Expense')

            for name, amount in payload.get('income', {}).items():
                Finance.create(amount, name, income, client).save()
            for name, amount in payload.get('expenses', {}).items():
                Finance.create(amount, name, expense, client).save()                

    return redirect('view_client', client_id=client_id)


@login_required
def add_document(request, client_id):

    if request.method == 'POST' and request.FILES:
        try:
            name = form_field(request, 'name', 'Document Name')
        except MissingDataError as error:
            form_error(request, error.message)
            return redirect('view_client', client_id=client_id)

        path = None if 'path' not in request.FILES else request.FILES['path']

        if not path:
            form_error(request, 'Document file upload must be present')
            return redirect('view_client', client_id=client_id)

        queryset = Client.objects.filter(pk=client_id)
        client = queryset[0] if queryset else None

        document = Document.create(name, path, client)
        document.save()

    return redirect('view_client', client_id=client_id)    

