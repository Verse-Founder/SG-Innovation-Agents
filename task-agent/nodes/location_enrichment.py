"""
nodes/location_enrichment.py
位置富化节点：根据风险评估结果，决定是否推荐附近的公园
"""
from state.task_state import TaskAgentState
from engine.location_service import get_nearby_parks
from schemas.health import HealthSnapshot

def location_enrichment_node(state: TaskAgentState) -> dict:
    """
    位置富化逻辑：
    1. 检查生成的任务中是否有运动类任务且描述中提到需要寻找地点
    2. 如果有经纬度信息，调用 LocationService 获取附近的公园
    3. 将公园信息存入 state，供下一步 LLM 生成文案时使用
    """
    snapshot_data = state.get("health_snapshot")
    if not snapshot_data:
        return {}

    snapshot = HealthSnapshot(**snapshot_data)
    lat = snapshot.latitude
    lon = snapshot.longitude
    
    # 只有当有经纬度时才进行位置查找
    if lat and lon:
        print(f"[LocationNode] 检测到 GPS: {lat}, {lon}，开始查找附近公园...")
        nearby_parks = get_nearby_parks(lat, lon)
        return {"nearby_parks": nearby_parks}
    
    return {"nearby_parks": []}
