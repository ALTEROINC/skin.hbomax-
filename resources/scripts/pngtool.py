import math
import struct
import zlib

# Minimal PNG reader/writer used to give TMDb's logos the same treatment as the bundled ones (trim the empty
# margins, size to the same visual weight, turn dark pixels white). Kodi's Python has no imaging library, so
# this is plain Python on small images. Handles non-interlaced PNGs of any colour type; anything else raises
# ValueError and the caller simply shows no logo.

AREA = 26000       # target area of a logo (px^2) before SCALE, so wide and square logos look equally big
MAXW = 300
MAXH = 104
SCALE = 1.5        # same export scale as the bundled logos (media/studios)
DARK_BELOW = 120   # luminance under which a pixel is turned white
DARK_FEATHER = 40.0


def _unfilter(raw, width, height, bpp, stride):
    rows = []
    prev = bytearray(stride)
    pos = 0
    for _ in range(height):
        ftype = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 255
        elif ftype != 0:
            raise ValueError('bad filter')
        rows.append(line)
        prev = line
    return rows


def decode(data):
    """PNG bytes -> (width, height, rows) where rows are bytearrays of RGBA, 4 bytes per pixel."""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG')
    pos = 8
    idat = []
    palette = []
    trns = b''
    while pos < len(data):
        length, ctype = struct.unpack('>I4s', data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b'IHDR':
            width, height, depth, color, _, _, interlace = struct.unpack('>IIBBBBB', body)
        elif ctype == b'PLTE':
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif ctype == b'tRNS':
            trns = body
        elif ctype == b'IDAT':
            idat.append(body)
        elif ctype == b'IEND':
            break
    if interlace:
        raise ValueError('interlaced')
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    bits = depth * channels
    stride = (width * bits + 7) // 8
    bpp = max(1, bits // 8)
    rows = _unfilter(zlib.decompress(b''.join(idat)), width, height, bpp, stride)

    out = []
    for line in rows:
        px = bytearray(width * 4)
        if depth == 16:
            line = bytearray(line[0::2])        # keep the high byte of each sample
            depth_eff = 8
        else:
            depth_eff = depth
        if color == 6:
            px[:] = line[:width * 4]
        elif color == 2:
            for x in range(width):
                px[x * 4:x * 4 + 3] = line[x * 3:x * 3 + 3]
                px[x * 4 + 3] = 255
        elif color == 4:
            for x in range(width):
                g = line[x * 2]
                px[x * 4] = px[x * 4 + 1] = px[x * 4 + 2] = g
                px[x * 4 + 3] = line[x * 2 + 1]
        else:   # 0 grey, 3 palette; sample sizes 1,2,4,8
            per = 8 // depth_eff
            mask = (1 << depth_eff) - 1
            for x in range(width):
                byte = line[x // per]
                shift = 8 - depth_eff * (x % per + 1)
                v = (byte >> shift) & mask
                if color == 3:
                    r, g, b = palette[v] if v < len(palette) else (0, 0, 0)
                    a = trns[v] if v < len(trns) else 255
                else:
                    r = g = b = v * 255 // mask
                    a = 255
                px[x * 4:x * 4 + 4] = bytes((r, g, b, a))
        out.append(px)
    return width, height, out


def encode(width, height, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def _whiten(rows):
    for r in rows:
        for i in range(0, len(r), 4):
            lum = 0.299 * r[i] + 0.587 * r[i + 1] + 0.114 * r[i + 2]
            if lum < DARK_BELOW:
                f = min(1.0, (DARK_BELOW - lum) / DARK_FEATHER)
                for k in range(3):
                    r[i + k] = int(r[i + k] * (1 - f) + 255 * f)


def _bbox(width, height, rows, threshold=8):
    xs0, ys0, xs1, ys1 = width, height, -1, -1
    for y, r in enumerate(rows):
        alphas = r[3::4]
        if max(alphas) > threshold:
            xs = [x for x, a in enumerate(alphas) if a > threshold]
            xs0, xs1 = min(xs0, xs[0]), max(xs1, xs[-1])
            ys0, ys1 = min(ys0, y), max(ys1, y)
    if xs1 < 0:
        raise ValueError('empty image')
    return xs0, ys0, xs1 + 1, ys1 + 1


def _resize(width, height, rows, new_w, new_h):
    """Bilinear, with colour weighted by alpha so transparent pixels don't tint the edges."""
    out = []
    for y in range(new_h):
        sy = (y + 0.5) * height / new_h - 0.5
        y0 = max(0, min(height - 1, int(math.floor(sy))))
        y1 = min(height - 1, y0 + 1)
        fy = min(1.0, max(0.0, sy - y0))
        r0, r1 = rows[y0], rows[y1]
        line = bytearray(new_w * 4)
        for x in range(new_w):
            sx = (x + 0.5) * width / new_w - 0.5
            x0 = max(0, min(width - 1, int(math.floor(sx))))
            x1 = min(width - 1, x0 + 1)
            fx = min(1.0, max(0.0, sx - x0))
            w00, w10 = (1 - fx) * (1 - fy), fx * (1 - fy)
            w01, w11 = (1 - fx) * fy, fx * fy
            a = (r0[x0 * 4 + 3] * w00 + r0[x1 * 4 + 3] * w10 + r1[x0 * 4 + 3] * w01 + r1[x1 * 4 + 3] * w11)
            if a > 0:
                for k in range(3):
                    c = (r0[x0 * 4 + k] * r0[x0 * 4 + 3] * w00 + r0[x1 * 4 + k] * r0[x1 * 4 + 3] * w10 +
                         r1[x0 * 4 + k] * r1[x0 * 4 + 3] * w01 + r1[x1 * 4 + k] * r1[x1 * 4 + 3] * w11)
                    line[x * 4 + k] = min(255, int(c / a))
            line[x * 4 + 3] = min(255, int(a))
        out.append(line)
    return out


def normalise(data):
    """PNG bytes of a logo -> PNG bytes trimmed, dark parts white, sized like the bundled logos."""
    width, height, rows = decode(data)
    _whiten(rows)
    x0, y0, x1, y1 = _bbox(width, height, rows)
    rows = [bytearray(r[x0 * 4:x1 * 4]) for r in rows[y0:y1]]
    width, height = x1 - x0, y1 - y0
    ar = width / height
    w = math.sqrt(AREA * ar)
    h = w / ar
    s = min(1.0, MAXW / w, MAXH / h)
    new_w = max(1, round(w * s * SCALE))
    new_h = max(1, round(h * s * SCALE))
    return encode(new_w, new_h, _resize(width, height, rows, new_w, new_h))
