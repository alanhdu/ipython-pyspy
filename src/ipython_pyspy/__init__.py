import os
import shlex
import signal
import subprocess
import tempfile
import threading

from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.display import SVG


def tail_process(proc: subprocess.Popen) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line.decode(), end="")


@magics_class
class PySpyMagic(Magics):
    # TODO: is there a way to auto-generate flags from `py-spy --help`?
    @magic_arguments()
    @argument("--rate", "-r", help="The number of samples to collect per second")
    @argument("--threads", "-t", help="The number of samples to collect per second")
    @argument(
        "--function",
        "-F",
        help="Aggregates samples by function's first line number, instead of current line number",
    )
    @argument("--nolineno", help="Do not show line numbers", action="store_true")
    @argument(
        "--gil",
        "-g",
        help="Only include traces that are holding on to the GIL",
        action="store_true",
    )
    @argument(
        "--idle",
        "-i",
        help="Include stack traces for idle threads",
        action="store_true",
    )
    @argument("--subprocesses", "-s", help="Profile subprocesses of the notebook")
    @argument(
        "--native",
        "-n",
        help="Collect stack traces from native extensions written in Cython, C or C++",
        action="store_true",
    )
    @argument(
        "--nonblocking",
        help="Don't pause the python process when collecting samples. Setting this option will reduce the performance impact of sampling, but may lead to inaccurate results",
        action="store_true",
    )
    @argument("--output", "-o", help="Output file name")
    @cell_magic
    def py_spy_record(self, line, cell):
        """Run `py-spy record` on the notebook as it runs the cell

        Automatically generates a flamegraph for profiling purposes. Supports
        a (subset) of flags that `py-spy record` does.
        """

        args = parse_argstring(self.py_spy_record, line)

        # TODO: support speedscope?
        if args.output is None:
            args.output = tempfile.mkstemp(suffix=".svg")[1]

        cmd = ["py-spy", "record", "--pid", str(os.getpid())]
        for k, v in vars(args).items():
            if v is True:
                cmd.append(f"--{k}")
            elif v is not None and v is not False:
                cmd += [f"--{k}", v]
        shell = shlex.join(cmd)

        print(f"RUNNING `{shell}`")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        thread = threading.Thread(target=tail_process, args=(proc,))
        try:
            thread.start()
            self.shell.run_cell(cell)
            proc.send_signal(signal.SIGINT)

            proc.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            pass
        finally:
            proc.kill()
            thread.join()  # Process is killed, so thread will auto-exit with an exception

        if proc.returncode != 0:
            assert proc.stderr is not None
            msg = f"""`{shell}` failed with returncode {proc.returncode}!
STDERR:
{proc.stderr.read().decode()}
"""
            raise RuntimeError(msg)
        return SVG(filename=args.output)


def load_ipython_extension(ipython):
    ipython.register_magics(PySpyMagic)
