#include <inttypes.h>
#include <stdio.h>

int32_t kernel(int32_t x);

int main(void) {
    printf("kernel(4) = %" PRId32 "\n", kernel(INT32_C(4)));
    return 0;
}
