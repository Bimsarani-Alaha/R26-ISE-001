"""Isolated ONNX runtime. Run as a script, before importing pandas or PyTorch.

Frames contain a command byte, an unsigned 64-bit length, and a pickle-free NPY
array. Stdout is reserved for this protocol; diagnostics go to stderr.
"""

import io
from pathlib import Path
import struct
import sys


def read_exact(stream, length):
    parts = bytearray()
    while len(parts) < length:
        data = stream.read(length - len(parts))
        if not data:
            raise EOFError("FashionSigLIP worker pipe closed")
        parts.extend(data)
    return bytes(parts)


def main():
    # Import first: some Windows native runtimes conflict with pandas DLLs.
    import onnxruntime as ort
    import numpy as np

    path, threads = Path(sys.argv[1]), int(sys.argv[2])
    options = ort.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    sessions = {
        b"T": (ort.InferenceSession(str(path / "onnx/text_model.onnx"), sess_options=options,
                                   providers=["CPUExecutionProvider"]), "input_ids", "text_embeds"),
        b"I": (ort.InferenceSession(str(path / "onnx/vision_model.onnx"), sess_options=options,
                                   providers=["CPUExecutionProvider"]), "pixel_values", "image_embeds"),
    }
    source, target = sys.stdin.buffer, sys.stdout.buffer
    target.write(b"READY\n")
    target.flush()
    while command := source.read(1):
        try:
            size = struct.unpack("<Q", read_exact(source, 8))[0]
            values = np.load(io.BytesIO(read_exact(source, size)), allow_pickle=False)
            session, input_name, output_name = sessions[command]
            result = session.run([output_name], {input_name: values})[0]
            buffer = io.BytesIO()
            np.save(buffer, result, allow_pickle=False)
            payload, status = buffer.getvalue(), b"O"
        except Exception as exc:
            payload, status = str(exc).encode(), b"E"
        target.write(status + struct.pack("<Q", len(payload)) + payload)
        target.flush()


if __name__ == "__main__":
    main()
