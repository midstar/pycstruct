/**
 * This code assures no padding will be performed
 */
#pragma pack(1)

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
  signed int   fivesignedbits : 5;
  unsigned int eightbits : 8;
  signed int   eightsignedbits : 8;
  signed int   onesignedbit : 1;
  signed int   foursignedbits : 4;
  signed int   sixteensignedbits: 16;
  unsigned int fivebits : 5;
} Data;

int main() {
   Data d;
   memset(&d, 0, sizeof(Data));

   d.onebit = 1;
   d.twobits = 3;
   d.threebits = 1;
   d.fourbits = 3;
   d.fivesignedbits = -2;
   d.eightbits = 255;
   d.eightsignedbits = -128;
   d.onesignedbit = -1;
   d.foursignedbits = 5;
   d.sixteensignedbits = -12345;
   d.fivebits = 16;

   int size = sizeof(Data);

   printf("Saving %d bytes to bitfield_little.dat\n", size);
   FILE *f = fopen("bitfield_little.dat", "w");
   fwrite(&d, size, 1, f);
   fclose(f);

   if(sizeof(unsigned long long) != size) 
   {
     printf("ERROR! Big endian conversion will not work due to size error!");
     return 1;
   }

   // Create a big endian version
   unsigned long long longvalue = *((unsigned long long *)&d);
   SWAP(longvalue);

   printf("Saving %d bytes to bitfield_big.dat\n", size);
   f = fopen("bitfield_big.dat", "w");
   fwrite(&longvalue, size, 1, f);
   fclose(f);

   return 0;
}