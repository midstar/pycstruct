struct name_conflict {
    int member;
};

typedef union {
    int member1;
    int member2;
}name_conflict;

struct non_supported_member {
    int matrix[10][10];
};

struct with_volatile {
    volatile int volatile_member;
    volatile int volatile_array[2];
};