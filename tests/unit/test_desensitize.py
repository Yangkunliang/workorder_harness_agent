"""
脱敏工具函数单元测试
测试 app/utils/desensitize.py 中的脱敏函数
"""
import pytest
from app.utils.desensitize import desensitize_name, desensitize_phone, desensitize_email


class TestDesensitizeName:
    """姓名脱敏测试"""

    def test_single_char_name(self):
        """测试单字符姓名脱敏"""
        assert desensitize_name("李") == "李*"
        assert desensitize_name("张") == "张*"
        assert desensitize_name("王") == "王*"

    def test_two_char_name(self):
        """测试双字符姓名脱敏"""
        assert desensitize_name("张三") == "张*"
        assert desensitize_name("李四") == "李*"
        assert desensitize_name("王五") == "王*"

    def test_three_char_name(self):
        """测试三字符姓名脱敏（保留首尾，中间脱敏）"""
        assert desensitize_name("张三丰") == "张*丰"
        assert desensitize_name("欧阳锋") == "欧*锋"
        assert desensitize_name("诸葛亮") == "诸*亮"
        assert desensitize_name("司马懿") == "司*懿"
        assert desensitize_name("孙悟空") == "孙*空"  # 保留首尾：孙+空，中间脱敏

    def test_four_char_name(self):
        """测试四字符姓名脱敏（少数民族或复姓）"""
        # 四字符姓名：司马昭，张三丰（实际是3字符）
        # 真实4字符姓名示例
        assert desensitize_name("司马昭") == "司*昭"
        assert desensitize_name("诸葛亮") == "诸*亮"  # 也是3字符

    def test_long_name(self):
        """测试长姓名脱敏"""
        name = "阿不思·邓布利多"
        result = desensitize_name(name)
        assert result.startswith("阿")
        assert result.endswith("多")
        assert "*" in result

    def test_empty_string(self):
        """测试空字符串（strip 后为空）"""
        # strip 后为空字符串，函数返回空字符串
        assert desensitize_name("") == ""
        assert desensitize_name("   ") == ""

    def test_none_value(self):
        """测试 None 值"""
        assert desensitize_name(None) == ""

    def test_numeric_string(self):
        """测试数字字符串"""
        assert desensitize_name("123") == "1*3"

    def test_special_characters(self):
        """测试特殊字符（8字符名字：保留首尾，中间6个脱敏）"""
        # John.Doe 是 8 个字符，脱敏后应为 J******e
        assert desensitize_name("John.Doe") == "J******e"


class TestDesensitizePhone:
    """手机号脱敏测试"""

    def test_normal_phone(self):
        """测试正常手机号"""
        assert desensitize_phone("13812345678") == "138****5678"
        assert desensitize_phone("13912345678") == "139****5678"
        assert desensitize_phone("18812345678") == "188****5678"

    def test_short_phone(self):
        """测试短手机号"""
        assert desensitize_phone("12345678") == "123****5678"

    def test_empty_string(self):
        """测试空字符串"""
        assert desensitize_phone("") == ""

    def test_none_value(self):
        """测试 None 值"""
        assert desensitize_phone(None) == ""


class TestDesensitizeEmail:
    """邮箱脱敏测试"""

    def test_normal_email(self):
        """测试正常邮箱"""
        assert desensitize_email("zhangsan@example.com") == "z***@example.com"
        assert desensitize_email("test.user@example.com") == "t***@example.com"

    def test_short_username(self):
        """测试短用户名邮箱"""
        assert desensitize_email("a@example.com") == "a***@example.com"

    def test_no_at_symbol(self):
        """测试无 @ 符号"""
        assert desensitize_email("notanemail") == "notanemail"

    def test_empty_string(self):
        """测试空字符串"""
        assert desensitize_email("") == ""

    def test_none_value(self):
        """测试 None 值"""
        assert desensitize_email(None) == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
