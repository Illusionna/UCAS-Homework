#ifndef _MD5_H_
#define _MD5_H_


#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#define F(X, Y, Z) ((X & Y) | (~X & Z))
#define G(X, Y, Z) ((X & Z) | (Y & ~Z))
#define H(X, Y, Z) (X ^ Y ^ Z)
#define I(X, Y, Z) (Y ^ (X | ~Z))
#define L(X, s) (((X << s) | (X >> (32 - s))) & 0xffffffff)
#define T(x) ((unsigned int)(fabs(sin(x)) * 0x100000000))
#define MATHCAL_H(q, w, e, r) ((q << 0) | (w << 8) | (e << 16) | (r << 24))
#define SWAP(x) ((x >> 24) & 0xff | ((x >> 16) & 0xff) << 8 | ((x >> 8) & 0xff) << 16 | (x & 0xff) << 24)


/**
 * @brief Calculate the md5 hash value.
 * @param input The input string.
 * @param result The result string.
**/
void md5(char *input, char *result);


#endif