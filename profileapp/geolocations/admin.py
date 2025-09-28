from django.contrib import admin
from .models import Region, Province, City, Barangay, Country
import csv
from django import forms
from django.contrib import messages
from io import TextIOWrapper
from django.shortcuts import render


# Individual Admin Classes with CSV Import Action
class RegionAdmin(admin.ModelAdmin):
    list_display = ('region_id', 'region')
    search_fields = ('region',)
   


class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('province_id', 'province', 'region')
    search_fields = ('province',)
    list_filter = ('region',)

class CityAdmin(admin.ModelAdmin):
    list_display = ('city_id', 'city', 'province')
    search_fields = ('city',)
    list_filter = ('province',)
   

class BarangayAdmin(admin.ModelAdmin):
    list_display = ('barangay_id', 'barangay', 'city', 'latitude', 'longitude', 'fun_fact')
    search_fields = ('barangay',)
    list_filter = ('city',)
   

class CountryAdmin(admin.ModelAdmin):
    list_display = ('country_id', 'country')
    search_fields = ('country',)
   

# Register Admin Classes
admin.site.register(Region, RegionAdmin)
admin.site.register(Province, ProvinceAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Barangay, BarangayAdmin)
admin.site.register(Country, CountryAdmin)
