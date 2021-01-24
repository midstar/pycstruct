/**
 * This code assures no padding will be performed
 */
#pragma pack(1)

typedef struct {
  int m1;
  unsigned int bf1a : 3;
  unsigned int bf1b : 5;
  unsigned char m2;
  int bf2a : 4;
  int bf2b : 10;
  unsigned char bf3a : 3;
  unsigned char bf3b : 5;
  long m3;
} Data;