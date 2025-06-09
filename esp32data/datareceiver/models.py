from django.db import models

class Measurement(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    humidity = models.FloatField()
    temperature = models.FloatField()
    current = models.FloatField()
    voltage = models.FloatField()
    energy = models.FloatField()
    local=models.TextField(default="")

    def __str__(self):
        return f"{self.timestamp} | Temp: {self.temperature} °C | Humidity: {self.humidity}%"