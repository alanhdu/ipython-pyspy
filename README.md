# ipython-pyspy

This is a small IPython cell magic to automatically run
[py-spy](https://github.com/benfred/py-spy) on some in-line
code.

This assumes that you have permissions setup to run `py-spy` as non-root (see
[discussion
here](https://github.com/benfred/py-spy?tab=readme-ov-file#when-do-you-need-to-run-as-sudo)).


## Usage

First, you need to register the extension:

```python
%load_ext ipython_pyspy
```

Then, you can profile an arbitrary cell like:

```python
%%py_spy_record --native  # supports subset of `py-spy record`'s flags

run_my_expensive_function()
```

This will automatically generate a flamegraph SVG for you.
