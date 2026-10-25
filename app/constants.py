"""Approved domain enums shared by validation, queries and templates."""

CATEGORIES = (
    "照明", "水管", "门锁", "网络",
    "本体类", "电类", "电梯类", "道路景观类", "给排水类", "空调类",
    "开水饮水类", "门窗五金类", "暖气类", "洗浴热水类", "消防设施类", "其他",
)
STATUS_LABELS = {
    "PENDING": "待处理",
    "ACCEPTED": "已接单",
    "IN_PROGRESS": "维修中",
    "COMPLETED": "已完成",
}
