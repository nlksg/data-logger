from django.db import models


class SensorReading(models.Model):
    device_id = models.TextField()
    humidity = models.DecimalField(max_digits=5, decimal_places=2)
    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    sensor_timestamp = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return (
            f"{self.device_id} | temp={self.temperature}C "
            f"humidity={self.humidity}% @ {self.created_at.isoformat()}"
        )
