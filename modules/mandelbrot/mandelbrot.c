
// Include the header file to get access to the MicroPython API
#include "py/runtime.h"

// Convert RGB to RGB565
STATIC uint16_t rgb_to_rgb565(uint8_t r, uint8_t g, uint8_t b) {
     return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
}

//Calculate Mandelbrot
STATIC uint mandelbrot_internal(float c_real, float c_imaginary, uint iterations) {
    float z_real = 0;
    float z_imaginary = 0;
    float z_real2 = 0;
    float z_imaginary2 = 0;

    uint n = 0;
    while (z_real2 + z_imaginary2 <= 4 && n < iterations) {
        z_imaginary = (z_real + z_real) * z_imaginary + c_imaginary;
        z_real = z_real2 - z_imaginary2 + c_real;
        z_real2 = z_real * z_real;
        z_imaginary2 = z_imaginary * z_imaginary;
        n += 1;
    }
    return n;
}

// Choose what color to return
STATIC uint16_t get_colour(uint colour, char colour_base) {
    if(colour_base == 0x72){ //"r"
        return rgb_to_rgb565(colour, 0, 0);
    }
    if(colour_base == 0x67) { //"g"
        return rgb_to_rgb565(0, colour, 0);
    }
    return rgb_to_rgb565(0, 0, colour);
}

STATIC void madelbrot_write_into(
                                uint width,
                                uint height, 
                                float real_start, 
                                float real_end, 
                                float imaginary_end, 
                                float imaginary_start, 
                                uint iterations,
                                char colour_base,
                                uint8_t* buffer
                            ) 
{
    float real_part, imaginary_part;
    uint m;
    uint16_t colour;
    for (int x = 0; x < width; x++) {
        for (int y = 0; y < height; y++) {
            real_part = real_start + ((float) x / (float) width) * (real_end - real_start);
            imaginary_part = imaginary_start + ((float) y / (float) height) * (imaginary_end - imaginary_start);
            m =  mandelbrot_internal(real_part, imaginary_part, iterations);
            colour = 255 - (int)((m * 255) / iterations);
            colour = get_colour(colour, colour_base);
            buffer[(x + width*y)*2 + 1] = colour & 0xFF; 
            buffer[(x + width*y)*2 + 0] = (colour >> 8) & 0xFF;
        }
    }
}

// Mandelbrot Python interface
STATIC void _mandelbrot_into(uint width, uint height, uint8_t* buffer, uint iterations, size_t n_args, const mp_obj_t *args) 
{
    // Extract the tuple from the MicroPython input object
    mp_obj_t *tuple; 

    char * colour_base = (char *) mp_obj_str_get_str(args[1]);

    //Tuple of boundries
    mp_obj_get_array_fixed_n(args[2], 4, &tuple);
    float real_start = mp_obj_get_float(tuple[0]);
    float real_end = mp_obj_get_float(tuple[1]);
    float imaginary_start = mp_obj_get_float(tuple[2]);
    float imaginary_end = mp_obj_get_float(tuple[3]);

    madelbrot_write_into(width, height, real_start, real_end, imaginary_start, imaginary_end, iterations, colour_base[0], buffer);
}

// Mandelbrot Python interface
STATIC mp_obj_t mandelbrot(size_t n_args, const mp_obj_t *args) 
{
    mp_obj_t *tuple; 
    
    //Tuple of resolution
    mp_obj_get_array_fixed_n(args[0], 2, &tuple);
    uint width = mp_obj_get_int(tuple[0]);
    uint height = mp_obj_get_int(tuple[1]);

    uint diplay_size_buffer = width * height * 2;

    uint iterations = 10;
    if(n_args == 4) {
        iterations = mp_obj_get_int(args[3]);
    }

    uint8_t* buffer = (uint8_t*) m_malloc(diplay_size_buffer);
    _mandelbrot_into(width, height, buffer, iterations, n_args, args);

    return mp_obj_new_bytearray_by_ref(diplay_size_buffer, buffer);
}
// Define a Python reference to the function above
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mandelbrot_obj, 3, 4, mandelbrot);

// Mandelbrot write into buffer Python interface. Avoid allocation
STATIC mp_obj_t mandelbrot_into(size_t n_args, const mp_obj_t *args) 
{
    mp_obj_t *tuple; 
    
    //Tuple of resolution
    mp_obj_get_array_fixed_n(args[0], 2, &tuple);
    int width = mp_obj_get_int(tuple[0]);
    int height = mp_obj_get_int(tuple[1]);

    //Buffer to write into
    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(args[3], &bufinfo, MP_BUFFER_WRITE);
    if(bufinfo.len != width * height * 2) {
        mp_raise_ValueError(MP_ERROR_TEXT("Buffer must have size of width * height * 2"));
    }

    //Number of iterations
    uint iterations = 10;
    if(n_args == 5) {
        iterations = mp_obj_get_int(args[4]);
    }

    _mandelbrot_into(width, height, bufinfo.buf, iterations, n_args, args);

    return mp_obj_new_int(bufinfo.len);
}

// Define a Python reference to the function above
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mandelbrot_into_obj, 4, 5, mandelbrot_into);

STATIC const mp_rom_map_elem_t mandelbrot_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_mandelbrot) },
    { MP_ROM_QSTR(MP_QSTR_mandelbrot), MP_ROM_PTR(&mandelbrot_obj) },
    { MP_ROM_QSTR(MP_QSTR_mandelbrot_into), MP_ROM_PTR(&mandelbrot_into_obj) },
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