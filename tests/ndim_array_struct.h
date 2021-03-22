/**
 * This code assures no padding will be performed
 */
#pragma pack(1)

typedef struct {
	unsigned char r;
	unsigned char g;
	unsigned char b;
	unsigned char a;
} Color;

typedef struct {
  char array_of_strings[4][2][16];
  unsigned int array_of_int[4][2];
  Color array_of_struct[4][2];
} Data;
