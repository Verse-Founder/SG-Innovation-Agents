"""
tests/test_data_masker.py
数据脱敏测试
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.data_masker import (
    mask_name, mask_phone, mask_address, mask_id_number,
    hash_patient_id, mask_report_data,
)


class TestMaskFunctions:
    def test_mask_name(self):
        assert mask_name("张三丰") == "张**"
        assert mask_name("A") == "*"
        assert mask_name("") == ""

    def test_mask_phone(self):
        assert mask_phone("13812345678") == "138****5678"
        assert mask_phone("") == "***"

    def test_mask_address(self):
        assert mask_address("新加坡乌节路123号") == "新加坡乌***"
        assert mask_address("") == "***"

    def test_mask_id_number(self):
        assert mask_id_number("S1234567A") == "S***567A"

    def test_hash_patient_id(self):
        h = hash_patient_id("patient_001")
        assert len(h) == 16
        assert hash_patient_id("patient_001") == h  # consistent


class TestMaskReportData:
    def test_masks_sensitive_fields(self):
        data = {
            "patient_name": "张三",
            "phone": "13812345678",
            "blood_glucose": 6.5,
        }
        masked = mask_report_data(data)
        assert masked["patient_name"] == "张*"
        assert masked["phone"] == "138****5678"
        assert masked["blood_glucose"] == 6.5  # non-sensitive unchanged

    def test_nested_masking(self):
        data = {
            "profile": {
                "name": "李四",
                "address": "北京市朝阳区",
            },
            "glucose": 7.0,
        }
        masked = mask_report_data(data)
        assert masked["profile"]["name"] == "李*"
        assert masked["profile"]["address"] == "北京市朝***"

    def test_list_in_data(self):
        data = {
            "contacts": [
                {"name": "王五", "phone": "13900001111"},
            ],
        }
        masked = mask_report_data(data)
        assert masked["contacts"][0]["name"] == "王*"
