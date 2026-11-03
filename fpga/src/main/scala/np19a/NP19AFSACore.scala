package chipyard.fpga.np19a

import chisel3._
import org.chipsalliance.cde.config._
import org.chipsalliance.diplomacy.lazymodule._
import freechips.rocketchip.amba.axi4._
import freechips.rocketchip.diplomacy.{AddressSet, IdRange, RegionType, TransferSizes}
import freechips.rocketchip.subsystem.ExtMem
import fsa.{AXI4FSA, Configs, FpFSAImplKey, WithFpFSA}

// Hardware arithmetic and scheduling are unchanged from the original port baseline.
// The external MIG/SmartConnect owns width conversion (256 -> 512) and CDC.
class NP19AFSACore(implicit p: Parameters) extends LazyModule {
  val control = AXI4MasterNode(Seq(AXI4MasterPortParameters(Seq(
    AXI4MasterParameters(name = "host", id = IdRange(0, 16), maxFlight = Some(16))))))
  val memory = AXI4SlaveNode(Seq(AXI4SlavePortParameters(Seq(
    AXI4SlaveParameters(address = Seq(AddressSet(0, (BigInt(1) << 34) - 1)),
      regionType = RegionType.UNCACHED, executable = false,
      supportsRead = TransferSizes(1, 4096), supportsWrite = TransferSizes(1, 4096),
      interleavedId = Some(0))), beatBytes = 32)))
  val fsa = LazyModule(new AXI4FSA(p(FpFSAImplKey).get))
  fsa.configNode := AXI4Fragmenter() := AXI4Buffer() := control
  memory := AXI4UserYanker(capMaxFlight = Some(8)) := fsa.memNode
  lazy val module = new LazyModuleImp(this) {
    val s_axi = control.makeIOs()
    val m_axi = memory.makeIOs()
  }
}
class WithNP19AMemory extends Config((site, here, up) => {
  case ExtMem => up(ExtMem, site).map(x => x.copy(master = x.master.copy(
    base = BigInt(0), size = BigInt(1) << 34, beatBytes = 32)))
})
class EmptyNP19AConfig extends Config(
  new WithNP19AMemory ++ new WithFpFSA(params = Configs.fsa16x16.copy(nMemPorts = 1)) ++
  new chipyard.EmptyChipTopConfig)
