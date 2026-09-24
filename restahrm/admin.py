from django.contrib import admin
from .models import RestaurantEmployee,RestaurantFoodBillPayment,RestaurantSalaryVoucher,RestaurantLoanPayment,RestaurantAttendance,RestaurantAdvancePayment,RestaurantPayroll,RestaurantPayslip,RestaurantSalaryPayment,RestaurantAllowances,RestaurantLeave

admin.site.register(RestaurantEmployee)
admin.site.register(RestaurantSalaryVoucher)
admin.site.register(RestaurantAttendance)
admin.site.register(RestaurantAdvancePayment)
admin.site.register(RestaurantPayroll)
admin.site.register(RestaurantPayslip)
admin.site.register(RestaurantSalaryPayment)
admin.site.register(RestaurantAllowances)
admin.site.register(RestaurantLeave)
admin.site.register(RestaurantLoanPayment)
admin.site.register(RestaurantFoodBillPayment)


from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import RestaurantAttendanceLocation


@admin.register(RestaurantAttendanceLocation)
class RestaurantAttendanceLocationAdmin(admin.ModelAdmin):
    list_display = ('attendance', 'check_in_map', 'check_out_map', 'is_verified', 'verified_by', 'verified_at')
    list_filter = ('is_verified', 'attendance__date')
    search_fields = ('attendance__employee__rda_emp_name',)
    actions = ['verify_selected']

    def check_in_map(self, obj):
        if obj.check_in_latitude and obj.check_in_longitude:
            url = f"https://www.google.com/maps?q={obj.check_in_latitude},{obj.check_in_longitude}"
            return format_html('<a href="{}" target="_blank">Check-in Location</a>', url)
        return "-"
    check_in_map.short_description = "Check-in"

    def check_out_map(self, obj):
        if obj.check_out_latitude and obj.check_out_longitude:
            url = f"https://www.google.com/maps?q={obj.check_out_latitude},{obj.check_out_longitude}"
            return format_html('<a href="{}" target="_blank">Check-out Location</a>', url)
        return "-"
    check_out_map.short_description = "Check-out"

    def verify_selected(self, request, queryset):
        if not request.user.has_perm('hrm.can_verify_attendance_location'):
            self.message_user(request, "You don't have permission to verify attendance.", level='error')
            return
        updated = queryset.update(is_verified=True, verified_by=request.user, verified_at=timezone.now())
        self.message_user(request, f"{updated} record(s) verified.")
    verify_selected.short_description = "Verify selected location(s)"
    
    

from django.contrib import admin
from .models import RestaurantAttendanceAccessControl

@admin.register(RestaurantAttendanceAccessControl)
class RestaurantAttendanceAccessControlAdmin(admin.ModelAdmin):
    filter_horizontal = ('allowed_employees',)
    list_display = ('name', 'updated_at')