import re
from uuid import uuid4
from django.db import models
from django.conf import settings
from datetime import datetime, timedelta, date

from .utils import date_from_string, datetime_from_string, date_to_age, datetime_round


class AppointmentReasonCategory (models.Model):
    name = models.CharField(max_length=16, unique=True)

    class Meta:
        verbose_name = 'Appointment Reason Category'
        verbose_name_plural = 'Appointment Reason Categories'

    def __str__(self):
        return self.name


class AppointmentReferralCategory (models.Model):
    name = models.CharField(max_length=16, unique=True)

    class Meta:
        verbose_name = 'Appointment Referral Category'
        verbose_name_plural = 'Appointment Referral Categories'

    def __str__(self):
        return self.name


class Appointment (models.Model):
    last_name = models.CharField(max_length=64)
    first_name = models.CharField(max_length=64)
    birthdate = models.DateField()
    phone = models.CharField(max_length=10,null=True,blank=True)
    caution = models.BooleanField(default=False)
    start = models.DateTimeField()
    canceled = models.BooleanField(default=False)
    client = models.ForeignKey('Client', related_name='appointments', null=True, blank=True)
    seen_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='appointments', null=True, blank=True)
    scheduled_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    referred_by = models.ForeignKey('AppointmentReferralCategory', related_name='appointments', null=True)
    reason = models.ForeignKey('AppointmentReasonCategory', related_name='appointments', null=True)

    @property
    def is_client(self):
        return False if self.client is None else True

    @property
    def end(self):
        return self.start + timedelta(hours=1)

    @property
    def age(self):
        return date_to_age(self.birthdate)   

    @property
    def nearest_start(self):
        return datetime_round(self.start)

    def save(self, *args, **kwargs):
        self.start = self.nearest_start
        return super(Appointment, self).save(*args, **kwargs)

    @classmethod
    def create(cls, last_name, first_name, birthdate, start, referral, reason, user, phone=None): 
        return cls(
            last_name=last_name.strip().capitalize(),
            first_name=first_name.strip().capitalize(),
            birthdate=date_from_string(birthdate),
            start=datetime_from_string(start),
            phone=phone,
            referred_by=referral,
            reason=reason,
            scheduled_by=user
        )


class Sex (models.Model):
    name = models.CharField(max_length=16, unique=True)
    
    class Meta:
        verbose_name = 'Sex Category'
        verbose_name_plural = 'Sex Categories'

    def __str__(self):
        return self.name


class Consideration (models.Model):
    name = models.CharField(max_length=16, unique=True)

    class Meta:
        verbose_name = 'Consideration Category'
        verbose_name_plural = 'Consideration Categories'

    def __str__(self):
        return self.name


class Client (models.Model):
    last_name = models.CharField(max_length=64)
    first_name = models.CharField(max_length=64)
    birthdate = models.DateField()
    created = models.DateField()
    sex = models.ForeignKey(Sex, null=True, blank=True)
    consideration = models.ForeignKey(Consideration, null=True, blank=True)
    caution = models.BooleanField(default=False)

    def __str__(self):
        return '{} - ID {}'.format(self.full_name, self.pk)

    @property
    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    @property
    def primary_phone(self):
        primaries = self.phones.filter(primary=True)
        return None if not primaries else primaries[0]

    @classmethod
    def create(cls, last_name, first_name, birthdate): 
        return cls(
            last_name=last_name.strip().capitalize(),
            first_name=first_name.strip().capitalize(),
            birthdate=date_from_string(birthdate),
            created=date.today()
        )


class Phone (models.Model):
    number = models.CharField(max_length=10)
    client = models.ForeignKey('Client', related_name='phones')
    primary = models.BooleanField()

    class Meta:
        unique_together = ('number', 'client')

    def __str__(self):
        return '({}) {}-{}'.format(self.number[0:3], self.number[3:6], self.number[6:])

    def save(self, *args, **kwargs):
        self.number = re.sub(r'\D', '', self.number)
        return super(Phone, self).save(*args, **kwargs)

    @classmethod
    def create(cls, number, client, primary=True):
        return cls(
            number=number.strip(),
            client=client,
            primary=primary
        )


class State (models.Model):
    name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name


class Address (models.Model):
    street = models.CharField(max_length=64)
    street_number = models.CharField(max_length=64, blank=True, null=True)
    city = models.CharField(max_length=64)
    state = models.ForeignKey('State', related_name='addresses')
    zip = models.IntegerField()
    moved_in = models.DateField()
    moved_out = models.DateField(null=True, blank=True)
    client = models.ForeignKey('Client', related_name='addresses')

    class Meta:
        verbose_name_plural = 'Addresses'

    def duration(self):
        return self.moved_out - self.moved_in

    def __str__(self):
        return '{} {}, {}, {} {}'.format(self.street, self.street_number, self.city, self.state, self.zip)

    @classmethod
    def create(cls, street, number, city, state, zip, moved, client):
        return cls(
            street=street.strip().title(),
            street_number=number.strip().title() if number else None,
            city=city.strip().title(),
            state=state,
            zip=zip,
            moved_in=date_from_string(moved), 
            client=client
        )

    def update(self, street, number, city, state, zip, moved_in, moved_out):
        self.street = street.strip().title()
        self.street_number = number.strip().title() if number else None
        self.city = city.strip().title()
        self.state = state
        self.zip = zip
        self.moved_in = date_from_string(moved_in)
        self.moved_out = date_from_string(moved_out) if moved_out else None


class HomelessLocation (models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name = 'Homeless Location Category'
        verbose_name_plural = 'Homeless Location Categories'

    def __str__(self):
        return self.name


class HomelessCause (models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name = 'Homeless Cause Category'
        verbose_name_plural = 'Homeless Cause Categories'

    def __str__(self):
        return self.name


class Homeless (models.Model):
    location = models.ForeignKey('HomelessLocation', related_name='homelessness')
    city = models.CharField(max_length=64)
    started = models.DateField()
    ended = models.DateField(null=True, blank=True)
    cause = models.ForeignKey('HomelessCause', related_name='homelessness')
    client = models.ForeignKey('Client', related_name='homeless')

    class Meta:
        verbose_name_plural = 'Homelessness'

    def duration(self):
        return self.ended - self.started

    def update(self, location, city, started, ended, cause):
        self.location = location
        self.city = city.strip().title()
        self.started = date_from_string(started)
        self.ended = date_from_string(ended) if ended else None
        self.cause = cause

    @classmethod
    def create(cls, location, city, started, cause, client):
        return cls(
            location=location,
            city=city.strip().title(),
            started=date_from_string(started),
            cause=cause,
            client=client
        )     


class DependentRelation (models.Model):
    name = models.CharField(max_length=32, unique=True)

    class Meta:
        verbose_name = 'Dependent Relationship Category'
        verbose_name_plural = 'Dependent Relationship Categories'

    def __str__(self):
        return self.name


class Dependent (models.Model):
    last_name = models.CharField(max_length=64)
    first_name = models.CharField(max_length=64)
    birthdate = models.DateField()
    relation = models.ForeignKey('DependentRelation', related_name='dependents')
    client = models.ForeignKey('Client', related_name='dependents')

    @property
    def age(self):
        return date_to_age(self.birthdate)

    @property
    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def __str__(self):
        return self.full_name

    @classmethod
    def create(cls, last_name, first_name, birthdate, relation, client):
        return cls(
            last_name=last_name.strip().title(),
            first_name=first_name.strip().title(),
            birthdate=date_from_string(birthdate),
            relation=relation,
            client=client
        )


class Termination (models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        verbose_name = 'Termination Category'
        verbose_name_plural = 'Termination Categories'

    def __str__(self):
        return self.name


class Employment (models.Model):
    name = models.CharField(max_length=128)
    start = models.DateField()
    end = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=128)
    reason = models.ForeignKey('Termination', related_name='employment')
    client = models.ForeignKey('Client', related_name='employment')

    def duration(self):
        return self.end - self.start

    class Meta:
        verbose_name_plural = 'Employment'

    def update(self, name, start, end, role, reason):
        self.name = name.strip().title()
        self.start = date_from_string(start)
        self.end = date_from_string(end) if end else None
        self.role = role.strip().title()
        self.reason = reason

    @classmethod
    def create(cls, name, start, end, role, reason, client):
        return cls(
            name=name.strip().title(),
            start=date_from_string(start),
            role=role.strip().title(),
            reason=reason,
            client=client
        )


class ReferenceCategory (models.Model):
    name = models.CharField(max_length=128)
    individual = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Reference Category'
        verbose_name_plural = 'Reference Categories'

    def __str__(self):
        return self.name


class Reference (models.Model):
    name = models.CharField(max_length=128)
    position = models.ForeignKey('ReferenceCategory', related_name='references')
    contact = models.CharField(max_length=128, null=True, blank=True)
    client = models.ForeignKey('Client', related_name='references')

    @classmethod
    def create(cls, name, position, contact, client):
        return cls(
            name=name.strip().title(),
            position=position,
            contact=contact.strip(),
            client=client
        )


class ConvictionCategory (models.Model):
    name = models.CharField(max_length=128)
  
    class Meta:
        verbose_name = 'Conviction Category'
        verbose_name_plural = 'Conviction Categories'

    def __str__(self):
        return self.name


class Conviction (models.Model):
    classification = models.ForeignKey('ConvictionCategory', related_name='convictions')
    when = models.DateField()
    officer = models.CharField(max_length=64, null=True, blank=True)
    client = models.ForeignKey('Client', related_name='convictions')

    @classmethod
    def create(cls, classification, when, officer, client):
        return cls(
            classification=classification,
            when=date_from_string(when),
            officer=officer.strip().title(),
            client=client
        )


class Frequency (models.Model):
    name = models.CharField(max_length=128)
  
    class Meta:
        verbose_name = 'Frequency Category'
        verbose_name_plural = 'Frequency Categories'

    def __str__(self):
        return self.name


class Connection (models.Model):
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = 'Connection Category'
        verbose_name_plural = 'Connection Categories'

    def __str__(self):
        return self.name


class Church (models.Model):
    name = models.CharField(max_length=128, unique=True)
    contact = models.CharField(max_length=64)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=11)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Churches'


class ChurchAttendence (models.Model):
    church = models.ForeignKey('Church', related_name='attendees')
    attendence = models.ForeignKey('Frequency', related_name='church_attendence')
    connection = models.ForeignKey('Connection', related_name='church_connections')
    client = models.ForeignKey('Client', related_name='church_attendence')

    class Meta:
       verbose_name_plural = 'Church Attendence'

    @classmethod
    def create(cls, church, attendence, connection, client):
        return cls(
            church=church,
            attendence=attendence,
            connection=connection,
            client=client
        )


class CommentCategory (models.Model):
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = 'Comment Category'
        verbose_name_plural = 'Comment Categories'

    def __str__(self):
        return self.name


class Comment (models.Model):
    created = models.DateTimeField()
    category = models.ForeignKey('CommentCategory', related_name='comments')
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comments')
    client = models.ForeignKey('Client', related_name='comments')

    @classmethod
    def create(cls, category, content, author, client):
        return cls(
            created=datetime.now(),
            category=category,
            content=content.strip(),
            author=author,
            client=client
        )


class FinanceCategory (models.Model):
    name = models.CharField(max_length=128)
    type = models.IntegerField(choices=((0, 'Income'), (1, 'Expense')))

    class Meta:
        verbose_name = 'Finance Category'
        verbose_name_plural = 'Finance Categories'

    def __str__(self):
        return self.name


class Finance (models.Model):
    amount = models.IntegerField()
    category = models.ForeignKey('FinanceCategory', related_name='finances')
    client = models.ForeignKey('Client', related_name='finances')
    dependent = models.ForeignKey('Dependent', null=True, blank=True, related_name='finances')

    @classmethod
    def create(cls, amount, category, client, dependent=None):
        return cls(
            amount=int(amount),
            category=category,
            client=client,
            dependent=dependent
        )


class AssignmentCategory (models.Model):
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = 'Assignment Category'
        verbose_name_plural = 'Assignment Categories'

    def __str__(self):
        return self.name


class Assignment (models.Model):
    category = models.ForeignKey('AssignmentCategory', related_name='assignments')
    details = models.TextField(null=True)
    when = models.DateField()
    due = models.DateField()
    abandoned = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    client = models.ForeignKey('Client', related_name='assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL)

    def __str__(self):
        return '{} ({})'.format(self.category, self.when)

    @classmethod
    def create(cls, category, details, when, due, completed, assigned_by, client):
        return cls(
            category=category,
            details=details.strip(),
            when=date_from_string(when),
            due=date_from_string(due),
            completed=completed if completed else False,
            assigned_by=assigned_by,
            client=client
        )


class ReferralCategory (models.Model):
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = 'Referral Category'
        verbose_name_plural = 'Referral Categories'

    def __str__(self):
        return self.name


class Referral (models.Model):
    category = models.ForeignKey('ReferralCategory', related_name='referrals')
    details = models.TextField(null=True)
    when = models.DateField()
    client = models.ForeignKey('Client', related_name='referrals')


class AssistanceCategory (models.Model):
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name = 'Assistance Category'
        verbose_name_plural = 'Assistance Categories'

    def __str__(self):
        return self.name


class Assistance (models.Model):
    value = models.IntegerField()
    when = models.DateField()
    issued = models.DateField(null=True, blank=True)
    blocked = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    details = models.TextField(null=True)
    category = models.ForeignKey('AssistanceCategory', related_name='assistance')
    client = models.ForeignKey('Client', related_name='assistance')
    assisted_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    assignment = models.ForeignKey('Assignment', null=True, blank=True, related_name='assistance')
    referral = models.ForeignKey('Referral', null=True, blank=True, related_name='assistance')

    def __str__(self):
        return '{} - {}'.format(self.category, self.when)

    class Meta:
       verbose_name_plural = 'Assistance'

    @classmethod
    def create(cls, value, when, details, category, client, user):
        return cls(
            value=value,
            when=date_from_string(when),
            details=details.strip(),
            category=category,
            client=client,
            issued=None,
            blocked=False,
            rejected=False,
            assisted_by=user,
            assignment=None,
            referral=None
        )


class IntentToAssist (models.Model):
    church = models.ForeignKey('Church', related_name='assistance', null=True, blank=True)
    assistance = models.ForeignKey('Assistance', related_name='intentions')
    amount = models.IntegerField()
    payee = models.CharField(max_length=256)
    payee_address = models.CharField(max_length=256)
    payee_phone = models.CharField(max_length=10, blank=True, null=True)
    payee_memo = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created = models.DateField(default=date.today)
    submitted = models.DateField(null=True,blank=True)
    completed = models.DateField(null=True,blank=True)

    def __str__(self):
        return 'Intented: {}'.format(self.assistance)

    class Meta:
        verbose_name_plural = 'Intents To Assist'
        verbose_name = 'Intent To Assist'


def document_path(instance, filename):
    return '/'.join(['clients', 'documents', str(instance.client.pk), filename])


class Document (models.Model):
    name = models.CharField(max_length=128)
    added = models.DateField()
    payload = models.FileField(upload_to=document_path, max_length=256)
    client = models.ForeignKey('Client', related_name='documents')

    @property
    def friendly_name(self):
        return self.payload.url.split('/')[-1]

    @classmethod
    def create(cls, name, payload, client):
        return cls(
            name=name.strip().title(),
            added=datetime.today(),
            payload=payload,
            client=client
        )


