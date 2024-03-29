struct name_conflict {
    int member;
};

typedef union {
    int member1;
    int member2;
}name_conflict;

struct with_volatile {
    volatile int volatile_member;
    volatile int volatile_array[2];
};

enum filled_enum { 
    emem1 = 0,
    emem2 = 1,
    emem3 = 2,
    emem_fill = 0xFFFFFFFF
};

enum signed_enum { 
    semem1 = -1,
    semem2 = 1,
    semem3 = 2,
    semem_fill = 0xFFFFFFFF
};

struct different_char_arrays {
    char char_array[10];
    unsigned char unsigned_char_array[10];
    signed char signed_char_array[10];
};

struct struct_with_struct_inside {
    struct struct_inside {
        int inside_a;
        int inside_b;
    } inside;
};