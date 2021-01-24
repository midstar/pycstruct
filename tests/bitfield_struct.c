#include "bitfield_struct.h"
#include <stdio.h>
#include <string.h>



int main() {
   Data d;
   memset(&d, 0, sizeof(Data));

   d.m1 = -11111;
   d.bf1a = 2;
   d.bf1b = 3;
   d.m2 = 44;
   d.bf2a = 5;
   d.bf2b = 66;
   d.bf3a = 7;
   d.bf3b = 8;
   d.m3 = 99;

   int size = sizeof(Data);

   printf("Saving %d bytes to bitfield_struct.dat\n", size);
   FILE *f = fopen("bitfield_struct.dat", "w");
   fwrite(&d, size, 1, f);
   fclose(f);

   return 0;
}