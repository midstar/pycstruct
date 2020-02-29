/**
 * This code assures no padding will be performed
 */
//#pragma pack(1)

#include <stdio.h>
#include <string.h>

#define TRUE 1
#define FALSE 0

void SwapBytes(void *pv, size_t n)
{
    char *p = pv;
    size_t lo, hi;
    for(lo=0, hi=n-1; hi>lo; lo++, hi--)
    {
        char tmp=p[lo];
        p[lo] = p[hi];
        p[hi] = tmp;
    }
}
#define SWAP(x) SwapBytes(&x, sizeof(x));

typedef struct {
  unsigned int onebit : 1;
  unsigned int twobits : 2;
  unsigned int threebits : 3;
  unsigned int fourbits : 4;
  unsigned int fivebits : 5;
  unsigned int eightbits : 8;
  /*unsigned int sixteenbits : 8;*/
  /*signed int onesignedbit : 1;
  signed int foursignedbits : 4;
  signed int sixteensignedbits: 16;*/
} Data;

void main() {
   Data d;
   memset(&d, 0, sizeof(Data));

   //d.onebit = 1;
   d.threebits = 3;
   //d.foursignedbits = -1;

   printf("Saving bitfield_little.dat (%d bytes)\n", sizeof(Data));
   FILE *f = fopen("bitfield_little.dat", "w");
   fwrite(&d, sizeof(Data), 1, f);
   fclose(f);

    /*
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

   for (int i=0 ; i < 5; i++)
      d.int32_array[i] = i;

   strcpy(d.utf8_ascii, "This is a normal ASCII string!");
   strcpy(d.utf8_nonascii, "This string has special characters ÅÄÖü");
   d.utf8_no_term[0] = 'A';
   d.utf8_no_term[1] = 'B';
   d.utf8_no_term[2] = 'C';
   d.utf8_no_term[3] = 'D';

   printf("Saving struct_little.dat\n");
   FILE *f = fopen("struct_little.dat", "w");
   fwrite(&d, sizeof(Data), 1, f);
   fclose(f);

   // Create a big endian version

   SWAP(d.int16_low);
   SWAP(d.int16_high);
   SWAP(d.uint16_low);
   SWAP(d.uint16_high);
   SWAP(d.bool16_false);
   SWAP(d.bool16_true);

   SWAP(d.int32_low);
   SWAP(d.int32_high);
   SWAP(d.uint32_low);
   SWAP(d.uint32_high);
   SWAP(d.bool32_false);
   SWAP(d.bool32_true);  
   SWAP(d.float32_low);
   SWAP(d.float32_high);

   SWAP(d.int64_low);
   SWAP(d.int64_high);
   SWAP(d.uint64_low);
   SWAP(d.uint64_high);
   SWAP(d.bool64_false);
   SWAP(d.bool64_true);  
   SWAP(d.float64_low);
   SWAP(d.float64_high);

   for (int i=0 ; i < 5; i++)
      SWAP(d.int32_array[i]);

   printf("Saving struct_big.dat\n");
   f = fopen("struct_big.dat", "w");
   fwrite(&d, sizeof(Data), 1, f);
   fclose(f);
 */
}