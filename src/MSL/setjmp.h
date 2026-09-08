#ifndef MSL_SETJMP_H
#define MSL_SETJMP_H

#include <Runtime/Gecko_setjmp.h> // IWYU pragma: export

typedef __jmp_buf jmp_buf[1];

#define setjmp(env) __setjmp(env)

#endif
