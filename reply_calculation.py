def get_proximity_level(method: str, L: float, param_value: float) -> str:
    """
    根据城市轨道交通结构施工方法和相对净距判定接近程度。

    参数:
    method (str): 施工方法，可选值: '明挖、盖挖法', '矿山法', '盾构法或顶管法', '高架结构'
    L (float): 最小相对净距
    param_value (float): 对应的参数值 (H, W, D, 或 P)

    返回:
    str: 接近程度 (非常接近, 接近, 较接近, 不接近)
    """

    # 1. 明挖、盖挖法 (对应参数 H: 基坑开挖深度)
    if "明挖" in method or "盖挖" in method or "暗挖" in method:
        if L <= 0.5 * param_value:
            return "非常接近"
        elif 0.5 * param_value < L <= 1.0 * param_value:
            return "接近"
        elif 1.0 * param_value < L <= 2.0 * param_value:
            return "较接近"
        else:
            return "不接近"

    # 2. 矿山法 (对应参数 W: 隧道毛洞跨度)
    elif "矿山" in method:
        if L <= 1.0 * param_value:
            return "非常接近"
        elif 1.0 * param_value < L <= 1.5 * param_value:
            return "接近"
        elif 1.5 * param_value < L <= 2.5 * param_value:
            return "较接近"
        else:
            return "不接近"

    # 3. 盾构法或顶管法 (对应参数 D: 隧道外径/顶管外径)
    elif "盾构" in method or "顶管" in method:
        if L <= 1.0 * param_value:
            return "非常接近"
        elif 1.0 * param_value < L <= 2.0 * param_value:
            return "接近"
        elif 2.0 * param_value < L <= 3.0 * param_value:
            return "较接近"
        else:
            return "不接近"

    # 4. 高架结构（桥梁桩基） (对应参数 P: 桩径)
    elif method == "高架":
        if L <= 3.0 * param_value:
            return "非常接近"
        elif 3.0 * param_value < L <= 10.0 * param_value:
            return "接近"
        elif 10.0 * param_value < L <= 20.0 * param_value:
            return "较接近"
        else:
            return "不接近"

    else:
        return "未知施工方法"

def get_affected_area(method: str, dis: float, param_value: float) -> str:
    #获取影响区
    #param_value为文档中的h1,h2,d; depth为实际输入

    L=dis
    # 1. 明挖、盖挖法 (对应参数 h1)
    if "明挖" in method or "盖挖" in method:
        if L <= 0.7 * param_value:
            return "A"
        elif 0.7 * param_value < L <= 1.3 * param_value:
            return "B"
        elif 1.3 * param_value < L <= 2.5 * param_value:
            return "C"
        else:
            return "D"

    elif ("矿山" in method or "盾构" in method or "顶管" in method or "拉管" in method) and ("浅埋" not in method) and ("深埋" not in method):
        return "输入浅埋或深埋"

    # 2. 浅埋矿山、盾构法 (对应参数 h2)
    elif ("矿山" in method or "盾构" in method or "顶管" in method or "拉管" in method) and "浅埋" in method:
        if L <= 0.7 * param_value:
            return "A"
        elif 0.7 * param_value < L <= 1.0 * param_value:
            return "B"
        elif 1.0 * param_value < L <= 2.0 * param_value:
            return "C"
        else:
            return "D"

    # 3. 深埋矿山、盾构法 (对应参数 b)
    elif ("矿山" in method or "盾构" in method or "顶管" in method or "拉管" in method) and "深埋" in method:
        if L <= 1.0 * param_value:
            return "A"
        elif 1.0 * param_value < L <= 2.0 * param_value:
            return "B"
        elif 2.0 * param_value < L <= 3.0 * param_value:
            return "C"
        else:
            return "D"

    else:
        return "D"

def get_affected_level(proximity_level,affected_area):
    if proximity_level == "非常接近":
        if affected_area=="A":
            return "特级"
        elif affected_area=="B":
            return "特级"
        elif affected_area=="C":
            return "一级"
        else:
            return "二级"
    elif proximity_level == "接近":
        if affected_area=="A":
            return "特级"
        elif affected_area=="B":
            return "一级"
        elif affected_area=="C":
            return "二级"
        else:
            return "三级"
    elif proximity_level == "较接近":
        if affected_area=="A":
            return "一级"
        elif affected_area=="B":
            return "二级"
        elif affected_area=="C":
            return "三级"
        else:
            return "四级"
    elif proximity_level == "不接近":
        if affected_area=="A":
            return "二级"
        elif affected_area=="B":
            return "三级"
        elif affected_area=="C":
            return "四级"
        else:
            return "四级"
    else:
        return "四级"

def promote_affected_level(affected_level):
    if affected_level == "一级":
        return "特级"
    elif affected_level == "二级":
        return "一级"
    elif affected_level == "三级":
        return "二级"
    elif affected_level == "四级":
        return "三级"
    elif affected_level == "特级":
        return "特级"
    else:
        return "四级"

def is_safe_distance_satisfied(structure_type, geological_section, dis):
    if "明挖" in structure_type or "暗挖" in structure_type or "盾构" in structure_type:
        if geological_section=="非漫滩":
            if dis>=5:
                return "满足"
            else:
                return "不满足"
        elif geological_section=="漫滩":
            if dis>=50:
                return "满足"
            else:
                return "不满足"
    elif "高架" in structure_type:
        if dis>=3:
            return "满足"
        else:
            return "不满足"
    else:
        if dis>=5:
            return "满足"
        else:
            return "不满足"

def is_safety_estimation_needed(affected_level):
    if affected_level == "特级" or affected_level == "一级" or affected_level == "二级":
        return "需要"
    else:
        return "不需要"

def is_protection_monitor_needed(affected_level):
    if affected_level == "特级" or affected_level == "一级" or affected_level == "二级":
        return "需要"
    else:
        return "不需要"