import re
import os
from datetime import datetime
from typing import Dict, List, Any

class MagicRename:
    """文件名魔法重命名工具"""

    magic_regex = {
        "$TV": {
            "pattern": r".*?([Ss]\d{1,2})?(?:[第EePpXx\.\-\_\( ]{1,2}|^)(\d{1,3})(?!\d).*?\.(mp4|mkv)",
            "replace": r"\1E\2.\3",
        },
        "$BLACK_WORD": {
            "pattern": r"^(?!.*纯享)(?!.*加更)(?!.*超前企划)(?!.*训练室)(?!.*蒸蒸日上).*",
            "replace": "",
        },
    }

    magic_variable = {
        "{TASKNAME}": "",
        "{I}": 1,
        "{EXT}": [r"(?<=\.)\w+$"],
        "{CHINESE}": [r"[\u4e00-\u9fa5]{2,}"],
        "{DATE}": [
            r"(18|19|20)?\d{2}[\.\-/年]\d{1,2}[\.\-/月]\d{1,2}",
            r"(?<!\d)[12]\d{3}[01]?\d[0123]?\d",
            r"(?<!\d)[01]?\d[\.\-/月][0123]?\d",
        ],
        "{YEAR}": [r"(?<!\d)(18|19|20)\d{2}(?!\d)"],
        "{S}": [r"(?<=[Ss])\d{1,2}(?=[EeXx])", r"(?<=[Ss])\d{1,2}"],
        "{SXX}": [r"[Ss]\d{1,2}(?=[EeXx])", r"[Ss]\d{1,2}"],
        "{E}": [
            r"(?<=[Ss]\d\d[Ee])\d{1,3}",
            r"(?<=[Ee])\d{1,3}",
            r"(?<=[Ee][Pp])\d{1,3}",
            r"(?<=第)\d{1,3}(?=[集期话部篇])",
            r"(?<!\d)\d{1,3}(?=[集期话部篇])",
            r"(?!.*19)(?!.*20)(?<=[\._])\d{1,3}(?=[\._])",
            r"^\d{1,3}(?=\.\w+)",
            r"(?<!\d)\d{1,3}(?!\d)(?!$)",
        ],
        "{PART}": [
            r"(?<=[集期话部篇第])[上中下一二三四五六七八九十]",
            r"[上中下一二三四五六七八九十]",
        ],
        "{VER}": [r"[\u4e00-\u9fa5]+版"],
    }

    priority_list = [
        "上",
        "中",
        "下",
        "一",
        "二",
        "三",
        "四",
        "五",
        "六",
        "七",
        "八",
        "九",
        "十",
    ]

    def __init__(self, magic_regex={}, magic_variable={}):
        """
        初始化
        :param magic_regex: 自定义魔法正则
        :param magic_variable: 自定义魔法变量
        """
        self.magic_regex.update(magic_regex)
        self.magic_variable.update(magic_variable)
        self.dir_filename_dict = {}

    def set_taskname(self, taskname: str):
        """
        设置任务名称
        :param taskname: 任务名称
        """
        self.magic_variable["{TASKNAME}"] = taskname

    def magic_regex_conv(self, pattern: str, replace: str) -> tuple:
        """
        魔法正则匹配
        :param pattern: 匹配模式
        :param replace: 替换模式
        :return: (pattern, replace) 元组
        """
        keyword = pattern
        if keyword in self.magic_regex:
            pattern = self.magic_regex[keyword]["pattern"]
            if replace == "":
                replace = self.magic_regex[keyword]["replace"]
        return pattern, replace
    def start_magic_is_save(self, start_magic:List[Dict[str, Any]],file_name:str) -> bool:
        """
        判断是否需要保存
        :param start_magic: 正则表达式
        :param file_name: 文件名
        :return: 是否需要保存
        """
        # 如果start_magic为空，则返回True
        if not start_magic:
            return True
        if len(start_magic) == 0:
            return True
        flag = [False] * len(start_magic)
        for i, start_magic in enumerate(start_magic):
            if start_magic["type"] in self.magic_variable:
              regex = self.magic_variable[start_magic["type"]]
              #  根据文件名 正则匹配 然后根据symbol判断 symbol 是> < 或者=              
              for p in regex:
                match = re.search(p, file_name)
                if match:
                    # 提取数字
                    number_str = re.search(r'\d+', match.group())
                    if number_str:
                        number = int(number_str.group())
                        if start_magic["symbol"] == ">":
                            if number > start_magic["value"]:
                                flag[i] = True
                        elif start_magic["symbol"] == "<":
                            if number < start_magic["value"]:
                                flag[i] = True
                        elif start_magic["symbol"] == "=":
                            if number == start_magic["value"]:
                                flag[i] = True
                                
        return all(flag)

    def sub(self, pattern: str, replace: str, file_name: str) -> str:
        """
        魔法正则、变量替换
        :param pattern: 匹配模式
        :param replace: 替换模式
        :param file_name: 文件名
        :return: 替换后的文件名
        """
        if not replace:
            return file_name
            
        # 预处理替换变量
        for key, p_list in self.magic_variable.items():
            if key in replace:
                # 正则类替换变量
                if p_list and isinstance(p_list, list):
                    match = None
                    for p in p_list:
                        match = re.search(p, file_name)
                        if match:
                            # 匹配成功，替换为匹配到的值
                            value = match.group()
                            # 日期格式处理：补全、格式化
                            if key == "{DATE}":
                                value = "".join(
                                    [char for char in value if char.isdigit()]
                                )
                                value = (
                                    str(datetime.now().year)[: (8 - len(value))] + value
                                )
                            replace = replace.replace(key, value)
                            break
                    # 清理未匹配的变量
                    if not match:
                        if key == "{SXX}":
                            replace = replace.replace(key, "S01")
                        else:
                            replace = replace.replace(key, "")
                # 非正则类替换变量
                elif key == "{TASKNAME}":
                    replace = replace.replace(key, self.magic_variable["{TASKNAME}"])
                elif key == "{I}":
                    continue
                else:
                    # 清理未匹配的 magic_variable key
                    replace = replace.replace(key, "")

        if pattern and replace:
            file_name = re.sub(pattern, replace, file_name)
        else:
            file_name = replace
            
        return file_name

    def _custom_sort_key(self, name: str) -> str:
        """
        自定义排序键
        :param name: 文件名
        :return: 排序键
        """
        for i, keyword in enumerate(self.priority_list):
            if keyword in name:
                return name.replace(keyword, f"{i:02d}")  # 替换为数字，方便排序
        return name

    def sort_file_list(self, file_list: List[Dict[str, Any]], dir_filename_dict: Dict[int, str] = {}):
        """
        文件列表统一排序，给{I+}赋值
        :param file_list: 文件列表
        :param dir_filename_dict: 目录文件名字典
        """
        filename_list = [
            f["file_name_re"]
            for f in file_list
            if f.get("file_name_re") and not f["dir"]
        ]
        
        dir_filename_dict = dir_filename_dict or self.dir_filename_dict
        # 合并目录文件列表
        filename_list = list(set(filename_list) | set(dir_filename_dict.values()))
        filename_list.sort(key=self._custom_sort_key)
        
        filename_index = {}
        for name in filename_list:
            if name in dir_filename_dict.values():
                continue
            i = filename_list.index(name) + 1
            while i in dir_filename_dict.keys():
                i += 1
            dir_filename_dict[i] = name
            filename_index[name] = i
            
        for file in file_list:
            if file.get("file_name_re"):
                if match := re.search(r"\{I+\}", file["file_name_re"]):
                    i = filename_index.get(file["file_name_re"], 0)
                    file["file_name_re"] = re.sub(
                        match.group(),
                        str(i).zfill(match.group().count("I")),
                        file["file_name_re"],
                    )

    def set_dir_file_list(self, file_list: List[Dict[str, Any]], replace: str):
        """
        设置目录文件列表
        :param file_list: 文件列表
        :param replace: 替换模式
        """
        if not file_list:
            return
            
        self.dir_filename_dict = {}
        filename_list = [f["file_name"] for f in file_list if not f["dir"]]
        filename_list.sort()
        
        if match := re.search(r"\{I+\}", replace):
            # 由替换式转换匹配式
            magic_i = match.group()
            pattern_i = r"\d" * magic_i.count("I")
            pattern = replace.replace(match.group(), "🔢")
            
            for key, _ in self.magic_variable.items():
                if key in pattern:
                    pattern = pattern.replace(key, "🔣")
                    
            pattern = re.sub(r"\\[0-9]+", "🔣", pattern)  # \1 \2 \3
            pattern = f"({re.escape(pattern).replace('🔣', '.*?').replace('🔢', f')({pattern_i})(')})"
            
            # 获取起始编号
            if match := re.match(pattern, filename_list[-1]):
                self.magic_variable["{I}"] = int(match.group(2))
                
            # 目录文件列表
            for filename in filename_list:
                if match := re.match(pattern, filename):
                    self.dir_filename_dict[int(match.group(2))] = (
                        match.group(1) + magic_i + match.group(3)
                    )

    def is_exists(self, filename: str, filename_list: List[str], ignore_ext: bool = False) -> str:
        """
        判断文件是否存在，处理忽略扩展名
        :param filename: 文件名
        :param filename_list: 文件名列表
        :param ignore_ext: 是否忽略扩展名
        :return: 存在返回文件名，不存在返回None
        """
        
        if ignore_ext:
            filename = os.path.splitext(filename)[0]
            filename_list = [os.path.splitext(f)[0] for f in filename_list]
        
        # {I+} 模式，用I通配数字序号
        if match := re.search(r"\{I+\}", filename):
            magic_i = match.group()
            pattern_i = r"\d" * magic_i.count("I")
            pattern = filename.replace(magic_i, pattern_i)
            for filename in filename_list:
                if re.match(pattern, filename):
                    return filename
            return None
        else:
            return filename if filename in filename_list else None 
        