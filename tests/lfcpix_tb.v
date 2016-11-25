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
    .SRAM_WE_B(SRAM_WE_B)
 
);   

//SRAM Model
reg [15:0] sram [1048576-1:0];
assign SRAM_IO = !SRAM_OE_B ? sram[SRAM_A] : 16'hzzzz;
always@(negedge SRAM_WE_B)
    sram[SRAM_A] <= SRAM_IO;

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
