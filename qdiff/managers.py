class TaskManager:
    """
    This class will manage the whole process of a comparison task
    It handles following jobs:
            1. setup table for conflicted results
            2. field comparison
            3. value comparison
            4. provide information for report generator
                4.1 field information
                4.2 task information( or report generator get the data from db)
            5. set the task as running before run
            6. set the task as completed/error after run
    """

    def __init__(self):
        pass
