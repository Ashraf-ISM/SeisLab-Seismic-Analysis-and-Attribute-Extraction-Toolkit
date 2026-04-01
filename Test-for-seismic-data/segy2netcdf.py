# -*- coding: utf-8 -*-
"""Tests for segy2netcdf.
"""

from netCDF4 import Dataset
import pytest
import segyio
import numpy as np
from netcdf_segy import segy2netcdf


# ---------------------------------------------------------
# Fixtures
# ---------------------------------------------------------

@pytest.fixture
def d_all_headers():
    return (("ShotPoint", 3), ("GroupX", 10))


@pytest.fixture
def d_mixed_headers():
    return (("ShotPoint", 3), ("ReceiverID", 10))


@pytest.fixture
def d_no_headers():
    return (("ShotID", 3), ("ReceiverID", 10))


@pytest.fixture
def dim_names1():
    return ["FieldRecord", "ReceiverID", "Time"]


@pytest.fixture
def dim_lens1():
    return [3, 10, 20]


@pytest.fixture
def rootgrp_empty(tmpdir):
    path = str(tmpdir.join("tmp.nc"))
    rootgrp = Dataset(path, "w", format="NETCDF4")
    yield rootgrp
    rootgrp.close()


@pytest.fixture
def rootgrp_dims(tmpdir, dim_names1, dim_lens1):
    path = str(tmpdir.join("tmp.nc"))
    rootgrp = Dataset(path, "w", format="NETCDF4")
    segy2netcdf._create_dimensions(dim_names1, dim_lens1, rootgrp)
    yield rootgrp
    rootgrp.close()


@pytest.fixture
def rootgrp_vars(tmpdir, dim_names1, dim_lens1):
    path = str(tmpdir.join("tmp.nc"))
    rootgrp = Dataset(path, "w", format="NETCDF4")
    segy2netcdf._create_dimensions(dim_names1, dim_lens1, rootgrp)
    segy2netcdf._create_variables(rootgrp, dim_names1, False)
    yield rootgrp
    rootgrp.close()


@pytest.fixture
def segy1():
    segy_path = "tests/testsegy1.segy"
    with segyio.open(segy_path, ignore_geometry=True) as f:
        yield f


# ---------------------------------------------------------
# Dimension Tests
# ---------------------------------------------------------

class Test_make_dim_name_len:

    def test_all_args(self, d_all_headers):
        dim_names, dim_lens = segy2netcdf._make_dim_name_len("Time", 5, d_all_headers)

        assert dim_names == ["ShotPoint", "GroupX", "Time"]
        assert dim_lens == [3, 10, 5]


    def test_no_d(self):
        dim_names, dim_lens = segy2netcdf._make_dim_name_len("Time", 5, ())

        assert dim_names == ["Time"]
        assert dim_lens == [5]


class Test_count_traces_in_user_dims:

    def test_d(self, d_all_headers):
        dims_ntraces = segy2netcdf._count_traces_in_user_dims(d_all_headers)

        assert dims_ntraces == 30


    def test_no_d(self):
        dims_ntraces = segy2netcdf._count_traces_in_user_dims(())

        assert dims_ntraces == 1


class Test_check_user_dims:

    def test_full_d(self):
        segy2netcdf._check_user_dims(30, 30)

    def test_partial_d(self):
        segy2netcdf._check_user_dims(15, 30)

    def test_no_d(self):
        segy2netcdf._check_user_dims(1, 30)

    def test_zero_d_zero_ntraces(self):
        segy2netcdf._check_user_dims(0, 0)

    def test_nondivisible_d(self):
        with pytest.raises(ValueError):
            segy2netcdf._check_user_dims(16, 30)

    def test_too_big_d(self):
        with pytest.raises(ValueError):
            segy2netcdf._check_user_dims(31, 30)

    def test_negative_d(self):
        with pytest.raises(ValueError):
            segy2netcdf._check_user_dims(-1, 30)

    def test_zero_d(self):
        with pytest.raises(ValueError):
            segy2netcdf._check_user_dims(0, 30)


# ---------------------------------------------------------
# Fill Missing Dimensions
# ---------------------------------------------------------

class Test_fill_missing_dims:

    def test_full_d(self):

        dim_names = ["ShotPoint", "GroupX", "Time"]
        dim_lens = [3, 10, 20]

        segy2netcdf._fill_missing_dims(30, 30, dim_names, dim_lens)

        assert dim_names == ["ShotPoint", "GroupX", "Time"]
        assert dim_lens == [3, 10, 20]


    def test_partial_d(self):

        dim_names = ["ShotPoint", "GroupX", "Time"]
        dim_lens = [3, 5, 20]

        segy2netcdf._fill_missing_dims(15, 30, dim_names, dim_lens)

        assert dim_names == ["Traces", "ShotPoint", "GroupX", "Time"]
        assert dim_lens == [2, 3, 5, 20]


    def test_no_d(self):

        dim_names = ["Time"]
        dim_lens = [20]

        segy2netcdf._fill_missing_dims(1, 30, dim_names, dim_lens)

        assert dim_names == ["Traces", "Time"]
        assert dim_lens == [30, 20]


# ---------------------------------------------------------
# Create Dimensions
# ---------------------------------------------------------

class Test_create_dimensions:

    def test_multiple_dims(self, rootgrp_empty, dim_names1, dim_lens1):

        segy2netcdf._create_dimensions(dim_names1, dim_lens1, rootgrp_empty)

        for name, dim in rootgrp_empty.dimensions.items():

            idx = dim_names1.index(name)

            assert dim.size == dim_lens1[idx]


# ---------------------------------------------------------
# Create Variables
# ---------------------------------------------------------

class Test_create_variables:

    def test_1(self, rootgrp_dims, dim_names1, dim_lens1):

        segy2netcdf._create_variables(rootgrp_dims, dim_names1, False)

        for name, var in rootgrp_dims.variables.items():

            if name == "Samples":

                assert var.dimensions == tuple(dim_names1)

                assert var.dtype == np.float32

                assert var.shape == tuple(dim_lens1)

            elif name in dim_names1:

                idx = dim_names1.index(name)

                assert var.dimensions == (name,)

                assert var.shape == (dim_lens1[idx],)


# ---------------------------------------------------------
# Data Validation
# ---------------------------------------------------------

def check_samples1(data):

    assert data.size == 3 * 10 * 20

    it = np.nditer(data, ["c_index"])

    while not it.finished:

        assert np.isclose(it[0], it.index + 123.456, atol=1e-4)

        it.iternext()


# ---------------------------------------------------------
# Copy Data
# ---------------------------------------------------------

class Test_copy_data:

    def test_copy1(self, segy1, rootgrp_vars, dim_names1, dim_lens1):

        segy2netcdf._copy_data(

            segy1,
            rootgrp_vars.variables.values(),
            dim_names1,
            dim_lens1,
            False,
        )

        assert "Samples" in rootgrp_vars.variables


# ---------------------------------------------------------
# Full SEG-Y → NetCDF Conversion
# ---------------------------------------------------------

class Test_segy2netcdf:

    def test_conversion(self, tmpdir, dim_names1, dim_lens1):

        d = tuple([(x, y) for x, y in zip(dim_names1[:-1], dim_lens1[:-1])])

        netcdf_path = str(tmpdir.join("tmp.nc"))

        segy2netcdf.segy2netcdf(
            "tests/testsegy1.segy",
            netcdf_path,
            "Time",
            d,
            False,
            False,
        )

        rootgrp = Dataset(netcdf_path, "r")

        assert "Samples" in rootgrp.variables

        rootgrp.close()