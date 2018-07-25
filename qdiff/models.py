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
    left_ignore_fields = models.TextField(
        max_length=1000,
        null=True, blank=True)
    right_source = models.TextField(max_length=1000)
    right_query_sql = models.TextField(
        max_length=2000,
        null=True, blank=True)
    right_ignore_fields = models.TextField(
        max_length=1000,
        null=True, blank=True)
    start_datetime = models.DateTimeField(
        auto_now_add=True,
        null=True, blank=True)
    end_datetime = models.DateTimeField(
        auto_now=True,
        null=True, blank=True)
    owner = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, related_name='tasks')
    resolving_ruleset = models.ForeignKey(
        'RuleSet', on_delete=models.SET_NULL,
        null=True, related_name='tasks')
    STATUS_OF_TASK_PENDING = 'PN'
    STATUS_OF_TASK_COMPLETED = 'CM'
    STATUS_OF_TASK_RUNNING = 'RN'
    STATUS_OF_TASK_ERROR = 'ER'
    STATUS_OF_TASK_CHOICES = (
        (STATUS_OF_TASK_PENDING, 'Pending'),
        (STATUS_OF_TASK_COMPLETED, 'Completed'),
        (STATUS_OF_TASK_RUNNING, 'Running'),
        (STATUS_OF_TASK_ERROR, 'Error'),
    )
    status = models.CharField(
        max_length=2, choices=STATUS_OF_TASK_CHOICES, default='PN')
    result = models.TextField(
        max_length=500, null=True, blank=True)
    result_detail = models.TextField(
        max_length=2000, null=True, blank=True)
    total_left_count = models.IntegerField(
        null=True)
    total_right_count = models.IntegerField(
        null=True)
    left_diff_count = models.IntegerField(
        null=True)
    right_diff_count = models.IntegerField(
        null=True)


class ConflictRecord(models.Model):
    """
    ConflictRecord is the model for linking Tasks with dynamic raw tables
    """
    raw_table_name = models.TextField(max_length=100)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='tasks')
    POSITION_IN_TASK_LEFT = 'LF'
    POSITION_IN_TASK_RIGHT = 'RT'
    POSITION_IN_TASK_CHOICES = (
        (POSITION_IN_TASK_LEFT, 'Left'),
        (POSITION_IN_TASK_RIGHT, 'Right'),

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
    JOIN_TYPE_IN_RULESET_LEFT = 'LF'
    JOIN_TYPE_IN_RULESET_RIGHT = 'RT'
    JOIN_TYPE_IN_RULESET_BOTH = 'BT'

    JOIN_TYPE_IN_RULESET_CHOICES = (
        (JOIN_TYPE_IN_RULESET_LEFT, 'Left'),
        (JOIN_TYPE_IN_RULESET_RIGHT, 'Right'),
        (JOIN_TYPE_IN_RULESET_BOTH, 'Both'),
    )
    join_type = models.CharField(
        max_length=2, choices=JOIN_TYPE_IN_RULESET_CHOICES)
    conditions = models.TextField(max_length=2000)


class Report(models.Model):
    report_generator = models.CharField(max_length=256)
    parameters = models.CharField(max_length=256, blank=True, null=True)
    file = models.FileField(upload_to='gen_reports', blank=True, null=True)
    task = models.ForeignKey(
        'qdiff.task',
        on_delete=models.CASCADE,
        related_name='reports')
