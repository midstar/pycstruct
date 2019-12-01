#pragma pack(1)

#include <stdio.h>
#include <string.h>

#define TRUE 1
#define FALSE 0

typedef signed char   INT8;
typedef unsigned char UINT8;
typedef unsigned char BOOL8;

typedef signed short   INT16;
typedef unsigned short UINT16;
typedef unsigned short BOOL16;
//typedef ? FLOAT16 - Not supprted

typedef int          INT32;
typedef unsigned int UINT32;
typedef unsigned int BOOL32;
typedef float        FLOAT32;

typedef long long          INT64;
typedef unsigned long long UINT64;
typedef unsigned long long BOOL64;
typedef double             FLOAT64;


typedef struct {
   // 1 byte members
   INT8    int8_low;
   INT8    int8_high;
   UINT8   uint8_low;
   UINT8   uint8_high;
   BOOL8   bool8_false;
   BOOL8   bool8_true;

   // 2 byte members
   INT16   int16_low;
   INT16   int16_high;
   UINT16  uint16_low;
   UINT16  uint16_high;
   BOOL16  bool16_false;
   BOOL16  bool16_true;

   // 4 byte members
   INT32   int32_low;
   INT32   int32_high;
   UINT32  uint32_low;
   UINT32  uint32_high;
   BOOL32  bool32_false;
   BOOL32  bool32_true;
   FLOAT32 float32_low;
   FLOAT32 float32_high;

   // 8 byte members
   INT64   int64_low;
   INT64   int64_high;
   UINT64  uint64_low;
   UINT64  uint64_high;
   BOOL64  bool64_false;
   BOOL64  bool64_true;
   FLOAT64 float64_low;
   FLOAT64 float64_high;

   // UTF-8 strings
   char utf8_ascii[100];
   char utf8_nonascii[80];
   char utf8_no_term[4];
} Data;

void main() {
   Data d;
   memset(&d, 0, sizeof(Data));

   d.int8_low     = -128;
   d.int8_high    = 127;
   d.uint8_low    = 0;
   d.uint8_high   = 255;
   d.bool8_false  = FALSE;
   d.bool8_true   = TRUE;
   
   d.int16_low     = -32768;
   d.int16_high    = 32767;
   d.uint16_low    = 0;
   d.uint16_high   = 65535;
   d.bool16_false  = FALSE;
   d.bool16_true   = TRUE;
   
   d.int32_low     = -2147483648;
   d.int32_high    = 2147483647;
   d.uint32_low    = 0;
   d.uint32_high   = 4294967295;
   d.bool32_false  = FALSE;
   d.bool32_true   = TRUE;
   d.float32_low   = 1.23456;
   d.float32_high  = 12345.6;
   
   d.int64_low     = -9223372036854775808; 
   d.int64_high    = 9223372036854775807;
   d.uint64_low    = 0;
   d.uint64_high   = 18446744073709551615; 
   d.bool64_false  = FALSE;
   d.bool64_true   = TRUE;
   d.float64_low   = 1.23456789;
   d.float64_high  = 12345678.9;

   strcpy(d.utf8_ascii, "This is a normal ASCII string!");
   strcpy(d.utf8_nonascii, "This string has special characters ÅÄÖü");
   d.utf8_no_term[0] = 'A';
   d.utf8_no_term[1] = 'B';
   d.utf8_no_term[2] = 'C';
   d.utf8_no_term[3] = 'D';

   printf("Saving struct to struct.dat\n");
   FILE *f = fopen("struct.dat", "w");
   fwrite(&d, sizeof(Data), 1, f);
   fclose(f);
}