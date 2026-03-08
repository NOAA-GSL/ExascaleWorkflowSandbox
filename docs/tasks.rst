Tasks
=====

Chiltepin provides decorators to define workflow tasks that can be executed on
configured resources. Tasks are the fundamental units of work in a Chiltepin workflow.

.. note::
   Chiltepin's task decorators are thin wrappers around Parsl's ``@python_app``,
   ``@bash_app``, and ``@join_app`` decorators. Chiltepin adds two key capabilities:

   1. **Method decoration**: Support for decorating class methods that reference ``self``
   2. **Dynamic resource selection**: Ability to choose the execution resource at runtime
      via the ``executor`` parameter

   For more information about Parsl's execution model and features, see the
   `Parsl documentation <https://parsl.readthedocs.io/>`_.

Overview
--------

Chiltepin offers three task decorators:

- **@python_task**: Execute Python functions as workflow tasks
- **@bash_task**: Execute shell commands as workflow tasks
- **@join_task**: Coordinate multiple tasks without blocking workflow execution

When you decorate a function with one of these decorators, it becomes a workflow task
that can be submitted for execution on any configured resource. The function itself
defines *what* to execute, while the ``executor`` parameter at call time specifies
*where* to execute it.

Python Tasks
------------

The ``@python_task`` decorator transforms a Python function into a workflow task.
The function will be serialized and executed on the specified resource.

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   from chiltepin.tasks import python_task
   
   @python_task
   def hello_world():
       return "Hello from a Chiltepin task!"
   
   # Call the task and specify where to run it
   future = hello_world(executor=["my-resource"])
   result = future.result()  # Wait for completion and get result
   print(result)  # "Hello from a Chiltepin task!"

Tasks with Arguments
^^^^^^^^^^^^^^^^^^^^

Python tasks can accept both positional and keyword arguments:

.. code-block:: python

   @python_task
   def add_numbers(a, b, multiply_by=1):
       return (a + b) * multiply_by
   
   # Use positional arguments
   future1 = add_numbers(5, 3, executor=["compute"])
   print(future1.result())  # 8
   
   # Use keyword arguments
   future2 = add_numbers(5, 3, multiply_by=2, executor=["compute"])
   print(future2.result())  # 16

Importing Modules
^^^^^^^^^^^^^^^^^

Since tasks may execute on remote systems, import statements should be inside the
function:

.. code-block:: python

   @python_task
   def get_hostname():
       import platform
       return platform.node()
   
   @python_task
   def process_data(filename):
       import pandas as pd
       import numpy as np
       
       df = pd.read_csv(filename)
       return np.mean(df['values'])

Return Values
^^^^^^^^^^^^^

Python tasks can return any serializable Python object:

.. code-block:: python

   @python_task
   def get_list(n):
       return list(range(n))
   
   @python_task
   def get_dict(key, value):
       return {key: value}
   
   @python_task
   def get_dataframe():
       import pandas as pd
       return pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
   
   list_result = get_list(5, executor=["local"]).result()
   dict_result = get_dict("temperature", 72.5, executor=["local"]).result()
   df_result = get_dataframe(executor=["compute"]).result()

Bash Tasks
----------

The ``@bash_task`` decorator transforms a function into a shell command workflow task.
The function must return a string containing the bash commands to execute.

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   from chiltepin.tasks import bash_task
   
   @bash_task
   def echo_hello():
       return "echo 'Hello from bash!'"
   
   # Bash tasks return the exit code (0 = success)
   future = echo_hello(executor=["my-resource"])
   exit_code = future.result()
   print(exit_code)  # 0

Dynamic Command Generation
^^^^^^^^^^^^^^^^^^^^^^^^^^

Use function arguments to dynamically construct commands:

.. code-block:: python

   @bash_task
   def process_file(input_file, output_file):
       return f"cat {input_file} | sort | uniq > {output_file}"
   
   @bash_task
   def run_simulation(config_file, num_steps):
       return f"./my_simulator --config {config_file} --steps {num_steps}"
   
   exit_code = process_file("data.txt", "sorted.txt", executor=["compute"]).result()

.. warning::
   Be careful with shell injection vulnerabilities. Validate and sanitize inputs
   when constructing shell commands from user-provided data.

Capturing Output
^^^^^^^^^^^^^^^^

By default, bash tasks return the exit code. To capture stdout or stderr, use the
``stdout`` and ``stderr`` parameters that are automatically added to bash tasks:

.. code-block:: python

   @bash_task
   def get_hostname():
       return "hostname"
   
   # Capture stdout to a file
   future = get_hostname(
       executor=["compute"],
       stdout="hostname_output.txt"
   )
   exit_code = future.result()
   
   # Read the captured output
   with open("hostname_output.txt") as f:
       hostname = f.read().strip()
       print(f"Task ran on: {hostname}")

.. note::
   When running tasks on remote resources (via Globus Compute endpoints), output files
   are created on the remote system, not on the local host. You'll need to use shared
   filesystems, data staging, or file transfer mechanisms to access these files locally.

You can also capture stderr for debugging:

.. code-block:: python

   @bash_task
   def risky_command():
       return "some_command_that_might_fail"
   
   future = risky_command(
       executor=["compute"],
       stdout="output.txt",
       stderr="errors.txt"
   )

Multi-line Commands
^^^^^^^^^^^^^^^^^^^

For complex bash scripts, return multi-line strings:

.. code-block:: python

   @bash_task
   def setup_and_run(workdir):
       return f"""
       mkdir -p {workdir}
       cd {workdir}
       git clone https://github.com/example/repo.git
       cd repo
       make
       ./run_tests.sh
       """

Join Tasks
----------

The ``@join_task`` decorator creates tasks that coordinate other tasks without blocking
the main workflow. Join tasks can launch multiple subtasks and depend on their results.

Basic Usage
^^^^^^^^^^^

Join tasks call other tasks and return futures:

.. code-block:: python

   from chiltepin.tasks import python_task, join_task
   
   @python_task
   def multiply(x, factor):
       return x * factor
   
   @python_task
   def add_values(*values):
       return sum(values)
   
   @join_task
   def process_list(values, factor):
       # Launch multiple tasks in parallel
       futures = [multiply(v, factor, executor=["compute"]) for v in values]
       # Aggregate results with another task
       return add_values(*futures, executor=["compute"])
   
   # Process [1, 2, 3] with factor 2: (1*2) + (2*2) + (3*2) = 12
   result = process_list([1, 2, 3], 2).result()
   print(result)  # 12

When to Use Join Tasks
^^^^^^^^^^^^^^^^^^^^^^

Use join tasks when you need to:

1. **Fan-out operations**: Launch many parallel tasks based on input data
2. **Task dependencies**: Chain tasks where one depends on another's output
3. **Dynamic workflows**: Create tasks based on runtime conditions

Example - Processing Multiple Files:

.. code-block:: python

   @bash_task
   def process_file(filepath):
       return f"./process.sh {filepath}"
   
   @python_task
   def check_all_success(exit_codes):
       return all(code == 0 for code in exit_codes)
   
   @join_task
   def process_all_files(file_list):
       # Process all files in parallel
       futures = [process_file(f, executor=["compute"]) for f in file_list]
       # Check if all succeeded
       return check_all_success(futures, executor=["local"])
   
   files = ["data1.txt", "data2.txt", "data3.txt"]
   success = process_all_files(files).result()

Mixing Task Types
^^^^^^^^^^^^^^^^^

Join tasks can coordinate both python and bash tasks:

.. code-block:: python

   @bash_task
   def compile_code():
       return "gcc -o myapp myapp.c"
   
   @bash_task
   def run_app(input_file):
       return f"./myapp {input_file}"
   
   @python_task
   def parse_results(output_file):
       with open(output_file) as f:
           return float(f.read().strip())
   
   @join_task
   def compile_and_run(input_file):
       # First compile
       compile_future = compile_code(executor=["compute"])
       compile_future.result()  # Wait for compilation
       
       # Then run
       run_future = run_app(input_file, executor=["compute"], stdout="output.txt")
       run_future.result()  # Wait for execution
       
       # Parse results
       return parse_results("output.txt", executor=["local"])
   
   result = compile_and_run("input.dat").result()

Tasks as Class Methods
----------------------

All task decorators work with both standalone functions and class methods. This enables
object-oriented workflow design:

.. code-block:: python

   from chiltepin.tasks import python_task, bash_task
   
   class DataProcessor:
       def __init__(self, config):
           self.config = config
       
       @python_task
       def load_data(self, filename):
           import pandas as pd
           # Can access self and instance variables
           return pd.read_csv(filename, **self.config)
       
       @python_task
       def transform_data(self, df):
           # Use instance configuration
           if self.config.get('normalize'):
               return (df - df.mean()) / df.std()
           return df
       
       @bash_task
       def export_data(self, output_file):
           # self is available in method tasks
           format_type = self.config.get('export_format', 'csv')
           return f"convert_data --format {format_type} -o {output_file}"
   
   # Create instance and use tasks
   processor = DataProcessor({'normalize': True, 'export_format': 'json'})
   data = processor.load_data("input.csv", executor=["compute"]).result()
   transformed = processor.transform_data(data, executor=["compute"]).result()
   exit_code = processor.export_data("output.json", executor=["compute"]).result()

.. warning::
   **Mutable Object State**: When using class methods as tasks, be aware that mutable
   object state can lead to non-deterministic behavior in distributed systems. Each task
   captures the object state at the time it's submitted. If the object's state is modified
   between task submissions (e.g., updating ``self.config``), different tasks may see
   different states, leading to unexpected results. For best reliability, use immutable
   configuration or pass state explicitly as task arguments rather than relying on
   mutable instance variables.

Specifying Resources
--------------------

The ``executor`` parameter determines where a task runs. This parameter refers to
resource names defined in your configuration file.

.. note::
   The parameter is called ``executor`` due to Parsl's API, but it specifies which
   resource to use, not an "executor" in the traditional programming sense.

Single Resource
^^^^^^^^^^^^^^^

Specify a single resource by name:

.. code-block:: python

   @python_task
   def my_task():
       return "result"
   
   # Run on the "compute" resource from your config
   future = my_task(executor=["compute"])

Multiple Resources
^^^^^^^^^^^^^^^^^^

Provide a list of resource names to allow Parsl to choose based on availability:

.. code-block:: python

   # Can run on either resource
   future = my_task(executor=["compute", "backup-compute"])

Default Executor
^^^^^^^^^^^^^^^^

If you omit the ``executor`` parameter, the task can run on any configured resource:

.. code-block:: python

   # Can run on any available resource
   future = my_task()

.. tip::
   For production workflows, explicitly specify resources to ensure tasks run where
   intended (e.g., GPU tasks on GPU resources, MPI tasks on MPI resources).

Futures and Results
-------------------

Task calls return ``AppFuture`` objects, which represent asynchronous computation.

Getting Results
^^^^^^^^^^^^^^^

Call ``.result()`` to wait for task completion and retrieve the result:

.. code-block:: python

   @python_task
   def compute_value():
       import time
       time.sleep(2)
       return 42
   
   future = compute_value(executor=["compute"])
   print("Task submitted, doing other work...")
   
   # This blocks until the task completes
   result = future.result()
   print(f"Result: {result}")

Checking Status
^^^^^^^^^^^^^^^

Check if a task is done without blocking:

.. code-block:: python

   future = compute_value(executor=["compute"])
   
   if future.done():
       print("Task completed!")
       print(future.result())
   else:
       print("Task still running...")

Multiple Futures
^^^^^^^^^^^^^^^^

Wait for multiple tasks efficiently:

.. code-block:: python

   # Launch multiple tasks
   futures = [compute_value(executor=["compute"]) for _ in range(10)]
   
   # Wait for all to complete
   results = [f.result() for f in futures]
   print(f"All done: {results}")

Exception Handling
^^^^^^^^^^^^^^^^^^

Exceptions raised in tasks are re-raised when calling ``.result()``:

.. code-block:: python

   @python_task
   def failing_task():
       raise ValueError("Something went wrong!")
   
   future = failing_task(executor=["compute"])
   
   try:
       result = future.result()
   except ValueError as e:
       print(f"Task failed: {e}")

File and Data Handling
----------------------

Working with Files
^^^^^^^^^^^^^^^^^^

Tasks can read and write files, but file paths must be accessible from the resource
where the task runs:

.. code-block:: python

   @python_task
   def process_file(input_path, output_path):
       with open(input_path) as f:
           data = f.read()
       
       processed = data.upper()
       
       with open(output_path, 'w') as f:
           f.write(processed)
       
       return output_path

.. warning::
   When running on remote resources via Globus Compute, ensure files are accessible
   on the remote system. You may need to stage files or use shared filesystems.

Data Transfer Between Endpoints
""""""""""""""""""""""""""""""""

For moving data between Globus Transfer endpoints, Chiltepin provides specialized data
transfer and deletion tasks that can be incorporated into your workflows:

.. code-block:: python

   from chiltepin.data import transfer_task, delete_task
   from chiltepin.tasks import python_task

   @python_task
   def process_file(transfer_complete, input_path):
       # transfer_complete is a boolean we can check or ignore
       # The important part is passing it creates a dependency
       with open(input_path) as f:
           data = f.read()
       return len(data)

   # Transfer data between Globus Transfer endpoints
   transfer = transfer_task(
       src_ep="my-source-endpoint",
       dst_ep="my-dest-endpoint",
       src_path="/data/input.dat",
       dst_path="/scratch/input.dat",
       executor=["local"]
   )

   # Process the transferred data (waits for transfer by passing its future)
   result = process_file(transfer, "/scratch/input.dat", executor=["compute"])

   # Clean up after processing
   cleanup = delete_task(
       src_ep="my-dest-endpoint",
       src_path="/scratch/input.dat",
       executor=["local"],
       inputs=[result]  # Waits for processing to complete
   )
   cleanup.result()

These tasks operate on Globus **Transfer endpoints** (which are different from
Globus Compute endpoints used for execution). See :doc:`data` for comprehensive
documentation on data transfer and deletion tasks.

Passing Data Between Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pass data directly through futures:

.. code-block:: python

   @python_task
   def generate_data(n):
       return list(range(n))
   
   @python_task
   def sum_data(data):
       return sum(data)
   
   # Data flows through futures
   data_future = generate_data(100, executor=["compute"])
   sum_future = sum_data(data_future, executor=["compute"])
   result = sum_future.result()

For large data, consider files or data staging strategies.

Advanced Topics
---------------

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

Access environment variables in tasks:

.. code-block:: python

   @python_task
   def get_user():
       import os
       return os.environ.get('USER', 'unknown')
   
   @bash_task
   def get_user_bash():
       return "echo ${USER:-unknown}"

Task Dependencies
^^^^^^^^^^^^^^^^^

Create task dependencies to ensure tasks execute in the correct order. There are
two primary methods for establishing dependencies between tasks.

Passing Futures as Arguments
"""""""""""""""""""""""""""""

The most common approach is to pass a future from one task as an argument to another:

.. code-block:: python

   @python_task
   def step1():
       return "result1"
   
   @python_task
   def step2(input_data):
       return f"processed_{input_data}"
   
   @python_task
   def step3(input_data):
       return f"final_{input_data}"
   
   # Chain tasks - data flows through futures
   future1 = step1(executor=["compute"])
   future2 = step2(future1, executor=["compute"])  # Waits for future1
   future3 = step3(future2, executor=["compute"])  # Waits for future2
   
   final_result = future3.result()

Using the inputs Parameter
"""""""""""""""""""""""""""

For dependencies where you don't need to pass data between tasks, use the ``inputs``
parameter. This is automatically supported by all Chiltepin task decorators
(via Parsl's underlying implementation):

.. code-block:: python

   from chiltepin.data import delete_task, transfer_task
   from chiltepin.tasks import python_task

   # Stage data to compute resource
   stage = transfer_task(
       src_ep="laptop",
       dst_ep="hpc-scratch",
       src_path="/data/input.dat",
       dst_path="/scratch/input.dat",
       executor=["local"]
   )

   # Process the data - waits for transfer without passing its result
   @python_task
   def process_data(filepath):
       with open(filepath) as f:
           return len(f.read())

   result = process_data("/scratch/input.dat", executor=["compute"], inputs=[stage])

   # Clean up - waits for processing to complete
   cleanup = delete_task(
       src_ep="hpc-scratch",
       src_path="/scratch/input.dat",
       executor=["local"],
       inputs=[result]
   )

The ``inputs`` parameter accepts a list of futures that must complete before the task
starts. This is particularly useful for:

- Ensuring files are transferred before processing begins
- Coordinating cleanup operations after processing completes
- Creating dependencies when you don't need to pass data between tasks
- Coordinating multiple independent prerequisites

Multiple Dependencies
"""""""""""""""""""""

You can combine both approaches and specify multiple dependencies:

.. code-block:: python

   @python_task
   def task_a():
       return "data_a"

   @python_task
   def task_b():
       return "data_b"

   @python_task
   def task_c():
       # Just needs to wait, doesn't use the result
       pass

   @python_task
   def combine(data1, data2):
       return f"{data1}_{data2}"

   a = task_a(executor=["compute"])
   b = task_b(executor=["compute"])
   c = task_c(executor=["compute"])

   # Combine waits for a and b (via arguments) and c (via inputs)
   result = combine(a, b, executor=["compute"], inputs=[c])

.. tip::
   **Avoid premature .result() calls**: In this example, notice that ``.result()`` is only
   called once at the very end. By passing futures directly as arguments instead of calling
   ``.result()`` immediately, you allow Parsl to manage task dependencies automatically and
   schedule tasks as soon as their dependencies complete. This maximizes parallelism.

   **Bad practice** (blocks unnecessarily):

   .. code-block:: python

      result1 = step1(executor=["compute"]).result()  # Blocks here
      result2 = step2(result1, executor=["compute"]).result()  # Blocks here
      result3 = step3(result2, executor=["compute"]).result()  # Blocks here

   **Good practice** (maximizes parallelism):

   .. code-block:: python

      future1 = step1(executor=["compute"])
      future2 = step2(future1, executor=["compute"])  # Scheduled, doesn't block
      future3 = step3(future2, executor=["compute"])  # Scheduled, doesn't block
      result = future3.result()  # Only block when you need the final result

Timeout Handling
^^^^^^^^^^^^^^^^

Handle long-running tasks with timeouts:

.. code-block:: python

   from concurrent.futures import TimeoutError
   
   @python_task
   def long_task():
       import time
       time.sleep(100)
       return "done"
   
   future = long_task(executor=["compute"])
   
   try:
       result = future.result(timeout=10)  # Wait max 10 seconds
   except TimeoutError:
       print("Task timed out")

Retry Logic
^^^^^^^^^^^

Implement retry logic for unreliable tasks:

.. code-block:: python

   def run_with_retry(task_func, *args, max_retries=3, **kwargs):
       for attempt in range(max_retries):
           try:
               future = task_func(*args, **kwargs)
               return future.result()
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               print(f"Attempt {attempt + 1} failed: {e}, retrying...")

Best Practices
--------------

1. **Keep tasks pure**: Avoid side effects when possible. Tasks should transform inputs
   to outputs predictably.

2. **Import inside tasks**: Always import modules inside task functions, not at the
   module level, to ensure imports work on remote systems.

3. **Specify resources explicitly**: Use the ``executor`` parameter to control where
   tasks run, especially for resource-specific requirements (GPU, MPI, etc.).

4. **Handle errors gracefully**: Wrap ``.result()`` calls in try-except blocks for
   production workflows.

5. **Use join tasks for coordination**: Don't block the main thread waiting for
   results. Let join tasks coordinate dependencies.

6. **Validate bash commands**: Sanitize inputs when constructing bash commands to
   avoid shell injection vulnerabilities.

7. **Use descriptive task names**: Function names should clearly indicate what the
   task does for easier debugging.

Common Patterns
---------------

Map-Reduce
^^^^^^^^^^

.. code-block:: python

   @python_task
   def map_task(item):
       return item ** 2
   
   @python_task
   def reduce_task(results):
       return sum(results)
   
   @join_task
   def map_reduce(items):
       # Map phase
       futures = [map_task(item, executor=["compute"]) for item in items]
       # Reduce phase
       return reduce_task(futures, executor=["compute"])
   
   result = map_reduce([1, 2, 3, 4, 5]).result()  # 55

Pipeline Processing
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   @python_task
   def stage1(data):
       return data * 2
   
   @python_task
   def stage2(data):
       return data + 10
   
   @python_task
   def stage3(data):
       return data ** 2
   
   # Create pipeline
   data1 = stage1(5, executor=["compute"])
   data2 = stage2(data1, executor=["compute"])
   result = stage3(data2, executor=["compute"]).result()  # ((5*2)+10)^2 = 400

Parameter Sweep
^^^^^^^^^^^^^^^

.. code-block:: python

   @python_task
   def run_experiment(param1, param2):
       # Run simulation with parameters
       result = param1 * param2
       return {"params": (param1, param2), "result": result}
   
   # Sweep over parameter space
   futures = []
   for p1 in [1, 2, 3]:
       for p2 in [10, 20, 30]:
           future = run_experiment(p1, p2, executor=["compute"])
           futures.append(future)
   
   # Collect all results
   results = [f.result() for f in futures]

See Also
--------

- :doc:`quickstart` - Quick introduction to tasks in a complete workflow
- :doc:`configuration` - Configuring resources where tasks execute
- :doc:`api` - Full API reference including task decorator signatures

