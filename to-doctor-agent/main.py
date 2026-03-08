"""
main.py
To-Doctor Agent CLI 入口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from graph.builder import run_report_pipeline


def main():
    print("=" * 60)
    print("🏥 To-Doctor Agent — 健康报告生成系统")
    print("=" * 60)

    user_id = input("\n请输入患者 ID (默认 patient_001): ").strip() or "patient_001"

    print(f"\n📊 正在为 {user_id} 生成健康报告...")
    result = run_report_pipeline(user_id)

    print("\n" + "=" * 60)
    print("📋 报告摘要")
    print("=" * 60)
    print(result["summary"])

    if result.get("appointment_suggestions"):
        print("\n📅 预约建议：")
        for a in result["appointment_suggestions"]:
            print(f"  - {a['department']}（{a['urgency']}）: {a['reason'][:50]}...")

    completeness = result.get("data_completeness", {})
    incomplete = [k for k, v in completeness.items() if not v]
    if incomplete:
        print(f"\n⚠️ 数据不完整: {', '.join(incomplete)}")

    if result.get("pdf_path"):
        print(f"\n📄 PDF 已生成: {result['pdf_path']}")

    if result.get("errors"):
        print(f"\n❌ 错误: {result['errors']}")


if __name__ == "__main__":
    main()
