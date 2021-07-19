
// Include the header file to get access to the MicroPython API
#include "py/runtime.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

STATIC const uint16_t color_palette[38] = {
   0, 8192, 8960, 25856, 26624, 43520, 60416, 60928, 12545, 29441, 62721, 14082, 14338, 31490, 47874, 47874, 64002, 64002, 14859, 30987, 47371, 63755, 14612, 14356, 30740, 47132, 63260, 63260, 14117, 14117, 30509, 30253, 46637, 46645, 31086, 64414, 32199, 65535
};

STATIC uint8_t get_color_index(uint16_t color) {
    for(int i = 0; i < 38; i++)
        if(color == color_palette[i])
            return i;
    return 0;
}

typedef struct _mp_obj_doom_fire_t {
    mp_obj_base_t base;
    mp_obj_t buf_obj; // need to store this to prevent GC from reclaiming buf
    void *buf;
    uint16_t width, height;
} mp_obj_doom_fire_t;

STATIC mp_obj_t doom_fire_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 3, 3, false);

    mp_obj_doom_fire_t *o = m_new_obj(mp_obj_doom_fire_t);
    o->base.type = type;
    o->buf_obj = args[0];

    mp_buffer_info_t bufinfo;
    mp_get_buffer_raise(args[0], &bufinfo, MP_BUFFER_WRITE);
    o->buf = bufinfo.buf;

    uint16_t *buf = (uint16_t *) bufinfo.buf;

    o->width = mp_obj_get_int(args[1]);
    o->height = mp_obj_get_int(args[2]);    

    memset(bufinfo.buf, 0, bufinfo.len);

    uint16_t strength = color_palette[5 + (rand() % 33)];

    for (int j=0; j < o->width; j++) {
        buf[(o->height-1) + o->width * j] = strength;
    }

    return MP_OBJ_FROM_PTR(o);
}

STATIC mp_obj_t doom_fire_update(mp_obj_t self_obj) {
    mp_obj_doom_fire_t *self = MP_OBJ_TO_PTR(self_obj);

    uint16_t width = self->width;
    uint16_t height = self->height;

    uint16_t *buff = (uint16_t *) self->buf;

    int decay, newFireValue, value, newJ;
    for (int j=0; j < width; j++) {
        for (int i=0; i < height - 1; i++) {
            decay = (rand() % 3);
            value = get_color_index(buff[(i + 1) + width * j]);
            newFireValue = value - (decay & 1);

            //  If the J value is less than 0, it will change the other
            // side of the fire
            //  If it is greater than the size of the width of the fire,
            // the same will happen
            newJ = j-decay+1;
            newJ = newJ < 0 ? width - 1 + newJ : newJ;
            newJ = newJ >= width ? newJ - width - 1 : newJ; 
            buff[i + width * newJ] = color_palette[newFireValue >= 0 ? newFireValue : 0];
        }
    }

    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(doom_fire_update_obj, doom_fire_update);

STATIC const mp_rom_map_elem_t doom_fire_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_update), MP_ROM_PTR(&doom_fire_update_obj) },
};
STATIC MP_DEFINE_CONST_DICT(doom_fire_locals_dict, doom_fire_locals_dict_table);

STATIC const mp_obj_type_t mp_type_doom_fire = {
    { &mp_type_type },
    .name = MP_QSTR_DoomFire,
    .make_new = doom_fire_make_new,
    .locals_dict = (mp_obj_dict_t *)&doom_fire_locals_dict,
};

STATIC const mp_rom_map_elem_t doom_fire_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_doom_fire) },
    { MP_ROM_QSTR(MP_QSTR_DoomFire), MP_ROM_PTR(&mp_type_doom_fire) },
};
STATIC MP_DEFINE_CONST_DICT(doom_fire_module_globals, doom_fire_module_globals_table);

// Define module object.
const mp_obj_module_t doom_fire_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&doom_fire_module_globals,
};

// Register the module to make it available in Python.
// Note: the "1" in the third argument means this module is always enabled.
MP_REGISTER_MODULE(MP_QSTR_doom_fire, doom_fire_user_cmodule, 1);