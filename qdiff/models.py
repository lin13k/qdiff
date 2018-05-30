from django.db import models

# Create your models here.


class Task(models.Model):
    """
    Task model is the main model for qdiff.
    It represent each diff task.
    """
    summary = models.TextField(
        max_length=100,
        null=True, blank=True)
    left_source = models.TextField(max_length=1000)
    left_query_sql = models.TextField(
        max_length=2000,
        null=True, blank=True)
    right_source = models.TextField(max_length=1000)
    right_query_sql = models.TextField(
        max_length=2000,
        null=True, blank=True)
    start_datetime = models.DateTimeField(
        auto_now_add=True,
        null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, related_name='tasks')
    resolving_ruleset = models.ForeignKey(
        'RuleSet', on_delete=models.SET_NULL,
        null=True, related_name='tasks')


class ConflictRecord(models.Model):
    """
    ConflictRecord is the model for linking Tasks with dynamic raw tables
    """
    raw_table_name = models.TextField(max_length=100)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='tasks')
    POSITION_IN_TASK_CHOICES = (
        ('LF', 'Left'),
        ('RT', 'Right'),

    )
    position = models.CharField(
        max_length=2, choices=POSITION_IN_TASK_CHOICES)


class RuleSet(models.Model):
    """
    This model is defining the rules to resolve the conflict records
    """
    summary = models.TextField(
        max_length=100,
        null=True, blank=True)
    '''
    this field defines where to write the resolved result
    '''
    data_target = models.TextField(max_length=1000)

    JOIN_TYPE_IN_RULESET_CHOICES = (
        ('LF', 'Left'),
        ('RT', 'Right'),
        ('BT', 'Both'),
    )
    join_type = models.CharField(
        max_length=2, choices=JOIN_TYPE_IN_RULESET_CHOICES)
    conditions = models.TextField(max_length=2000)




