"""
engine/data_masker.py
数据脱敏 — 患者敏感信息自动脱敏
"""
import re
import hashlib


def mask_name(name: str) -> str:
    """姓名脱敏：保留第一个字，其余用 *"""
    if not name:
        return ""
    if len(name) <= 1:
        return "*"
    return name[0] + "*" * (len(name) - 1)


def mask_phone(phone: str) -> str:
    """手机号脱敏：保留前3后4"""
    if not phone or len(phone) < 7:
        return "***"
    return phone[:3] + "****" + phone[-4:]


def mask_address(address: str) -> str:
    """地址脱敏：只保留城市级别"""
    if not address:
        return "***"
    # 简单处理：取前4个字符
    return address[:4] + "***"


def mask_id_number(id_number: str) -> str:
    """身份证/NRIC 脱敏"""
    if not id_number or len(id_number) < 4:
        return "***"
    return id_number[0] + "***" + id_number[-4:]


def hash_patient_id(patient_id: str) -> str:
    """患者 ID 哈希（用于日志存储）"""
    return hashlib.sha256(patient_id.encode()).hexdigest()[:16]


def mask_report_data(report_data: dict) -> dict:
    """对报告数据中的敏感字段进行脱敏"""
    masked = report_data.copy()

    sensitive_keys = {
        "name": mask_name,
        "patient_name": mask_name,
        "phone": mask_phone,
        "mobile": mask_phone,
        "address": mask_address,
        "id_number": mask_id_number,
        "nric": mask_id_number,
    }

    def _mask_dict(d: dict) -> dict:
        result = {}
        for k, v in d.items():
            if k in sensitive_keys and isinstance(v, str):
                result[k] = sensitive_keys[k](v)
            elif isinstance(v, dict):
                result[k] = _mask_dict(v)
            elif isinstance(v, list):
                result[k] = [_mask_dict(item) if isinstance(item, dict) else item for item in v]
            else:
                result[k] = v
        return result

    return _mask_dict(masked)
