from django.contrib import admin

from .models import Appointment, Client, Phone, Address, \
  Dependent, Homeless, Employment, Reference, Conviction, Church, \
  Comment, Finance, Referral, Assistance, Assignment, Document

from .models import Sex, Consideration, State, HomelessLocation, HomelessCause, \
  DependentRelation, Termination, ReferenceCategory, ConvictionCategory, \
  Frequency, Connection, CommentCategory, FinanceCategory, AssignmentCategory, \
  ReferralCategory, AssistanceCategory, AppointmentReasonCategory, \
  AppointmentReferralCategory


class ClientNameMixin:
    def client_name(self, obj):
        return obj.client.full_name

@admin.register(AppointmentReasonCategory)
class AppointmentReasonCategoryAdmin (admin.ModelAdmin):
    pass


@admin.register(AppointmentReferralCategory)
class AppointmentReferralCategoryAdmin (admin.ModelAdmin):
    pass


@admin.register(Sex)
class SexAdmin (admin.ModelAdmin):
    pass


@admin.register(Consideration)
class ConsiderationAdmin (admin.ModelAdmin):
    pass 


@admin.register(State)
class StateAdmin (admin.ModelAdmin):
    pass


@admin.register(HomelessLocation)
class HomelessLocationAdmin (admin.ModelAdmin):
    pass


@admin.register(HomelessCause)
class HomelessCauseAdmin (admin.ModelAdmin):
    pass


@admin.register(DependentRelation)
class DependentRelationAdmin (admin.ModelAdmin):
    pass


@admin.register(Termination)
class TerminationAdmin (admin.ModelAdmin):
    pass


@admin.register(ReferenceCategory)
class ReferenceCategoryAdmin (admin.ModelAdmin):
    pass


@admin.register(ConvictionCategory)
class ConvictionCategoryAdmin (admin.ModelAdmin):
    pass


@admin.register(Frequency)
class FrequencyAdmin (admin.ModelAdmin):
    pass


@admin.register(Connection)
class ConnectionAdmin (admin.ModelAdmin):
    pass


@admin.register(CommentCategory)
class CommentCategoryAdmin (admin.ModelAdmin):
    pass


@admin.register(FinanceCategory)
class FinanceCategoryAdmin (admin.ModelAdmin):
    list_display = ('name', 'get_type_display')


@admin.register(AssignmentCategory)
class AssignmentCategoryAdmin (admin.ModelAdmin):
    pass


@admin.register(ReferralCategory)
class ReferralCategoryAdmin (admin.ModelAdmin):
    pass


@admin.register(AssistanceCategory)
class AssistanceCategoryAdmin (admin.ModelAdmin):
    pass


@admin.register(Appointment)
class AppointmentAdmin (admin.ModelAdmin):
    list_display = ('start', 'last_name', 'first_name', 'birthdate')
    date_hierarchy = 'start' 
    search_fields = ['last_name', 'client__last_name']


@admin.register(Client)
class ClientAdmin (admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'birthdate')
    search_fields = ['last_name', 'first_name']


@admin.register(Phone)
class PhoneAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'number', 'primary')
    search_fields = ['number', 'client__last_name', 'client__first_name']


@admin.register(Address)
class AddressAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'street', 'city', 'state', 'zip', 'current')
    search_fields = ['street', 'client__last_name', 'client__first_name']

    def current(self, obj):
        return 'yes' if not obj.moved_out else 'no'


@admin.register(Homeless)
class HomelessAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'location', 'city', 'current')
    search_fields = ['client__last_name', 'client__first_name']
    
    def current(self, obj):
        return 'yes' if not obj.ended else 'no'


@admin.register(Dependent)
class DependentAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'full_name', 'birthdate', 'relation')
    search_fields = ['full_name', 'client__last_name', 'client__first_name']


@admin.register(Employment)
class EmploymentAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'name', 'role', 'start', 'current')
    search_fields = ['client__last_name', 'client__first_name']

    def current(self, obj):
        return 'yes' if not obj.end else 'no'
 

@admin.register(Reference)
class ReferenceAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'name', 'position', 'contact')
    search_fields = ['client__last_name', 'client__first_name']


@admin.register(Conviction)
class ConvictionAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'classification', 'when')
    search_fields = ['client__last_name', 'client__first_name']


@admin.register(Church)
class ChurchAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'name', 'attendence', 'connection')
    search_fields = ['client__last_name', 'client__first_name']


@admin.register(Comment)
class CommentAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'category', 'author', 'created')
    search_fields = ['client__last_name', 'client__first_name']


@admin.register(Finance)
class FinanceAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'category', 'amount')
    search_fields = ['client__last_name', 'client__first_name']


@admin.register(Referral)
class ReferralAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'category', 'when')
    search_fields = ['client__last_name', 'client__first_name']


@admin.register(Assignment)
class AssignmentAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'category', 'when', 'due', 'completed')
    search_fields = ['client__last_name', 'client__first_name']


@admin.register(Assistance)
class AssistanceAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'category', 'value', 'blocked', 'when', 'issued', 'referral', 'assignment', 'assisted_by')
    search_fields = ['client__last_name', 'client__first_name']

    def referrals(self, obj):
        return obj.referrals.count()

    def assignments(self, obj):
        return obj.assignments.count()


@admin.register(Document)
class DocumentAdmin (admin.ModelAdmin, ClientNameMixin):
    list_display = ('client_name', 'name', 'added', 'uri')
    search_fields = ['client__last_name', 'client__first_name']

    def uri(self, obj):
        return obj.payload.url

