#ifndef NO_PACK

/**
 * This code assures no padding will be performed
 */
#pragma pack(1)

const char *out_file = "embedded_struct.dat";

#else

const char *out_file = "embedded_struct_nopack.dat";

#endif // NO_PACK

#include <stdio.h>
#include <string.h>

enum car_type { Sedan=0, Station_Wagon=5, Bus=7, Pickup=12};

struct car_properties_s {
  unsigned int env_class : 3;
  unsigned int registered : 1;
  unsigned int over_3500_kg : 1;
};

struct car_s 
{
    unsigned short year;
    char model[50];
    char registration_number[10];
    struct car_properties_s properties;
    enum car_type type;
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
    house.garage.cars[0].properties.env_class = 0;
    house.garage.cars[0].properties.registered = 1;
    house.garage.cars[0].properties.over_3500_kg = 0;
    house.garage.cars[0].type = Sedan;

    strcpy(house.garage.cars[0].registration_number, "AHF432");
    strcpy(house.garage.cars[0].model, "Nissan Micra");

    house.garage.cars[1].year = 2005;
    house.garage.cars[1].properties.env_class = 1;
    house.garage.cars[1].properties.registered = 1;
    house.garage.cars[1].properties.over_3500_kg = 1;
    house.garage.cars[1].type = Bus;
    strcpy(house.garage.cars[1].registration_number, "CCO544");
    strcpy(house.garage.cars[1].model, "Ford Focus");

    house.garage.cars[2].year = 1998;
    house.garage.cars[2].properties.env_class = 3;
    house.garage.cars[2].properties.registered = 0;
    house.garage.cars[2].properties.over_3500_kg = 0;
    house.garage.cars[2].type = Pickup;
    strcpy(house.garage.cars[2].registration_number, "HHT434");
    strcpy(house.garage.cars[2].model, "Volkswagen Golf");

    printf("Size car_type: %d\n", sizeof(enum car_type));
    printf("Size car_properties_s: %d\n", sizeof(struct car_properties_s));
    printf("Size car_s: %d\n", sizeof(struct car_s));
    printf("Size garage_s: %d\n", sizeof(struct garage_s));
    printf("Size house_s: %d\n", sizeof(struct house_s));

    printf("Saving %s\n", out_file);
    FILE *f = fopen(out_file, "w");
    fwrite(&house, sizeof(struct house_s), 1, f);
    fclose(f);
 
}
