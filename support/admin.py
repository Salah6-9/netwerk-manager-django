from django.contrib import admin
from .models import SupportTicket, TicketMessage


class TicketMessageInline(admin.TabularInline):

    model = TicketMessage
    extra = 0

    readonly_fields = (
        "author",
        "content",
        "created_at",
    )

    can_delete = False


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "user",
        "device",
        "status",
        "created_at",
    )



    inlines = [TicketMessageInline]

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "title",
        "user__username",
        "device__hostname",
    )


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):

    list_display = (
        "ticket",
        "author",
        "created_at",
    )

    search_fields = (
        "ticket__ticket_code",
        "author__username",
        "content",
    )