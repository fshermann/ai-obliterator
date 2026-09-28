const value = 1;

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

class Fields {
    #alpha = 1;
    #beta = 2;
    #gamma = 3;
    #delta = 4;
}

const text = (
    "CLEAN_STRING one" +
    "CLEAN_STRING two" +
    "CLEAN_STRING three" +
    "CLEAN_STRING four"
);

const tricky = "/* CLEAN_STRING " +
    "two" +
    "three" +
    "four" +
    "five */";
