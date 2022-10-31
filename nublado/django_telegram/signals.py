from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import GroupMember
from group_points.models import GroupMemberPoints


# Create an associated GroupMemberPoints object when a GroupMember object is created.
@receiver(post_save, sender=GroupMember)
def create_group_member_points(sender, instance=None, created=False, **kwargs):
    if created:
        group_member_points = GroupMemberPoints(group_member=instance)
        group_member_points.save()