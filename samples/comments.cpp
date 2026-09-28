int value = 1;

// CLEAN_LINE one
// CLEAN_LINE two
// CLEAN_LINE three

// LONG_LINE one
// LONG_LINE two
// LONG_LINE three
// LONG_LINE four

// ALLOW_LINE one
// obliterator-allow ALLOW_LINE two
// ALLOW_LINE three
// ALLOW_LINE four

/* CLEAN_BLOCK one
CLEAN_BLOCK two
CLEAN_BLOCK three */

/* LONG_BLOCK one
LONG_BLOCK two
LONG_BLOCK three
LONG_BLOCK four */

/* ALLOW_BLOCK one
ALLOW_BLOCK two
obliterator-allow
ALLOW_BLOCK four */

/*
 * CLEAN_BLOCK star
 */

/*
 * LONG_BLOCK star
 * LONG_BLOCK star
 */

const char* text =
    "CLEAN_STRING one\n"
    "CLEAN_STRING two\n"
    "CLEAN_STRING three\n"
    "CLEAN_STRING four\n";

const char* raw = R"(CLEAN_STRING raw
CLEAN_STRING raw
CLEAN_STRING raw
CLEAN_STRING raw
CLEAN_STRING raw)";
