export function keep(): number {
    return 1;
}

// CLEAN_LINE one
// CLEAN_LINE two
// CLEAN_LINE three

// LONG_LINE one
// LONG_LINE two
// LONG_LINE three
// LONG_LINE four

// ALLOW_LINE one
// ALLOW_LINE two
// ALLOW_LINE three
// obliterator-allow ALLOW_LINE four

/* CLEAN_BLOCK one
CLEAN_BLOCK two
CLEAN_BLOCK three */

/* LONG_BLOCK one
LONG_BLOCK two
LONG_BLOCK three
LONG_BLOCK four */

/* obliterator-allow ALLOW_BLOCK
ALLOW_BLOCK two
ALLOW_BLOCK three
ALLOW_BLOCK four */

class Fields {
    #alpha: number;
    #beta: string;
    #gamma: boolean;
    #delta: bigint;
}
