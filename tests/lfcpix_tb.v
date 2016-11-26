/**
 * ------------------------------------------------------------
 * Copyright (c) SILAB , Physics Institute of Bonn University 
 * ------------------------------------------------------------
 */

`timescale 1ps / 1ps

`include "firmware/src/lfcpix.v"
 
module tb (
    input wire FCLK_IN, 

    //full speed 
    inout wire [7:0] BUS_DATA,
    input wire [15:0] ADD,
    input wire RD_B,
    input wire WR_B,
    
    //high speed
    inout wire [7:0] FD,
    input wire FREAD,
    input wire FSTROBE,
    input wire FMODE
);   

wire [19:0] SRAM_A;
wire [15:0] SRAM_IO;
wire SRAM_BHE_B;
wire SRAM_BLE_B;
wire SRAM_CE1_B;
wire SRAM_OE_B;
wire SRAM_WE_B;

wire SOUT, SIN, LDPIX, CKCONF, LDDAC, SR_EN, RESET, INJECTION;

lfcpix fpga (
    .FCLK_IN(FCLK_IN),
        
    .BUS_DATA(BUS_DATA), 
    .ADD(ADD), 
    .RD_B(RD_B), 
    .WR_B(WR_B), 
    .FDATA(FD), 
    .FREAD(FREAD), 
    .FSTROBE(FSTROBE), 
    .FMODE(FMODE),

    .SRAM_A(SRAM_A), 
    .SRAM_IO(SRAM_IO), 
    .SRAM_BHE_B(SRAM_BHE_B), 
    .SRAM_BLE_B(SRAM_BLE_B), 
    .SRAM_CE1_B(SRAM_CE1_B), 
    .SRAM_OE_B(SRAM_OE_B), 
    .SRAM_WE_B(SRAM_WE_B),
    
    .CCPD_SOUT(SOUT),   
    .CCPD_SIN(SIN),
    .CCPD_LDPIX(LDPIX),
    .CCPD_CKCONF(CKCONF),  
    .CCPD_LDDAC(LDDAC),  
	.CCPD_SR_EN(SR_EN),
    .CCPD_RESET(RESET),
    .CCPD_INJECTION(INJECTION)
    
);   

//SRAM Model
reg [15:0] sram [1048576-1:0];
assign SRAM_IO = !SRAM_OE_B ? sram[SRAM_A] : 16'hzzzz;
always@(negedge SRAM_WE_B)
    sram[SRAM_A] <= SRAM_IO;

struct packed{
    logic [2755:0] Pixels;
    logic [0:0] REGULATOR_EN;
    logic [0:0] BUFFER_EN;
    logic [17:0] SW_INJ;
    logic [35:0] SW_MON;
    logic [9:0] MONITOR_EN_ANA;
    logic [9:0] PREAMP_EN_ANA;
    logic [0:0] PREAMP_EN;
    logic [0:0] MONITOR_EN;
    logic [0:0] INJECT_EN;
    logic [3:0] TRIM_EN;
    logic [35:0] INJ_EN_AnaPassive;
    logic [5:0] IBCS2;
    logic [5:0] LSBdacL2;
    logic [5:0] LSBdacL;
    logic [5:0] WGT;
    logic [5:0] IBCS;
    logic [5:0] IBOTA;
    logic [5:0] VSTRETCH;
    logic [5:0] IComp;
    logic [5:0] VPLoad;
    logic [5:0] VPFoll;
    logic [5:0] VPFB;
    logic [5:0] VAmp;
    logic [5:0] BLRes;
} lfcpix_sr;

logic [2755:0] INJECT_EN, PREAMP_EN;

always@(posedge CKCONF or posedge RESET or posedge INJECTION)
    if(RESET)
        lfcpix_sr <= 0;
    else if(INJECTION)
        lfcpix_sr.Pixels <= ~(INJECT_EN & PREAMP_EN) & lfcpix_sr.Pixels;
    else
        lfcpix_sr <= {lfcpix_sr[$bits(lfcpix_sr)-1:0], SIN};

assign SOUT = lfcpix_sr[$bits(lfcpix_sr)-1];
         

always@(*)
    if(lfcpix_sr.INJECT_EN & LDPIX)
        INJECT_EN = lfcpix_sr.Pixels;

always@(*)
    if(lfcpix_sr.PREAMP_EN & LDPIX)
        PREAMP_EN = lfcpix_sr.Pixels;
 
initial begin
    
    $dumpfile("lfcpix.vcd");
    $dumpvars(0);
    
    //force dut.i_output_data.iser_div.cnt = 4'b0;
    //#10 force CLK_DATA = 4'b0;
    //#100000 force CLK_DATA = 4'b1;
    //#10000 release CLK_DATA;
    //#50000 release dut.i_output_data.iser_div.cnt;

end

endmodule
