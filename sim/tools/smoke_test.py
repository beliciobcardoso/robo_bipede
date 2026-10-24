"""F0 smoke test: MuJoCo on the CPU vs MJX on the GPU (JAX and Warp backends).

    .venv/bin/python sim/tools/smoke_test.py

Loads sim/models/f0_smoke.xml (torso + one 4-joint leg falling into a crouch),
runs it on the CPU, then runs batches of copies in parallel on the GPU and
reports throughput (simulated steps per second) and whether the GPU result
matches the CPU one.
"""

import os
import time
from pathlib import Path

os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")  # don't grab 75% of VRAM up front

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from mujoco import mjx  # noqa: E402
from warp._src.jax.ffi import JaxCallableGraphMode  # noqa: E402

MODEL = Path(__file__).resolve().parents[1] / "models" / "f0_smoke.xml"
CROUCH = np.array([0.4, -0.8, 0.4, 0.0])    # hip, knee, ankle pitch, ankle roll targets (rad)
STEPS = 500                                  # 1 s of simulated time at dt = 2 ms
BATCHES = tuple(int(n) for n in os.environ.get("SMOKE_BATCHES", "1,64,1024,4096,16384").split(","))
MAX_CPU_GPU_DIFF = 1e-3                      # m, torso height after 1 s


def run_cpu(m: mujoco.MjModel):
    d = mujoco.MjData(m)
    d.ctrl[:] = CROUCH
    t0 = time.perf_counter()
    for _ in range(STEPS):
        mujoco.mj_step(m, d)
    rate = STEPS / (time.perf_counter() - t0)
    return rate, float(d.qpos[2]), d.actuator_force.copy()


def run_gpu(m: mujoco.MjModel, impl: str, n: int):
    extra, graph = {}, {}
    if impl == "warp":
        # Warp preallocates contact/constraint buffers for the whole batch.
        extra = dict(naconmax=16 * n, njmax=64)
        # The default graph mode (JAX) fails here with CUDA_ERROR_NOT_SUPPORTED when
        # nesting graphs; Warp's own capture works and is the fastest mode measured.
        graph = dict(graph_mode=JaxCallableGraphMode.WARP)
    mx = mjx.put_model(m, impl=impl, **graph)
    d0 = mjx.make_data(m, impl=impl, **extra)
    d0 = d0.replace(ctrl=jnp.asarray(CROUCH, dtype=d0.ctrl.dtype))

    def rollout(d):
        return jax.lax.scan(lambda d, _: (mjx.step(mx, d), None), d, None, length=STEPS)[0]

    # Copies with a tiny different initial torso height, so they are really n different robots.
    heights = d0.qpos[2] + jnp.linspace(0.0, 0.002, n)
    batch = jax.vmap(lambda z: d0.replace(qpos=d0.qpos.at[2].set(z)))(heights)
    f = jax.jit(jax.vmap(rollout))

    t0 = time.perf_counter()
    jax.block_until_ready(f(batch))
    compile_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    out = jax.block_until_ready(f(batch))
    rate = n * STEPS / (time.perf_counter() - t0)
    return rate, compile_s, float(out.qpos[0, 2])


def main():
    m = mujoco.MjModel.from_xml_path(str(MODEL))
    print(f"MuJoCo {mujoco.__version__} | JAX {jax.__version__} | device {jax.devices()[0]}")
    print(f"model: {MODEL.name}  bodies={m.nbody} joints={m.njnt} actuators={m.nu}  "
          f"{STEPS} steps = {STEPS * m.opt.timestep:.1f} s simulated\n")

    cpu_rate, cpu_z, torques = run_cpu(m)
    print(f"CPU   1 robot          {cpu_rate:12,.0f} steps/s   torso z={cpu_z:.4f} m")
    print("      joint torques at 1 s (N·m): "
          + ", ".join(f"{m.actuator(i).name}={t:+.3f}" for i, t in enumerate(torques)))

    ok = True
    for impl in ("jax", "warp"):
        for n in BATCHES:
            try:
                rate, compile_s, z = run_gpu(m, impl, n)
            except Exception as e:  # a backend failing must not hide the other's result
                print(f"GPU/{impl:4s} {n:5d} robots   FAILED: {type(e).__name__}: {str(e).splitlines()[0][:120]}")
                ok = False
                break
            diff = abs(z - cpu_z)
            flag = "ok" if diff < MAX_CPU_GPU_DIFF else "MISMATCH"
            ok &= diff < MAX_CPU_GPU_DIFF
            print(f"GPU/{impl:4s} {n:5d} robots   {rate:12,.0f} steps/s   x{rate / cpu_rate:7.1f} vs CPU   "
                  f"compile {compile_s:5.1f}s   torso z={z:.4f} ({flag}, diff {diff * 1000:.3f} mm)")
    print("\nSMOKE TEST", "PASSED" if ok else "FAILED")


if __name__ == "__main__":
    main()
