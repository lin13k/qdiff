from django.db import models

# Create your models here.


class Task(models.Model):
    """
    Task model is the main model for qdiff.
    It represent each diff task.
    """

    # Brief summary for the task, input by user
    summary = models.TextField(
        max_length=100,
        null=True, blank=True)

    # Data source can be a masked database configuration or csv file location
    # Masked means the password and user name is removed
    left_source = models.TextField(max_length=1000)

    # If left data source is database,
    # This field will contain query sql
    left_query_sql = models.TextField(
        max_length=2000,
        null=True, blank=True)

    # This stores which fields should be ignored
    # For example, the ID field should be ignored when doing comparison
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

    # task create datetime
    start_datetime = models.DateTimeField(
        auto_now_add=True,
        null=True, blank=True)

    # task finish datetime
    end_datetime = models.DateTimeField(
        auto_now=True,
        null=True, blank=True)

    # who create this task, currently not used
    owner = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, related_name='tasks')

    # rule set to resolve the difference, currently not used
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

    # status of the task
    status = models.CharField(
        max_length=2, choices=STATUS_OF_TASK_CHOICES, default='PN')

    # brief result of the task
    result = models.TextField(
        max_length=500, null=True, blank=True)

    # detail result of the task
    result_detail = models.TextField(
        max_length=2000, null=True, blank=True)

    # total rows count
    total_left_count = models.IntegerField(
        null=True)
    total_right_count = models.IntegerField(
        null=True)

    # total different rows count
    left_diff_count = models.IntegerField(
        null=True)
    right_diff_count = models.IntegerField(
        null=True)


class ConflictRecord(models.Model):
    """
    ConflictRecord is the model for linking Tasks with dynamic raw tables
    """
    # table name of the ConflictRecord
    # the name is defined by setting, CONFLICT_TABLE_NAME_FORMAT
    raw_table_name = models.TextField(max_length=100)

    # which task these records belongs to
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='tasks')
    POSITION_IN_TASK_LEFT = 'LF'
    POSITION_IN_TASK_RIGHT = 'RT'
    POSITION_IN_TASK_CHOICES = (
        (POSITION_IN_TASK_LEFT, 'Left'),
        (POSITION_IN_TASK_RIGHT, 'Right'),

    )

    # which position do these record come from,
    # left or right source in the task
    position = models.CharField(
        max_length=2, choices=POSITION_IN_TASK_CHOICES)


class RuleSet(models.Model):
    """
    This model is defining the rules to resolve the conflict records
    This is not used currently
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
    '''This model is for the report generation layer'''

    # which generator should be invoked, see reports.py
    report_generator = models.CharField(max_length=256)

    # parameters for the generator
    parameters = models.CharField(max_length=256, blank=True, null=True)

    # generated file
    file = models.FileField(upload_to='gen_reports', blank=True, null=True)

    # which task this report belongs to
    task = models.ForeignKey(
        'qdiff.task',
        on_delete=models.CASCADE,
        related_name='reports')
