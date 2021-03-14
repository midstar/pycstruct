#include "ndim_array_struct.h"
#include <stdio.h>
#include <string.h>



int main() {
   int x;
   int y;
   Data d;
   memset(&d, 0, sizeof(Data));

   memset(&d, 0, sizeof(Color));

   for (x = 0; x < 4; x++) {
      for (y = 0; y < 2; y++) {
         sprintf(d.array_of_strings[x][y], "%d x %d = %d", x, y, x * y);
         d.array_of_struct[x][y].r = x;
         d.array_of_struct[x][y].g = y;
         d.array_of_struct[x][y].b = x * 2 + y;
         d.array_of_struct[x][y].a = 255;
      }
   }

   // check the natural C order
   unsigned int static_array[4][2] = {1, 2, 3, 4, 5, 6, 7, 8};
   memcpy(d.array_of_int, static_array, sizeof(static_array));

   int size = sizeof(Data);

   printf("Saving %d bytes to ndim_array_struct.dat\n", size);
   FILE *f = fopen("ndim_array_struct.dat", "w");
   fwrite(&d, size, 1, f);
   fclose(f);

   return 0;
}
