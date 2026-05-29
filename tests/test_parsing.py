"""Unit tests for file parsing."""

import io

import pytest
from openpyxl import Workbook

from app.services.parsing import ParsingError, parse_file

CSV_BYTES = b"external_id,email,amount\n1,a@b.com,10\n2,c@d.com,20\n"


def test_parse_csv():
    rows = parse_file("data.csv", CSV_BYTES)
    assert len(rows) == 2
    assert rows[0] == {"external_id": "1", "email": "a@b.com", "amount": "10"}


def test_parse_xlsx():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["external_id", "email", "amount"])
    sheet.append([1, "a@b.com", 10])
    buffer = io.BytesIO()
    workbook.save(buffer)

    rows = parse_file("data.xlsx", buffer.getvalue())
    assert len(rows) == 1
    assert rows[0]["email"] == "a@b.com"


def test_unsupported_extension():
    with pytest.raises(ParsingError):
        parse_file("data.txt", b"x")


def test_empty_file_rejected():
    with pytest.raises(ParsingError):
        parse_file("data.csv", b"")
