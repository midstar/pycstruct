/**
 * This code assures no padding will be performed
 */
#pragma pack(1)

#include <stdio.h>
#include <string.h>

struct car_s 
{
    unsigned short year;
    char model[50];
    char registration_number[10];
};

struct garage_s 
{
    struct car_s cars[20];
    unsigned char nbr_registered_parkings;
};

struct house_s {
    unsigned char nbr_of_levels;
    struct garage_s garage;
};

void main() {
    struct house_s house;

    memset(&house, 0, sizeof(struct house_s));
    house.nbr_of_levels = 5;
    house.garage.nbr_registered_parkings = 3;

    house.garage.cars[0].year = 2011;
    strcpy(house.garage.cars[0].registration_number, "AHF432");
    strcpy(house.garage.cars[0].model, "Nissan Micra");

    house.garage.cars[1].year = 2005;
    strcpy(house.garage.cars[1].registration_number, "CCO544");
    strcpy(house.garage.cars[1].model, "Ford Focus");

    house.garage.cars[2].year = 1998;
    strcpy(house.garage.cars[2].registration_number, "HHT434");
    strcpy(house.garage.cars[2].model, "Volkswagen Golf");

    printf("Saving embedded_stuct.dat\n");
    FILE *f = fopen("embedded_struct.dat", "w");
    fwrite(&house, sizeof(struct house_s), 1, f);
    fclose(f);
 
}
