//! The WebAssembly program's root (P2P_TARGET=wasm32-wasi): the same p2p, its entry given the name WASI's start calls.
//! wasi-libc's crt1-command starts the program and calls __main_argc_argv(argc, argv), the name a C compiler gives
//! main for WASI; Zig's own start does nothing here because this root has no main.
const p2p = @import("p2p.zig");

comptime {
    @export(&p2p.mainC, .{ .name = "__main_argc_argv" });
}
