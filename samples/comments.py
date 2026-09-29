value = 1

# CLEAN_LINE one
# CLEAN_LINE two
# CLEAN_LINE three

# LONG_LINE one
# LONG_LINE two
# LONG_LINE three
# LONG_LINE four

# ALLOW_LINE one
# ALLOW_LINE two
# ALLOW_LINE three
# ALLOW_LINE four
# ALLOW_LINE five
# obliterator-allow ALLOW_LINE six
# ALLOW_LINE seven

# obliterator-allow ALLOW_LINE first
# ALLOW_LINE first
# ALLOW_LINE first
# ALLOW_LINE first

    # LONG_LINE indent
    # LONG_LINE indent
    # LONG_LINE indent
    # LONG_LINE indent
    # LONG_LINE indent

# CLEAN_LINE gap
# CLEAN_LINE gap
# CLEAN_LINE gap

# CLEAN_LINE gap
# CLEAN_LINE gap
# CLEAN_LINE gap

x = 1  # inline
y = 2  # inline
z = 3  # inline
w = 4  # inline

"""CLEAN_BLOCK only"""

"""CLEAN_BLOCK three
CLEAN_BLOCK three
CLEAN_BLOCK three"""

"""LONG_BLOCK four
LONG_BLOCK four
LONG_BLOCK four
LONG_BLOCK four"""

"""ALLOW_BLOCK keep
ALLOW_BLOCK keep
obliterator-allow
ALLOW_BLOCK keep"""

'''CLEAN_BLOCK sq
CLEAN_BLOCK sq
CLEAN_BLOCK sq'''

'''LONG_BLOCK sq
LONG_BLOCK sq
LONG_BLOCK sq
LONG_BLOCK sq'''

'''obliterator-allow ALLOW_BLOCK sq
ALLOW_BLOCK sq
ALLOW_BLOCK sq
ALLOW_BLOCK sq'''

def documented():
    """LONG_BLOCK doc
    LONG_BLOCK doc
    LONG_BLOCK doc
    LONG_BLOCK doc"""
    return 1

def classic():
    """
    LONG_BLOCK classic
    LONG_BLOCK classic
    """
    return 1

def tiny():
    """
    CLEAN_BLOCK tiny
    """
    return 2

r"""LONG_BLOCK raw
LONG_BLOCK raw
LONG_BLOCK raw
LONG_BLOCK raw"""

text = """CLEAN_STRING
CLEAN_STRING
CLEAN_STRING
CLEAN_STRING"""

more = (
    "CLEAN_STRING paren"
    "CLEAN_STRING paren"
    "CLEAN_STRING paren"
    "CLEAN_STRING paren"
)

label = (
    """CLEAN_BLOCK paren
    CLEAN_BLOCK paren
    CLEAN_BLOCK paren"""
)

label2 = (
    """LONG_BLOCK paren
    LONG_BLOCK paren
    LONG_BLOCK paren
    LONG_BLOCK paren"""
)

gone = """CLEAN_STRING returned
CLEAN_STRING returned
CLEAN_STRING returned
CLEAN_STRING returned"""

"""LONG_BLOCK five
LONG_BLOCK five
LONG_BLOCK five
LONG_BLOCK five
LONG_BLOCK five"""

def shipped():
    return """CLEAN_STRING code
CLEAN_STRING code
CLEAN_STRING code
CLEAN_STRING code"""
