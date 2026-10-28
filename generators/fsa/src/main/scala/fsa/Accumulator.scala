package fsa

import chisel3._
import chisel3.util._
import fsa.arithmetic.ArithmeticSyntax._
import fsa.arithmetic._

object AccumulatorCmd {
  def width = 3

  def EXP_S1 = 0.U(width.W)

  def EXP_S2 = 1.U(width.W)

  def ACC_SA = 2.U(width.W)

  def ACC = 3.U(width.W)

  def SET_SCALE = 4.U(width.W)

  def RECIPROCAL = 5.U(width.W)
}


class AccumulatorControl extends Bundle {
  val cmd = UInt(AccumulatorCmd.width.W)
}

class Accumulator[A <: Data : Arithmetic]
(
  rows: Int, cols: Int,
  accType: A,
  accGen: () => MacUnit[A, A] with HasMultiCycleIO,
  accLatency: Int = 0
) extends Module {

  val io = IO(new Bundle {
    val ctrl_in = Flipped(Valid(new AccumulatorControl))
    val sa_in = Input(Vec(cols, accType))
    val sram_in = Input(Vec(cols, accType))
    val sram_out = Output(Vec(cols, accType))
  })

  val accUnit = Seq.fill(cols) {
    Module(accGen())
  }
  val scale = Seq.fill(cols) {
    Reg(accType)
  }
  val valid = io.ctrl_in.valid
  val cmd = io.ctrl_in.bits.cmd
  val exp_s1 = cmd === AccumulatorCmd.EXP_S1
  val exp_s2 = cmd === AccumulatorCmd.EXP_S2
  val acc_sa = cmd === AccumulatorCmd.ACC_SA
  val set = cmd === AccumulatorCmd.SET_SCALE
  val reciprocal = cmd === AccumulatorCmd.RECIPROCAL

  /*
    * exp s1: scale <- sa_in * lg2e/sqrt(dk) + 0
    * exp s2: scale <- pow2(scale)
    * acc sa: out <- scale * sram_in + sa_in
    * acc   : out <- scale * sram_in + 0
    * set: scale <- sram_in
  */

  // The accUnit datapath is pipelined (accLatency cycles from inputs to
  // out_accType).  Operands are consumed combinationally at the command
  // cycle, but everything that acts on the RESULT (scale writeback, and the
  // sram_in captured for SET_SCALE) must be delayed by accLatency to line
  // up with out_accType.
  val validD = ShiftRegister(valid, accLatency, false.B, true.B)
  val expS1D = ShiftRegister(exp_s1, accLatency, false.B, true.B)
  val expS2D = ShiftRegister(exp_s2, accLatency, false.B, true.B)
  val setD = ShiftRegister(set, accLatency, false.B, true.B)
  val sramInD = ShiftRegister(io.sram_in, accLatency)

  for (i <- 0 until cols) {
    val s = scale(i)
    val acc = accUnit(i)
    val sa_in = io.sa_in(i)
    val sram_in = io.sram_in(i)
    val sram_out = io.sram_out(i)
    acc.io.in_a := Mux(exp_s1, sa_in, s)
    acc.io.in_b := Mux(exp_s1, accType.attentionScale(rows), sram_in)
    acc.io.in_c := Mux(acc_sa, sa_in, accType.zero)
    acc.io.in_cmd := Mux(exp_s2, MacCMD.EXP2, MacCMD.MAC)
    acc.multiCycleIO.reciprocal_in_valid := valid && reciprocal
    when(validD) {
      when(expS1D || expS2D || acc.multiCycleIO.reciprocal_out_valid) {
        s := acc.io.out_accType
      }.elsewhen(setD) {
        s := sramInD(i)
      }
    }
    sram_out := acc.io.out_accType
  }

}
