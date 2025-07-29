from ._task import ForecastingTask
from .triple_barrier import TripleBarrierTask
from .ndays_distribution import NDaysDistributionTask

from typing import Dict
from enum import Enum

class AvailableTaskTemplate(Enum):
    TRIPLE_BARRIER_TASK = TripleBarrierTask
    NDAYS_DISTRIBUTION_TASK = NDaysDistributionTask

class ForecastingTaskFactory:

    @staticmethod
    def create_task(task_template: AvailableTaskTemplate, task_id: str, metadata: Dict) -> ForecastingTask:
        task_class = task_template.value
        task = task_class(task_id)
        task.load_metadata(metadata)
        return task