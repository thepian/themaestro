import ctypes

__all__ = ('ABDAY_1', 'ABDAY_2', 'ABDAY_3', 'ABDAY_4', 'ABDAY_5', 'ABDAY_6', 'ABDAY_7', 'ABMON_1', 'ABMON_10', 'ABMON_11', 'ABMON_12', 'ABMON_2', 'ABMON_3', 'ABMON_4', 'ABMON_5', 'ABMON_6', 'ABMON_7', 'ABMON_8', 'ABMON_9', 'ALL_CONSTANTS', 'ALT_DIGITS', 'AM_STR', 'CHAR_MAX', 'CODESET', 'CRNCYSTR', 'DAY_1', 'DAY_2', 'DAY_3', 'DAY_4', 'DAY_5', 'DAY_6', 'DAY_7', 'D_FMT', 'D_T_FMT', 'ERA', 'ERA_D_FMT', 'ERA_D_T_FMT', 'ERA_T_FMT', 'HAS_LANGINFO', 'LC_ALL', 'LC_COLLATE', 'LC_CTYPE', 'LC_MESSAGES', 'LC_MONETARY', 'LC_NUMERIC', 'LC_TIME', 'MON_1', 'MON_10', 'MON_11', 'MON_12', 'MON_2', 'MON_3', 'MON_4', 'MON_5', 'MON_6', 'MON_7', 'MON_8', 'MON_9', 'NOEXPR', 'PM_STR', 'RADIXCHAR', 'THOUSEP', 'T_FMT', 'T_FMT_AMPM', 'YESEXPR', 'nl_item')

ABDAY_1 = 14
ABDAY_2 = 15
ABDAY_3 = 16
ABDAY_4 = 17
ABDAY_5 = 18
ABDAY_6 = 19
ABDAY_7 = 20
ABMON_1 = 33
ABMON_10 = 42
ABMON_11 = 43
ABMON_12 = 44
ABMON_2 = 34
ABMON_3 = 35
ABMON_4 = 36
ABMON_5 = 37
ABMON_6 = 38
ABMON_7 = 39
ABMON_8 = 40
ABMON_9 = 41
ALL_CONSTANTS = ('LC_CTYPE', 'LC_TIME', 'LC_COLLATE', 'LC_MONETARY', 'LC_MESSAGES', 'LC_NUMERIC', 'LC_ALL', 'CHAR_MAX', 'RADIXCHAR', 'THOUSEP', 'CRNCYSTR', 'D_T_FMT', 'D_FMT', 'T_FMT', 'AM_STR', 'PM_STR', 'CODESET', 'T_FMT_AMPM', 'ERA', 'ERA_D_FMT', 'ERA_D_T_FMT', 'ERA_T_FMT', 'ALT_DIGITS', 'YESEXPR', 'NOEXPR', 'DAY_1', 'ABDAY_1', 'DAY_2', 'ABDAY_2', 'DAY_3', 'ABDAY_3', 'DAY_4', 'ABDAY_4', 'DAY_5', 'ABDAY_5', 'DAY_6', 'ABDAY_6', 'DAY_7', 'ABDAY_7', 'MON_1', 'ABMON_1', 'MON_2', 'ABMON_2', 'MON_3', 'ABMON_3', 'MON_4', 'ABMON_4', 'MON_5', 'ABMON_5', 'MON_6', 'ABMON_6', 'MON_7', 'ABMON_7', 'MON_8', 'ABMON_8', 'MON_9', 'ABMON_9', 'MON_10', 'ABMON_10', 'MON_11', 'ABMON_11', 'MON_12', 'ABMON_12')
ALT_DIGITS = 49
AM_STR = 5
CHAR_MAX = 127
CODESET = 0
CRNCYSTR = 56
DAY_1 = 7
DAY_2 = 8
DAY_3 = 9
DAY_4 = 10
DAY_5 = 11
DAY_6 = 12
DAY_7 = 13
D_FMT = 2
D_T_FMT = 1
ERA = 45
ERA_D_FMT = 46
ERA_D_T_FMT = 47
ERA_T_FMT = 48
HAS_LANGINFO = 1
LC_ALL = 0
LC_COLLATE = 1
LC_CTYPE = 2
LC_MESSAGES = 6
LC_MONETARY = 3
LC_NUMERIC = 4
LC_TIME = 5
MON_1 = 21
MON_10 = 30
MON_11 = 31
MON_12 = 32
MON_2 = 22
MON_3 = 23
MON_4 = 24
MON_5 = 25
MON_6 = 26
MON_7 = 27
MON_8 = 28
MON_9 = 29
NOEXPR = 53
PM_STR = 6
RADIXCHAR = 50
THOUSEP = 51
T_FMT = 3
T_FMT_AMPM = 4
YESEXPR = 52
nl_item = ctypes.c_long