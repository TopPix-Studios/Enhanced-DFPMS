from django.db import models

class Region(models.Model):
    region_id = models.AutoField(
        primary_key=True,
        verbose_name="Region ID",
        help_text="Unique identifier for the region."
    )
    region = models.CharField(
        max_length=255,
        verbose_name="Region Name",
        help_text="The name of the region."
    )

    def __str__(self):
        return self.region

    class Meta:
        verbose_name = "Region"
        verbose_name_plural = "Regions"
        ordering = ["region"]  # Alphabetical order by region name


class Province(models.Model):
    province_id = models.AutoField(
        primary_key=True,
        verbose_name="Province ID",
        help_text="Unique identifier for the province."
    )
    province = models.CharField(
        max_length=255,
        verbose_name="Province Name",
        help_text="The name of the province."
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        verbose_name="Region",
        help_text="The region associated with this province."
    )

    def __str__(self):
        return self.province

    class Meta:
        verbose_name = "Province"
        verbose_name_plural = "Provinces"
        ordering = ["province"]  # Alphabetical order by province name


class City(models.Model):
    city_id = models.AutoField(
        primary_key=True,
        verbose_name="City ID",
        help_text="Unique identifier for the city."
    )
    city = models.CharField(
        max_length=255,
        verbose_name="City Name",
        help_text="The name of the city."
    )
    province = models.ForeignKey(
        Province,
        on_delete=models.CASCADE,
        verbose_name="Province",
        help_text="The province associated with this city."
    )

    def __str__(self):
        return self.city

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"
        ordering = ["city"]  # Alphabetical order by city name


class Barangay(models.Model):
    barangay_id = models.AutoField(
        primary_key=True,
        verbose_name="Barangay ID",
        help_text="Unique identifier for the barangay."
    )
    barangay = models.CharField(
        max_length=255,
        verbose_name="Barangay Name",
        help_text="The name of the barangay."
    )
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        verbose_name="City",
        help_text="The city associated with this barangay."
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Latitude",
        help_text="Latitude coordinate of the barangay."
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Longitude",
        help_text="Longitude coordinate of the barangay."
    )
    fun_fact = models.CharField(
        max_length=255,
        null=True,              # Allows NULL in the database
        blank=True,             # Allows the field to be empty in forms
        default="Fun Fact",     # Default value if nothing is provided
        verbose_name="Fun Fact",
        help_text="A fun fact about the barangay."
    )


    def __str__(self):
        return self.barangay

    class Meta:
        verbose_name = "Barangay"
        verbose_name_plural = "Barangays"
        ordering = ["barangay"]  # Alphabetical order by barangay name


class Country(models.Model):
    country_id = models.AutoField(
        primary_key=True,
        verbose_name="Country ID",
        help_text="Unique identifier for the country."
    )
    country = models.CharField(
        max_length=255,
        verbose_name="Country Name",
        help_text="The name of the country."
    )

    def __str__(self):
        return self.country

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ["country"]  # Alphabetical order by country name
