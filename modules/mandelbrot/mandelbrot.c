
// Include the header file to get access to the MicroPython API
#include "py/runtime.h"
#include <complex.h>
#include <stdio.h>
#define ITERATIONS 40

// Convert RGB to RGB565
STATIC int TFTColor(int r, int g, int b) {
     return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
}

//Calculate Mandelbrot
STATIC int mandelbrot_internal(float complex c) {
    float complex z = 0 * I;
    uint8_t n = 0;
    while (cabs(z) <= 2 && n < ITERATIONS) {
        z = (z*z) + c;
        n += 1;
    }
    return n;
}

// Choose what color to return
STATIC int get_colour(int colour, char colour_base) {
    if(colour_base == 0x72){ //"r"
        return TFTColor(colour, 0, 0);
    }
    if(colour_base == 0x67) { //"g"
        return TFTColor(0, colour, 0);
    }
    return TFTColor(0, 0, colour);
}

// Mandelbrot Python interface
STATIC mp_obj_t mandelbrot(
                          mp_obj_t resolution_obj, 
                          mp_obj_t colour_obj, 
                          mp_obj_t boundries_obj
                        ) 
{
    // Extract the tuple from the MicroPython input object
    size_t size;
    mp_obj_t *tuple; 
    
    //Tuple of resolution
    mp_obj_get_array(resolution_obj, &size, &tuple);
    assert(size == 2);
    int width = mp_obj_get_int(tuple[0]);
    int height = mp_obj_get_int(tuple[1]);
    
    int diplay_size_buffer = width * height * 2;

    char * colour_base = (char *) mp_obj_str_get_str(colour_obj);

    //Tuple of boundries
    mp_obj_get_array(boundries_obj, &size, &tuple);
    assert(size == 4);
    float real_start = mp_obj_get_float(tuple[0]);
    float real_end = mp_obj_get_float(tuple[1]);
    float imaginary_start = mp_obj_get_float(tuple[2]);
    float imaginary_end = mp_obj_get_float(tuple[3]);

    uint8_t* buffer = (uint8_t*) m_malloc(diplay_size_buffer);

    float real_part, imaginary_part;
    float complex c;
    int m, colour;
    for (int x = 0; x < width; x++) {
        for (int y = 0; y < height; y++) {
            real_part = real_start + ((float) x / (float) width) * (real_end - real_start);
            imaginary_part = imaginary_start + ((float) y / (float) height) * (imaginary_end - imaginary_start);
            c = real_part + imaginary_part * I;
            m =  mandelbrot_internal(c);
            colour = 255 - (int)((m * 255) / ITERATIONS);
            colour = get_colour(colour, colour_base[0]);
            buffer[(x + width*y)*2 + 1] = colour & 0xFF; 
            buffer[(x + width*y)*2 + 0] = (colour >> 8) & 0xFF;
        }
    }

    return mp_obj_new_bytearray_by_ref(diplay_size_buffer, buffer);
}

// Define a Python reference to the function above
STATIC MP_DEFINE_CONST_FUN_OBJ_3(mandelbrot_obj, mandelbrot);

STATIC const mp_rom_map_elem_t mandelbrot_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_mandelbrot) },
    { MP_ROM_QSTR(MP_QSTR_mandelbrot), MP_ROM_PTR(&mandelbrot_obj) },
};
STATIC MP_DEFINE_CONST_DICT(mandelbrot_module_globals, mandelbrot_module_globals_table);

// Define module object.
const mp_obj_module_t mandelbrot_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&mandelbrot_module_globals,
};

// Register the module to make it available in Python.
// Note: the "1" in the third argument means this module is always enabled.
MP_REGISTER_MODULE(MP_QSTR_mandelbrot, mandelbrot_user_cmodule, 1);