#include <stdio.h>

typedef unsigned int UINT32;
typedef unsigned int INT32;
typedef unsigned int INT32;

typedef struct {
   UINT32 header;
   UINT32 length;
   INT32 signedInt;
   UINT32 unsignedInt;
   INT32 array[10];
   char ascii[100];
   char ascii_no_term[4];
   char utf8_specials[40];
} Data;9

void main() {
   Data d;
   d.header = 1234;
   d.length = 4;
   d.signedInt = -1;
   d.unsignedInt = 1;
   for (int i=0; i < 10; i++)
      d.array[i] = i;
   strcpy(d.ascii, "Hello there this is a string!");
   d.ascii_no_term[0] = 'A';
   d.ascii_no_term[1] = 'B';
   d.ascii_no_term[2] = 'C';
   d.ascii_no_term[3] = 'D';
   strcpy(d.utf8_specials, "Specials: ÅÄÖü");
   printf("Saving struct\n");
   
   FILE *f = fopen("struct.dat", "w");
   fwrite(&d, sizeof(Data), 1, f);
   fclose(f);
}