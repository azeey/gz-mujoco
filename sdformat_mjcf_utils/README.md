# Utils for converting between MJCF and SDFormat

To start development, create a python3 virtual environment, upgrade pip and
install dm-control

```
python3 -m venv path/to/venv --system-site-packages
. path/to/venv/bin/activate

pip install -U pip
pip install dm-control
```

Install `python3-ignition-math7` from the
[nightly](https://gazebosim.org/docs/all/release#type-of-releases) repo.

Build `libsdformat` from source from the `ahcorde/python/all` branch and add
the installation path to your `LD_LIBRARY_PATH` and `PYTHONPATH`.

```
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$INSTALL_DIR/lib"
export PYTHONPATH="$PYTHONPATH:$INSTALL_DIR/lib/python"
```

where `$INSTALL_DIR` is the installation directory you used when building
libsdformat.

Install the `sdformat_mjcf_utils` packages in "editable" mode

```
pip install -e path/to/sdformat_mjcf_utils
```
