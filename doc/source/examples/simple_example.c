#include <stdio.h>
#include <stdbool.h>
#include <string.h>

#pragma pack(1) // To secure no padding is added in struct

struct person 
{ 
    char name[50];
    unsigned int age;
    float height;
    bool is_male;
    unsigned int nbr_of_children;
    unsigned int child_ages[10];
};


void main(void) {
    struct person p;
    memset(&p, 0, sizeof(struct person));

    strcpy(p.name, "Foo Bar");
    p.age = 42;
    p.height = 1.75; // m
    p.is_male = true;
    p.nbr_of_children = 2;
    p.child_ages[0] = 7;
    p.child_ages[1] = 9;

    FILE *f = fopen("simple_example.dat", "w");
    fwrite(&p, sizeof(struct person), 1, f);
    fclose(f);
}