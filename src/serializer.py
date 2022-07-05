import io
import msgpack
import zstandard

from typing import Any, Optional


def s(obj: Any) -> bytes:
    buf = io.BytesIO()
    cctx = zstandard.ZstdCompressor()
    with cctx.stream_writer(buf, closefd=False) as writer:
        msgpack.dump(obj, writer)
    buf.seek(0)
    return buf.read()


def d(buf: Optional[bytes]) -> Any:
    if not buf:
        return None
    try:
        dctx = zstandard.ZstdDecompressor()
        with dctx.stream_reader(buf) as reader:
            return msgpack.load(reader)
    except ValueError:
        return None
