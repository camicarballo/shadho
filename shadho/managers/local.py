"""
"""
from collections import deque
import json
import time
import uuid


class TaskFailureError(Exception):
    """Raised when a task fails for any reason."""
    def __init__(self, e):
        super(TaskFailureError, self).__init__(str(e))


class LocalManager(object):
    """Task manager for running tasks on the local machine.

    Parameters
    ----------
    opt_value : str
        The value to search for in a task result.

    Attributes
    ----------
    tasks : list of LocalTask
        The tasks to run locally.
    opt_value : str
        The value to search for in a task result.
    """
    def __init__(self, opt_value):
        self.tasks = deque()
        self.opt_value = opt_value
        self.tasks_submitted = 0

    def empty(self):
        return len(self.tasks) == 0

    def add_task(self, cmd, tag, params, files=None, resource=None,
                 value=None):
        """Add a task to the task list.

        Parameters
        ----------
        cmd : str
            The command to run on the remote worker, e.g. ``echo hello`` or
            ``python script.py``.
        tag : str
            The tag to give this task.
        params : dict
            The hyperparameter value to supply to the task.
        files : optional
            Placeholder to match other managers.
        resource : optional
            Placeholder to match other managers.
        value : optional
            Placeholder to match other managers.
        """
        task = LocalTask(cmd, tag, params)
        self.tasks.append(task)
        self.tasks_submitted += 1

    def run_task(self):
        """Run the next task on the task list and return its result.

        This function chooses the next task to run from the task list and
        attempts to run it. Any encountered errors are repoted to the user.

        Returns
        -------
        result_id : str
            The id of the database entry representing this result.
        cc_id : str
            The id of the compute class that ran this result.
        loss : float
            Only returned on success. The value being optimized.
        results : dict
            Only returned on success. Other results returned by the task.
        """
        try:
            task = self.tasks.popleft()
        except IndexError:
            task = None
        if task is not None:
            result = None
            ret = [task.tag]
            #print(ret)
            try:
                result = task.run()
                #print(result)
                if result is not None:
                    if isinstance(result, dict):
                        ret.append(result[self.opt_value])
                        ret.append(result)
                    elif isinstance(result, float):
                        ret.append(result)
                        ret.append({self.opt_value: result})
                    else:
                        raise ValueError
            except TaskFailureError as e:
                print("Error: Task failed due to the following error:")
                print(str(e))
            except ValueError:
                print("Error: Invalid task result {}".format(result))
                print("Task results must be of type float")
                print("or dict with a float in key {}".format(self.opt_val))
            except KeyError:
                print("Error: Result {} does not contain the value {} to optimize."
                      .format(result, self.opt_val))
                print("Please check your function to ensure that it returns the")
                print("correct value.")

            return tuple(ret) if result is not None else None


class LocalTask(object):
    """A task to run using supplied hyperparameters.

    Parameters
    ----------
    cmd : function or callable object
        The command to run.
    tag : str
        Tag with metadata about the task.
    params : dict
        The parameters to supply to the task.

    Attributes
    ----------
    cmd : function or callable object
        The command to run.
    tag : str
        Tag with metadata about the task.
    params : dict
        The parameters to supply to the task.
    """
    def __init__(self, cmd, tag, params):
        self.id = str(uuid.uuid4())
        self.cmd = cmd
        self.tag = tag
        self.params = params

    def run(self):
        """Run the task and return the result.

        Returns
        -------
        result : float or dict
            The result of the task, either a float representing the loss or a
            dictionary containing the loss and (possibly) other results.
        """
        try:
            return self.cmd(self.params)
        except Exception as e:
            raise TaskFailureError(str(e))
