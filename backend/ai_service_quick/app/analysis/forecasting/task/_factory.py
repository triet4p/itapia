"""Factory module for creating forecasting tasks."""

from enum import Enum
from typing import Dict

from ._task import ForecastingTask
from .ndays_distribution import NDaysDistributionTask
from .triple_barrier import TripleBarrierTask


class AvailableTaskTemplate(Enum):
    """Enumeration of available forecasting task templates."""

    TRIPLE_BARRIER_TASK = TripleBarrierTask
    NDAYS_DISTRIBUTION_TASK = NDaysDistributionTask


class ForecastingTaskFactory:
    """Factory class for creating forecasting task instances."""

    @staticmethod
    def create_task(
        task_template: AvailableTaskTemplate, task_id: str, metadata: Dict
    ) -> ForecastingTask:
        """Create a forecasting task instance from a template.

        Args:
            task_template (AvailableTaskTemplate): The template to create the task from
            task_id (str): Unique identifier for the task
            metadata (Dict): Metadata to initialize the task with

        Returns:
            ForecastingTask: Created forecasting task instance
        """
        task_class = task_template.value
        task = task_class(task_id)
        task.load_metadata(metadata)
        return task
