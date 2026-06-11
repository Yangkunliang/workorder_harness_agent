"""
数据脱敏工具函数
"""


def desensitize_name(name: str) -> str:
    """
    姓名脱敏处理
    
    :param name: 原始姓名
    :return: 脱敏后的姓名
    
    脱敏规则：
    - 单字符姓名：保留首字，替换尾字为 '*'（如 '李' -> '李*'）
    - 双字符姓名：保留首字，替换尾字为 '*'（如 '张三' -> '张*'）
    - 多字符姓名：保留首字和尾字，中间替换为 '*'（如 '张三丰' -> '张*丰'）
    """
    if not name:
        return ""
    
    name = str(name).strip()
    
    # strip 后可能变成空字符串
    if not name:
        return ""
    
    if len(name) == 1:
        # 单字符姓名
        return f"{name}*"
    elif len(name) == 2:
        # 双字符姓名：保留首字，第二个字替换为 '*'
        return f"{name[0]}*"
    else:
        # 多字符姓名：保留首字和尾字，中间替换为 '*'
        return f"{name[0]}{'*' * (len(name) - 2)}{name[-1]}"


def desensitize_phone(phone: str) -> str:
    """
    手机号脱敏处理
    
    :param phone: 原始手机号
    :return: 脱敏后的手机号
    
    脱敏规则：保留前3位和后4位，中间4位替换为 '*'
    """
    if not phone:
        return ""
    
    phone = str(phone).strip()
    
    if len(phone) == 11:
        return f"{phone[:3]}****{phone[-4:]}"
    elif len(phone) > 7:
        return f"{phone[:3]}****{phone[-4:]}"
    else:
        return "****"


def desensitize_email(email: str) -> str:
    """
    邮箱脱敏处理
    
    :param email: 原始邮箱
    :return: 脱敏后的邮箱
    
    脱敏规则：保留邮箱名首字母和域名，中间替换为 '*'
    """
    if not email:
        return ""
    
    email = str(email).strip()
    at_index = email.find("@")
    
    if at_index == -1:
        return email
    
    username = email[:at_index]
    domain = email[at_index:]
    
    if len(username) <= 1:
        return f"{username}***{domain}"
    else:
        return f"{username[0]}***{domain}"
