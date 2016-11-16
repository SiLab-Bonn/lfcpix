/**
 * ------------------------------------------------------------
 * Copyright (c) All rights reserved 
 * SiLab , Physics Institute of Bonn University , All Right 
 * ------------------------------------------------------------
 *
 * SVN revision information:
 *  $Rev::                       $:
 *  $Author::                    $:
 *  $Date::                      $:
 */
 
`timescale 1ps / 1ps
`default_nettype none

module lfcpix (
    
    input wire FCLK_IN, // 48MHz
    
    //full speed 
    inout wire [7:0] BUS_DATA,
    input wire [15:0] ADD,
    input wire RD_B,
    input wire WR_B,
    
    //high speed
    inout wire [7:0] FDATA,
    input wire FREAD,
    input wire FSTROBE,
    input wire FMODE,

    //debug ports
    //output wire [15:0] DEBUG_D,
    //output wire [10:0] MULTI_IO, // Pin 1-11, 12: not connected, 13, 15: DGND, 14, 16: VCC_3.3V
  
    //LED
    output wire [4:0] LED,
    
    //SRAM
    output wire [19:0] SRAM_A,
    inout wire [15:0] SRAM_IO,
    output wire SRAM_BHE_B,
    output wire SRAM_BLE_B,
    output wire SRAM_CE1_B,
    output wire SRAM_OE_B,
    output wire SRAM_WE_B,
	 
    //FADC CONFIG
    output ADC_CSN,
    output ADC_SCLK,
    output ADC_SDI,
    input ADC_SD0,

    output ADC_ENC_P,
    output ADC_ENC_N,
    input ADC_DCO_P,
    input ADC_DCO_N,
    input ADC_FCO_P,
    input ADC_FCO_N,

    input [3:0] ADC_OUT_P,
    input [3:0] ADC_OUT_N,
	 
    // Triggers
    input wire [2:0] LEMO_RX,
    output wire [2:0] TX, // TX[0] == RJ45 trigger clock output, TX[1] == RJ45 busy output
    input wire RJ45_RESET,
    input wire RJ45_TRIGGER,

    // CCPD
	input wire CCPD_SOUT,       //DIN0
    output wire CCPD_SIN,      //DOUT3
    output wire CCPD_LDPIX,     //DOUT4
    output wire CCPD_CKCONF,    //DOUT1
    output wire CCPD_LDDAC,     //DOUT0
	output wire CCPD_SR_EN,     //DOUT2
    output wire CCPD_RESET,    //DOUT5
	output wire CCPD_THON,      //DOUT6
    input wire CCPD_TDC,        //DIN1
	output wire CCPD_INJECTION, //INJ
    output wire [3:0] CCPD_DEBUG,     //DEBUG DOUT9, 10, 11, 12
    // I2C
    inout SDA,
    inout SCL
);


// assignments for SCC_HVCMOS2FE-I4B_V1.0 and SCC_HVCMOS2FE-I4B_V1.1
// CCPD

// Assignments
wire BUS_RST;
(* KEEP = "{TRUE}" *)
wire BUS_CLK;
(* KEEP = "{TRUE}" *)
wire SPI_CLK;
wire CLK_40;
wire RX_CLK;
wire RX_CLK2X;
wire CLK_LOCKED;
wire ADC_ENC;

wire TDC_OUT, TDC_TRIG_OUT,TDC_TDC_OUT;

// TLU
wire TLU_BUSY; // busy signal to TLU to de-assert trigger
wire TLU_CLOCK;
wire TRIGGER_ACCEPTED_FLAG; // from TLU FSM
wire TRIGGER_ENABLE; // from CMD FSM
wire TRIGGER_ACKNOWLEDGE_FLAG; // to TLU FSM

wire CCPD_GATE,CCPD_PULSE_GATE;
reg CCPD_PULSE_GATE_FF;
always @ (posedge CLK_40)
begin
    CCPD_PULSE_GATE_FF <= CCPD_PULSE_GATE;
end
assign TRIGGER_ACKNOWLEDGE_FLAG = ~CCPD_PULSE_GATE & CCPD_PULSE_GATE_FF;

reg CCPD_PULSE_GATE_RISING_FF;
always @ (posedge ADC_ENC)
begin
    CCPD_PULSE_GATE_RISING_FF <= CCPD_PULSE_GATE;
end

wire ADC_TRIG_GATE;
assign ADC_TRIG_GATE = CCPD_PULSE_GATE & ~CCPD_PULSE_GATE_RISING_FF; //rising edge
wire ADC_TRIG;

// LEMO & RJ45 Tx
assign TX[0] = TLU_CLOCK; // trigger clock; also connected to RJ45 output
assign TX[1] = TLU_BUSY; // TLU_BUSY signal; also connected to RJ45 output. Asserted when TLU FSM has accepted a trigger or when CMD FSM is busy. 
assign TX[2] = CCPD_INJECTION;

// ------- RESRT/CLOCK  ------- //
reset_gen ireset_gen(.CLK(BUS_CLK), .RST(BUS_RST));



clk_gen iclkgen(
    .U1_CLKIN_IN(FCLK_IN),
    .U1_RST_IN(1'b0),
    .U1_CLKIN_IBUFG_OUT(),
    .U1_CLK0_OUT(BUS_CLK), // DCM1: 48MHz USB/SRAM clock
    .U1_STATUS_OUT(),
    .U2_CLKFX_OUT(CLK_40),  // DCM2: 40MHz command clock
    .U2_CLKDV_OUT(ADC_ENC), // DCM2: 16MHz SERDES clock  //10MH adc
    .U2_CLK0_OUT(RX_CLK),   // DCM2: 160MHz data clock ADC clock
    .U2_CLK90_OUT(),
    .U2_CLK2X_OUT(RX_CLK2X), // DCM2: 320MHz data recovery clock
    .U2_LOCKED_OUT(CLK_LOCKED),
    .U2_STATUS_OUT()
);



// -------  MODULE ADREESSES  ------- //
localparam FIFO_BASEADDR = 16'h8100;
localparam FIFO_HIGHADDR = 16'h8200-1;

localparam TLU_BASEADDR = 16'h8200;
localparam TLU_HIGHADDR = 16'h8300-1;

localparam GPIO_RX_BASEADDR = 16'h8800;
localparam GPIO_RX_HIGHADDR = 16'h8840-1;

//CCPD_ADC
localparam SPI_ADC_BASEADDR = 16'h8840;                 // 0x8840
localparam SPI_ADC_HIGHADDR = SPI_ADC_BASEADDR + 47;    // 0x886f

localparam ADC_RX_CH0_BASEADDR = SPI_ADC_HIGHADDR+1;       // 0x8870
localparam ADC_RX_CH0_HIGHADDR = ADC_RX_CH0_BASEADDR + 47; // 0x889f

// CCPD
localparam CCPD_SPI_BASEADDR = 16'h8900;
localparam CCPD_SPI_HIGHADDR = 16'h8Aff;

localparam CCPD_SPI_RX_BASEADDR = 16'h8B00;
localparam CCPD_SPI_RX_HIGHADDR = 16'h8Bff;

localparam CCPD_GPIO_SW_BASEADDR = 16'h8c00;
localparam CCPD_GPIO_SW_HIGHADDR = 16'h8c1f;

localparam CCPD_TDC_BASEADDR = 16'h8c20;
localparam CCPD_TDC_HIGHADDR = 16'h8c3f;

localparam CCPD_PULSE_GATE_BASEADDR= 16'h8c40;
localparam CCPD_PULSE_GATE_HIGHADDR= 16'h8c4f;

localparam CCPD_PULSE_INJ_BASEADDR= 16'h8c50;
localparam CCPD_PULSE_INJ_HIGHADDR= 16'h8c5f;

localparam CCPD_PULSE_THON_BASEADDR= 16'h8c60;
localparam CCPD_PULSE_THON_HIGHADDR= 16'h8c6f;

localparam CCPD_GPIO_TH_BASEADDR = 16'h8c80;
localparam CCPD_GPIO_TH_HIGHADDR = 16'h8c9f;

localparam CCPD_GPIO_TH2_BASEADDR = 16'h8ca0;
localparam CCPD_GPIO_TH2_HIGHADDR = 16'h8ccf;
    
//localparam ADC_RX_CH1_BASEADDR = ADC_RX_CH0_HIGHADDR + 1;  // 0x0040
//localparam ADC_RX_CH1_HIGHADDR = ADC_RX_CH1_BASEADDR + 15; // 0x004f
    
//localparam ADC_RX_CH2_BASEADDR = ADC_RX_CH1_HIGHADDR + 1;  // 0x0050
//localparam ADC_RX_CH2_HIGHADDR = ADC_RX_CH2_BASEADDR + 15; // 0x005f
    
//localparam ADC_RX_CH3_BASEADDR = ADC_RX_CH2_HIGHADDR + 1;  // 0x0060
//localparam ADC_RX_CH3_HIGHADDR = ADC_RX_CH3_BASEADDR + 15; // 0x006f


// -------  BUS SYGNALING  ------- //
wire [15:0] BUS_ADD;
assign BUS_ADD = ADD - 16'h4000;
wire BUS_RD, BUS_WR;
assign BUS_RD = ~RD_B;
assign BUS_WR = ~WR_B;


// -------  USER MODULES  ------- //

wire FIFO_NOT_EMPTY; // raised, when SRAM FIFO is not empty
wire FIFO_FULL, FIFO_NEAR_FULL; // raised, when SRAM FIFO is full / near full
wire FIFO_READ_ERROR; // raised, when attempting to read from SRAM FIFO when it is empty

wire [3:0] NOT_CONNECTED_RX;
wire ADC_SEL, TLU_SEL, CCPD_TDC_SEL,CCPD_RX_SEL;
gpio 
#( 
    .BASEADDR(GPIO_RX_BASEADDR),
    .HIGHADDR(GPIO_RX_HIGHADDR),
    .IO_WIDTH(8),
    .IO_DIRECTION(8'hff)
) i_gpio_rx (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),
    .IO({NOT_CONNECTED_RX,ADC_SEL,CCPD_TDC_SEL,CCPD_RX_SEL,TLU_SEL})
);

wire TLU_FIFO_READ;
wire TLU_FIFO_EMPTY;
wire [31:0] TLU_FIFO_DATA;
wire TLU_FIFO_PEEMPT_REQ;
wire [31:0] TIMESTAMP;

tlu_controller #(
    .BASEADDR(TLU_BASEADDR),
    .HIGHADDR(TLU_HIGHADDR),
    .DIVISOR(8)
) i_tlu_controller (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),
    
    .TRIGGER_CLK(CLK_40),
    
    .FIFO_READ(TLU_FIFO_READ),
    .FIFO_EMPTY(TLU_FIFO_EMPTY),
    .FIFO_DATA(TLU_FIFO_DATA),
    
    .FIFO_PREEMPT_REQ(TLU_FIFO_PEEMPT_REQ),
    
    .TRIGGER({7'b0,TDC_TRIG_OUT}),
    .TRIGGER_VETO({7'b0,FIFO_FULL}),
	 
    .TRIGGER_ACKNOWLEDGE(TRIGGER_ACKNOWLEDGE_FLAG),
    .TRIGGER_ACCEPTED_FLAG(TRIGGER_ACCEPTED_FLAG),
	 
    .TLU_TRIGGER(RJ45_TRIGGER),
    .TLU_RESET(RJ45_RESET),
    .TLU_BUSY(TLU_BUSY),
    .TLU_CLOCK(TLU_CLOCK),
    
    .TIMESTAMP(TIMESTAMP)
);
wire TRIGGER_ACCEPTED_FLAG_SYNC;
cdc_pulse_sync ext_start_sync (.clk_in(CLK_40), .pulse_in(TRIGGER_ACCEPTED_FLAG), .clk_out(SPI_CLK), .pulse_out(TRIGGER_ACCEPTED_FLAG_SYNC)); 
/*
reg [31:0] CNT;
always @ (posedge CLK_40) begin
    if (BUS_RST)
        CNT <= 0;
    else if(TRIGGER_ACCEPTED_FLAG)
        CNT <= 1;
    else if (CNT == 50)
	     CNT <= 0;
    else if(CNT != 0) 
        CNT <= CNT + 1;
end
assign TRIGGER_ACCEPTED_FLAG_SYNC = (CNT !=0);
*/
///////////////////////////
// ADC
wire ADC_EN;

    spi 
    #( 
        .BASEADDR(SPI_ADC_BASEADDR), 
        .HIGHADDR(SPI_ADC_HIGHADDR), 
        .MEM_BYTES(2) 
    )  i_spi_adc
    (
		 .BUS_CLK(BUS_CLK),
		 .BUS_RST(BUS_RST),
		 .BUS_ADD(BUS_ADD),
		 .BUS_DATA(BUS_DATA),
		 .BUS_RD(BUS_RD),
		 .BUS_WR(BUS_WR),
		 .SPI_CLK(SPI_CLK),
		 
		 .EXT_START(1'b0),

		 .SCLK(ADC_SCLK),
       .SDI(ADC_SDI),
       .SDO(ADC_SD0),
       .SEN(ADC_EN),
       .SLD()
    );
    assign ADC_CSN = !ADC_EN;
    wire [13:0] ADC_IN [3:0];
    wire ADC_DCO, ADC_FCO;
    gpac_adc_iobuf i_gpac_adc_iobuf
    (
        .ADC_CLK(RX_CLK),
		  
        .ADC_DCO_P(ADC_DCO_P), .ADC_DCO_N(ADC_DCO_N),
        .ADC_DCO(ADC_DCO),
    
        .ADC_FCO_P(ADC_FCO_P), .ADC_FCO_N(ADC_FCO_N),
        .ADC_FCO(ADC_FCO),
    
        .ADC_ENC(ADC_ENC), 
        .ADC_ENC_P(ADC_ENC_P), .ADC_ENC_N(ADC_ENC_N),
    
        .ADC_IN_P(ADC_OUT_P), .ADC_IN_N(ADC_OUT_N),
        
        .ADC_IN0(ADC_IN[0]), 
        .ADC_IN1(ADC_IN[1]), 
        .ADC_IN2(ADC_IN[2]), 
        .ADC_IN3(ADC_IN[3])
    );

    wire FIFO_EMPTY_ADC, FIFO_READ_ADC,ADC_ERROR;
    wire [31:0] FIFO_DATA_ADC;
	 
    wire [13:0] CCPD_ADC_TH;
	 wire CCPD_ADC_TH_SW,ADC_TRIG_STATUS;
	 reg adc_trig_ff;
    gpio #(
         .BASEADDR(CCPD_GPIO_TH_BASEADDR),
         .HIGHADDR(CCPD_GPIO_TH_HIGHADDR),
         .IO_WIDTH(16),
         .IO_DIRECTION(16'hff)
    ) i_gpio_th (
        .BUS_CLK(BUS_CLK), 
        .BUS_RST(BUS_RST), 
        .BUS_ADD(BUS_ADD),
        .BUS_DATA(BUS_DATA),
        .BUS_RD(BUS_RD),
        .BUS_WR(BUS_WR),
        .IO({ADC_TRIG_STATUS ,CCPD_ADC_TH_SW, CCPD_ADC_TH})
    );
    always@(posedge ADC_ENC)
        adc_trig_ff <= (ADC_IN[0] < CCPD_ADC_TH);
    assign ADC_TRIG_STATUS =(ADC_IN[0] < CCPD_ADC_TH);
    wire ADC_TRIG_TH;
    assign ADC_TRIG_TH = ADC_TRIG_STATUS && adc_trig_ff == 0;
    assign ADC_TRIG= CCPD_ADC_TH_SW? ADC_TRIG_TH : ADC_TRIG_GATE;

        gpac_adc_rx 
        #(
            .BASEADDR(ADC_RX_CH0_BASEADDR), 
            .HIGHADDR(ADC_RX_CH0_HIGHADDR),
            .ADC_ID(2'b11), 
            .HEADER_ID(1'b1) 
        ) i_gpac_adc_rx
        (
            .ADC_ENC(ADC_ENC),
            .ADC_IN(ADC_IN[0]),

            .ADC_SYNC(1'b0),
            .ADC_TRIGGER(ADC_TRIG),
				//.ADC_TRIGGER(ADC_TRIGGER),

            .BUS_CLK(BUS_CLK),
            .BUS_RST(BUS_RST),
            .BUS_ADD(BUS_ADD),
            .BUS_DATA(BUS_DATA),
            .BUS_RD(BUS_RD),
            .BUS_WR(BUS_WR), 

            .FIFO_READ(FIFO_READ_ADC),
            .FIFO_EMPTY(FIFO_EMPTY_ADC),
            .FIFO_DATA(FIFO_DATA_ADC),

            .LOST_ERROR(ADC_ERROR)
        );
//////////////////////
// CCPD
wire SPI_CLK_CE;

// fifo
wire CCPD_TDC_FIFO_READ,CCPD_TDC_FIFO_EMPTY;
wire [31:0] CCPD_TDC_FIFO_DATA;
wire CCPD_SPI_RX_FIFO_READ,CCPD_SPI_RX_FIFO_EMPTY;
wire [31:0] CCPD_SPI_RX_FIFO_DATA;


//GPIO_SW
wire CCPD_SW_GATE_NEG,CCPD_SW_TEST_HIT,CCPD_SW_HIT, CCPD_SW_LDDAC, CCPD_SW_LDPIX;
wire CCPD_SW_THON_NEG,CCPD_SW_EXT_START_TLU;
wire NC_CCPD_GPIO;

wire CCPD_SLD,CCPD_SCLK,CCPD_SEN,CCPD_SDI;
wire CCPD_PULSE_THON, CCPD_GATE_EXT_START;

assign CCPD_RESET= 0;
assign CCPD_SR_EN = (CCPD_GATE & CCPD_SW_HIT)| CCPD_SW_TEST_HIT; // TODO need to add a gate for external trigger.
assign CCPD_LDPIX = CCPD_SLD & CCPD_SW_LDPIX;
assign CCPD_LDDAC = CCPD_SLD & CCPD_SW_LDDAC;
//assign CCPD_SIN = (~CCPD_SW_LDPIX & ~CCPD_SW_LDDAC) | CCPD_SDI;
assign CCPD_SIN = CCPD_SDI;
assign CCPD_GATE_EXT_START = CCPD_SW_EXT_START_TLU? TRIGGER_ACCEPTED_FLAG_SYNC : (CCPD_SW_GATE_NEG ? ~TDC_TRIG_OUT : CCPD_SLD);
assign CCPD_CKCONF = CCPD_SCLK;

assign CCPD_DEBUG[0] = CCPD_PULSE_GATE; //DOUT 9
assign CCPD_DEBUG[1] = CCPD_GATE_EXT_START; //TRIGGER_ACKNOWLEDGE_FLAG; //DOUT10
assign CCPD_DEBUG[2] = TRIGGER_ACCEPTED_FLAG; //DOUT11
assign CCPD_DEBUG[3] = TDC_TDC_OUT; //DOUT12

assign CCPD_GATE = CCPD_SW_GATE_NEG ? ~CCPD_PULSE_GATE : CCPD_PULSE_GATE;
assign CCPD_THON = CCPD_SW_THON_NEG ? ~CCPD_PULSE_THON : CCPD_PULSE_THON;

//clock_divider #(   /// TODO if 10MHz works, merge with ADC_ENC is better
//    .DIVISOR(4) // 10MHz
//) i_clock_divisor_40MHz_to_1MHz (
//    .CLK(CLK_40),
//    .RESET(1'b0),
//    .CE(SPI_CLK_CE),
//    .CLOCK(SPI_CLK)
//);

assign SPI_CLK = ADC_ENC;

wire CMD_START_FLAG; // sending FE command triggered by external devices
tdc_s3
#(
    .BASEADDR(CCPD_TDC_BASEADDR),
    .HIGHADDR(CCPD_TDC_HIGHADDR),
    .CLKDV(4),
    .DATA_IDENTIFIER(4'b0101)
) i_ccpd_tdc (
    .CLK320(RX_CLK2X),
    .CLK160(RX_CLK),
    .DV_CLK(CLK_40),
    .TDC_IN(CCPD_TDC),
    .TDC_OUT(TDC_TDC_OUT),
	 
    .TRIG_IN(LEMO_RX[0]),
    .TRIG_OUT(TDC_TRIG_OUT),

    .FIFO_READ(CCPD_TDC_FIFO_READ),
    .FIFO_EMPTY(CCPD_TDC_FIFO_EMPTY),
    .FIFO_DATA(CCPD_TDC_FIFO_DATA),

    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),

    .ARM_TDC(CMD_START_FLAG), // arm TDC by sending commands

    .TIMESTAMP(TIMESTAMP[15:0]),
    .EXT_EN(CCPD_PULSE_GATE) 
);

spi
#(         
    .BASEADDR(CCPD_SPI_BASEADDR), 
    .HIGHADDR(CCPD_SPI_HIGHADDR),
    .MEM_BYTES(370) 
) i_ccpd_spi (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),
    .SPI_CLK(SPI_CLK),
    .EXT_START(CCPD_PULSE_GATE),

    .SCLK(CCPD_SCLK),
    .SDI(CCPD_SDI),
    .SDO(CCPD_SOUT),
    .SEN(CCPD_SEN),
    .SLD(CCPD_SLD)
);

fast_spi_rx
#(
        .BASEADDR(CCPD_SPI_RX_BASEADDR), 
        .HIGHADDR(CCPD_SPI_RX_HIGHADDR), 
        .IDENTYFIER(4'b0110)
) i_ccpd_fast_spi_rx
(
    .BUS_CLK(BUS_CLK),                     
    .BUS_RST(BUS_RST),                  
    .BUS_ADD(BUS_ADD),                    
    .BUS_DATA(BUS_DATA),                                       
    .BUS_WR(BUS_WR),                    
    .BUS_RD(BUS_RD),
      
    .SCLK(SPI_CLK),
    .SDI(CCPD_SOUT),
    .SEN(CCPD_SEN),

    .FIFO_READ(CCPD_SPI_RX_FIFO_READ),
    .FIFO_EMPTY(CCPD_SPI_RX_FIFO_EMPTY),
    .FIFO_DATA(CCPD_SPI_RX_FIFO_DATA)
);

gpio 
#( 
    .BASEADDR(CCPD_GPIO_SW_BASEADDR),
    .HIGHADDR(CCPD_GPIO_SW_HIGHADDR),
    .IO_WIDTH(8),
    .IO_DIRECTION(8'hff)
) i_gpio_ccpd_sw (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),
    .IO({NC_CCPD_GPIO,CCPD_SW_EXT_START_TLU,CCPD_SW_THON_NEG,CCPD_SW_GATE_NEG,
         CCPD_SW_TEST_HIT,CCPD_SW_HIT,CCPD_SW_LDDAC,CCPD_SW_LDPIX})
);

pulse_gen
#( 
    .BASEADDR(CCPD_PULSE_GATE_BASEADDR), 
    .HIGHADDR(CCPD_PULSE_GATE_HIGHADDR)
) i_pulse_gen_tdcgate (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),

    .PULSE_CLK(SPI_CLK),
    .EXT_START(CCPD_GATE_EXT_START),
    .PULSE(CCPD_PULSE_GATE)
);

pulse_gen
#( 
    .BASEADDR(CCPD_PULSE_INJ_BASEADDR), 
    .HIGHADDR(CCPD_PULSE_INJ_HIGHADDR)
) i_pulse_gen_inj (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),

    .PULSE_CLK(SPI_CLK),
    .EXT_START(CCPD_PULSE_GATE),
    .PULSE(CCPD_INJECTION)
);

 
pulse_gen
#( 
    .BASEADDR(CCPD_PULSE_THON_BASEADDR), 
    .HIGHADDR(CCPD_PULSE_THON_HIGHADDR)
) i_pulse_gen_thon (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR),

    .PULSE_CLK(SPI_CLK),
    .EXT_START(CCPD_PULSE_GATE),
    .PULSE(CCPD_PULSE_THON)
);


// Arbiter
wire ARB_READY_OUT, ARB_WRITE_OUT;
wire [31:0] ARB_DATA_OUT;
wire [3:0] READ_GRANT;


rrp_arbiter 
#( 
    .WIDTH(4)
) i_rrp_arbiter
(
    .RST(BUS_RST),
    .CLK(BUS_CLK),

    //.WRITE_REQ({~FIFO_EMPTY_ADC ,~CCPD_TDC_FIFO_EMPTY & CCPD_TDC_SEL, ~CCPD_SPI_RX_FIFO_EMPTY & CCPD_RX_SEL, ~TLU_FIFO_EMPTY & TLU_SEL}),
    .WRITE_REQ({~FIFO_EMPTY_ADC & ADC_SEL,~CCPD_TDC_FIFO_EMPTY & CCPD_TDC_SEL, ~CCPD_SPI_RX_FIFO_EMPTY & CCPD_RX_SEL, ~TLU_FIFO_EMPTY & TLU_SEL}),
    .HOLD_REQ({3'b0, TLU_FIFO_PEEMPT_REQ}),
    .DATA_IN({FIFO_DATA_ADC,CCPD_TDC_FIFO_DATA, CCPD_SPI_RX_FIFO_DATA, TLU_FIFO_DATA}),
    .READ_GRANT(READ_GRANT),

    .READY_OUT(ARB_READY_OUT),
    .WRITE_OUT(ARB_WRITE_OUT),
    .DATA_OUT(ARB_DATA_OUT)
);

assign TLU_FIFO_READ = READ_GRANT[0];
assign CCPD_SPI_RX_FIFO_READ = READ_GRANT[1];
assign CCPD_TDC_FIFO_READ = READ_GRANT[2];
assign FIFO_READ_ADC= READ_GRANT[3];

// SRAM
wire USB_READ;
assign USB_READ = FREAD & FSTROBE;

sram_fifo 
#(
    .BASEADDR(FIFO_BASEADDR),
    .HIGHADDR(FIFO_HIGHADDR)
) i_out_fifo (
    .BUS_CLK(BUS_CLK),
    .BUS_RST(BUS_RST),
    .BUS_ADD(BUS_ADD),
    .BUS_DATA(BUS_DATA),
    .BUS_RD(BUS_RD),
    .BUS_WR(BUS_WR), 

    .SRAM_A(SRAM_A),
    .SRAM_IO(SRAM_IO),
    .SRAM_BHE_B(SRAM_BHE_B),
    .SRAM_BLE_B(SRAM_BLE_B),
    .SRAM_CE1_B(SRAM_CE1_B),
    .SRAM_OE_B(SRAM_OE_B),
    .SRAM_WE_B(SRAM_WE_B),

    .USB_READ(USB_READ),
    .USB_DATA(FDATA),

    .FIFO_READ_NEXT_OUT(ARB_READY_OUT),
    .FIFO_EMPTY_IN(!ARB_WRITE_OUT),
    .FIFO_DATA(ARB_DATA_OUT),

    .FIFO_NOT_EMPTY(FIFO_NOT_EMPTY),
    .FIFO_FULL(FIFO_FULL),
    .FIFO_NEAR_FULL(FIFO_NEAR_FULL),
    .FIFO_READ_ERROR(FIFO_READ_ERROR)
);
    
// ------- LEDs  ------- //
parameter VERSION = 0; // all on: 31
//wire SHOW_VERSION;
//
//SRLC16E # (
//    .INIT(16'hF000) // in seconds, MSB shifted first
//) SRLC16E_LED (
//    .Q(SHOW_VERSION),
//    .Q15(),
//    .A0(1'b1),
//    .A1(1'b1),
//    .A2(1'b1),
//    .A3(1'b1),
//    .CE(CE_1HZ),
//    .CLK(CLK_40),
//    .D(1'b0)
//);

// LED assignments
assign LED[0] = 0;
assign LED[1] = 0;
assign LED[2] = 0;
assign LED[3] = 0;
assign LED[4] = 0;
endmodule
