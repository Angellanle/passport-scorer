from account.models import Community, EthAddressField
from django.db import models


class Passport(models.Model):
    address = EthAddressField(null=True, blank=False, max_length=100, db_index=True)
    community = models.ForeignKey(
        Community, related_name="passports", on_delete=models.CASCADE, null=True
    )
    requires_calculation = models.BooleanField(
        null=True,
        help_text="This flag indicates that this passport requires calculation of the score. The score calculation task shall skip calculation unless this flag is set.",
    )

    class Meta:
        unique_together = ["address", "community"]

    def __str__(self):
        return f"Passport #{self.id}, address={self.address}, community_id={self.community_id}"


class Stamp(models.Model):
    passport = models.ForeignKey(
        Passport,
        related_name="stamps",
        on_delete=models.CASCADE,
        null=True,
        db_index=True,
    )
    hash = models.CharField(null=False, blank=False, max_length=100, db_index=True)
    provider = models.CharField(
        null=False, blank=False, default="", max_length=256, db_index=True
    )
    credential = models.JSONField(default=dict)

    def __str__(self):
        return f"Stamp #{self.id}, hash={self.hash}, provider={self.provider}, passport={self.passport_id}"

    class Meta:
        unique_together = ["hash", "passport"]


class Score(models.Model):
    class Status:
        PROCESSING = "PROCESSING"
        DONE = "DONE"
        ERROR = "ERROR"

    STATUS_CHOICES = [
        (Status.PROCESSING, Status.PROCESSING),
        (Status.DONE, Status.DONE),
        (Status.ERROR, Status.ERROR),
    ]

    passport = models.ForeignKey(
        Passport, on_delete=models.PROTECT, related_name="score", unique=True
    )
    score = models.DecimalField(null=True, blank=True, decimal_places=9, max_digits=18)
    last_score_timestamp = models.DateTimeField(default=None, null=True, blank=True)
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=20, null=True, default=None, db_index=True
    )
    error = models.TextField(null=True, blank=True)
    evidence = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Score #{self.id}, score={self.score}, last_score_timestamp={self.last_score_timestamp}, status={self.status}, error={self.error}, evidence={self.evidence}, passport_id={self.passport_id}"
