"""
engine/location_service.py
位置服务：使用 OpenStreetMap Overpass API 查找用户附件的公园
"""
import requests
import logging

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def get_nearby_parks(lat: float, lon: float, radius_meters: int = 3000) -> list[dict]:
    """
    使用 Overpass API 查询附近的公园
    """
    # 构造 Overpass QL 查询语句
    # 查找指定半径内的 leisure=park 或 landuse=recreation_ground
    query = f"""
    [out:json];
    (
      node["leisure"="park"](around:{radius_meters},{lat},{lon});
      way["leisure"="park"](around:{radius_meters},{lat},{lon});
      node["landuse"="recreation_ground"](around:{radius_meters},{lat},{lon});
    );
    out center;
    """
    
    try:
        response = requests.post(OVERPASS_URL, data={'data': query}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        parks = []
        for element in data.get("elements", []):
            name = element.get("tags", {}).get("name")
            if not name:
                # 尝试获取本地化名称或默认名称
                name = element.get("tags", {}).get("name:zh") or element.get("tags", {}).get("name:en") or "未名公园"
            
            # 获取中心点坐标
            e_lat = element.get("lat") or element.get("center", {}).get("lat")
            e_lon = element.get("lon") or element.get("center", {}).get("lon")
            
            if name and e_lat and e_lon:
                parks.append({
                    "name": name,
                    "latitude": e_lat,
                    "longitude": e_lon,
                    "type": element.get("tags", {}).get("leisure") or element.get("tags", {}).get("landuse")
                })
        
        # 去重并排序（可选）
        unique_parks = {p["name"]: p for p in parks}.values()
        logger.info(f"找到 {len(unique_parks)} 个附近的公园")
        return list(unique_parks)[:5]  # 返回前5个推荐
        
    except Exception as e:
        logger.error(f"查询附近公园失败: {e}")
        # 回退：提供一些新加坡通用的公园作为兜底
        return [
            {"name": "East Coast Park", "latitude": 1.3048, "longitude": 103.9242},
            {"name": "Singapore Botanic Gardens", "latitude": 1.3138, "longitude": 103.8159},
            {"name": "Bishan-Ang Mo Kio Park", "latitude": 1.3621, "longitude": 103.8465},
        ]
