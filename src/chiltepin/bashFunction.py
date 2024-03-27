from typing import Any, Dict

import parsl.app.errors as pe


class BashFunction(object):

    def __init__(
        self,
        cmd_line: str,
        stdout: str | None = None,
        stderr: str | None = None,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        walltime: float | None = None,
        rundir: str = None,  # This could be a os.Pathlike, but check windows->unix transition
        resource_specification: Dict[str, Any] | None = None,
    ):
        self.cmd_line = cmd_line
        self.stdout = stdout
        self.stderr = stderr
        self.walltime = walltime
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.rundir = rundir
        self.resource_specification = resource_specification

    @property
    def __name__(self):
        # This is required for function registration
        return self.cmd_line

    def open_std_fd(self, fname, mode: str = "a+"):

        import os

        # fdname is 'stdout' or 'stderr'
        if fname is None:
            return None

        try:
            if os.path.dirname(fname):
                os.makedirs(os.path.dirname(fname), exist_ok=True)
            fd = open(fname, mode)
        except Exception as e:
            raise pe.BadStdStreamFile(fname, e)
        return fd

    def execute_cmd_line(self, cmd_line: str):

        import os
        import subprocess

        import parsl.app.errors as pe

        if self.rundir:
            os.makedirs(self.rundir, exist_ok=True)
            os.chdir(self.rundir)

        std_out = self.open_std_fd(self.stdout)
        std_err = self.open_std_fd(self.stderr)

        if std_err is not None:
            print(
                "--> executable follows <--\n{}\n--> end executable <--".format(
                    cmd_line
                ),
                file=std_err,
                flush=True,
            )

        returncode = None
        try:
            proc = subprocess.Popen(
                cmd_line,
                stdout=std_out,
                stderr=std_err,
                shell=True,
                executable="/bin/bash",
                close_fds=False,
            )
            proc.wait(timeout=self.walltime)
            returncode = proc.returncode

        except subprocess.TimeoutExpired:
            raise pe.AppTimeout(
                f"BashFunction exceeded walltime: {self.walltime} seconds"
            )

        except Exception as e:
            raise pe.AppException(
                f"BashFunction caught exception with returncode: {returncode}", e
            )

        if returncode != 0:
            raise pe.BashExitFailure("BashFunction", proc.returncode)

        # TODO : Add support for globs here

        missing = []
        for outputfile in self.outputs:
            fpath = outputfile.filepath

            if not os.path.exists(fpath):
                missing.extend([outputfile])

        if missing:
            raise pe.MissingOutputs(f"Missing outputs from app {func_name}", missing)

        return returncode

    def __call__(self, stdout=None, stderr=None, rundir=None, **kwargs):
        """There's potentially some weird mutability issue with stdout/stderr"""
        import copy

        self.stdout = stdout or self.stdout
        self.stderr = stderr or self.stderr
        self.rundir = rundir or self.rundir

        # Copy to avoid mutating the class vars
        format_args = copy.copy(vars(self))
        format_args.update(kwargs)
        cmd_line = self.cmd_line.format(**format_args)
        return self.execute_cmd_line(cmd_line)
