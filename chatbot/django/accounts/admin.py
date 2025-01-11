# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

# from .models import CustomUser


# class CustomUserAdmin(DjangoUserAdmin):
#     list_display = ["email", "is_superuser", "is_active", "last_login"]
#     list_filter = ["last_login"]
#     search_fields = ["email"]

#     ordering = ["email"]

#     add_fieldsets = (
#         (
#             None,
#             {"fields": ("email", "password1", "password2")},
#         ),
#     )

#     fieldsets = (
#         (
#             None,
#             {
#                 "fields": (
#                     "email",
#                     "password",
#                     "is_active",
#                     "last_login",
#                 )
#             },
#         ),
#         (
#             "Permissions",
#             {
#                 "fields": (
#                     "is_staff",
#                     "is_superuser",
#                     "groups",
#                     "user_permissions",
#                 )
#             },
#         ),
#         ("Other", {"fields": ("date_joined",)}),
#     )


# admin.site.register(CustomUser, CustomUserAdmin)
