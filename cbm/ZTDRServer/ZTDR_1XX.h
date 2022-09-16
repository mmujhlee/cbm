//==============================================================================
//
// Title:		ZTDR_1XX.h
// Release:		1.1.2 (01/13/2015)
// Purpose:		ZTDR driver module and DLL functionality (v1.x.x)
//
// Copyright:	(c) 2015, HYPERLABS INC. All rights reserved.
//
//==============================================================================

#ifndef __ZTDR_1XX_H__
#define __ZTDR_1XX_H__

#ifdef __cplusplus
extern "C" {
#endif

	
//==============================================================================
// Include files
					 
#include "FTD2XX.h"

	
//==============================================================================
// Constants	


//==============================================================================
// Types

typedef unsigned int UINT32;
typedef unsigned short UINT16;
typedef unsigned char UINT8;

struct	_delay16
{
	UINT16 frac_val;
	UINT16 int_val;
};

struct	_delay8
{
	UINT8 b0;
	UINT8 b1;
	UINT8 b2;
	UINT8 b3;
};


union _timeinf
{
	UINT32 time;
	struct _delay16 time_s;
	struct _delay8 time_b;
};

typedef union _timeinf timeinf;

	
//==============================================================================
// External variables


//==============================================================================
// Global functions

// User-facing functions
int		__stdcall 	initDevice (void);
int 	__stdcall	vertCal (void);
int 	__stdcall	setEnviron (int x, int y, double start, double end, double k, int rec);
int 	__stdcall	setRefX (double x);
int 	__stdcall	acquireWaveform (int numAvg);
int 	__stdcall	dumpFile (char *filename);
double	__stdcall	fetchDataX (int idx);
double	__stdcall	fetchDataY (int idx);

// Other driver functions
void 	__stdcall	calAcquireWaveform (int calStepIndex);
void 	__stdcall	calDAC (void);
void 	__stdcall	calFindDiscont (void);
void 	__stdcall	calFindMean (int calStepIndex);
int 	__stdcall	calFindStepcount (void);
void 	__stdcall	calReconstructData (void);
void 	__stdcall	calSetParams (void);
void 	__stdcall	calSetupTimescale (void);
int 	__stdcall	calTimebase (void); 
double 	__stdcall	meanArray (void);
void 	__stdcall	openDevice (void);
void 	__stdcall	reconstructData (double offset);
void 	__stdcall	setupTimescale (void);
void 	__stdcall	vertCalTimescale (void);
void 	__stdcall	vertCalZero (double windowStart);
int 	__stdcall	vertCalWriteParams (void);
int 	__stdcall	writeParams (void);

// USBFIFO functionality
char 	__stdcall	ftrdbyte (void);
void 	__stdcall	ftwrbyte (char ch);
int 	__stdcall	usbfifo_acquire (UINT8 *ret_val, UINT8 arg);
void 	__stdcall	usbfifo_close (void);
void 	__stdcall	usbfifo_getcomspd (char *buf, int len);
int 	__stdcall	usbfifo_gethostbps (void);
void 	__stdcall	usbfifo_getid (char *buf, int len);
int 	__stdcall	usbfifo_open (void);
int 	__stdcall	usbfifo_readblock (UINT8 block_no, UINT16 *buf);
int 	__stdcall	usbfifo_setparams (UINT8 freerun_en, UINT16 calstart, UINT16 calend, timeinf tmstart, timeinf tmend, UINT16 stepcount,
					   UINT16 strobecount, UINT8 noversample, UINT16 record_len, UINT16 dac0, UINT16 dac1, UINT16 dac2);


#ifdef __cplusplus
}
#endif

#endif  /* ndef __driver_H__ */
