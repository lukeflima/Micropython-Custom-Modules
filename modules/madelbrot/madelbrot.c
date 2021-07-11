
// Include the header file to get access to the MicroPython API
#include "py/runtime.h"


STATIC mp_obj_t madelbrot(
                          mp_obj_t resolution_obj, 
                          mp_obj_t colour_obj, 
                          mp_obj_t boundries_obj
                        ) 
{
    
}

// Define a Python reference to the function above
STATIC MP_DEFINE_CONST_FUN_OBJ_3(madelbrot_obj, madelbrot);

STATIC const mp_rom_map_elem_t madelbrot_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_madelbrot) },
    { MP_ROM_QSTR(MP_QSTR_madelbrot), MP_ROM_PTR(&madelbrot_obj) },
};
STATIC MP_DEFINE_CONST_DICT(madelbrot_module_globals, madelbrot_module_globals_table);

// Define module object.
const mp_obj_module_t madelbrot_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&madelbrot_module_globals,
};

// Register the module to make it available in Python.
// Note: the "1" in the third argument means this module is always enabled.
// This "1" can be optionally replaced with a macro like MODULE_Cmadelbrot_ENABLED
// which can then be used to conditionally enable this module.
MP_REGISTER_MODULE(MP_QSTR_madelbrot, madelbrot_user_cmodule, 1);