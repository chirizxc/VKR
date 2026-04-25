import re
import sys

RE_PATTERN = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+")

KBI_MESSAGE = "\nОперация прервана пользователем."
SELECT_INSTRUCTION = "(Используйте стрелки для навигации)"

IS_WINDOWS = sys.platform == "win32"
