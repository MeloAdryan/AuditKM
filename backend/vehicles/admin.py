from django.contrib import admin 
from . models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "plate",
        "brand",
        "model",
        "year",
        "current_km",
        "status",
    )
    
    search_fields = (
      "plate",
      "brand",
      "model",
      )
    
    list_filter = (
      "status",
      "brand",
      )
    
    readonly_fields = (
      "created_at",
      "updated_at",
      )
    
    ordering = ("plate",)
    
    def has_delete_permission(self, request, obj=None):
        return False