"""소녀 방 아이소메트릭 디오라마 - 스크립트 모델링 테스트.

실행: blender -b --python build_diorama.py -- [render]
결과: girl_room.blend, girl_room.glb, (render 인자 시) preview.png
규칙: 클릭 소품은 'prop_<id>' Empty 아래에 부품을 묶는다 (웹에서 이 이름으로 판정).
좌표: 바닥 x,y ∈ [-2,2], 왼쪽벽 x=-2, 뒷벽 y=+2, 카메라는 (+x,-y,+z) 방향.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

# ---------- 초기화 (환경설정은 건드리지 않고 씬 데이터만 정리) ----------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
    for d in list(coll):
        coll.remove(d)

scene = bpy.context.scene

# ---------- 팔레트 ----------
PAL = {
    "wall": "#F6B8CF", "wall_edge": "#FAD3E2", "floor": "#E9B488", "floor_edge": "#D79C6E",
    "lilac": "#C9A8E8", "lilac_dk": "#A986D3", "cream": "#FFF1DC", "pink": "#F59FB4",
    "pink_lt": "#FBC7D4", "yellow": "#FFD86B", "wood": "#E8B36A", "mint": "#B7D3A0",
    "green": "#6DBA5B", "green_dk": "#4E9A45", "sky": "#8CCBF5", "white": "#FFFFFF",
    "grey": "#6B6B78", "screen": "#4A4A5A", "blue": "#9CC3F0", "terracotta": "#F2D9C4",
    "lavender": "#DCD3F2", "lavender_dk": "#BBAAE2", "gold": "#F2C35A", "lace": "#FBF5E9", "spread": "#FFF9EF", "pillow": "#EEE8F6",
    "tvblue": "#A9C9DA", "tvblue_dk": "#8FB3C6", "tvscreen": "#A3A8AE", "chrome": "#D9DDE2", "tvdark": "#3E4A55",
    "deskpink": "#F5A9C2", "deskpink_lt": "#F9C3D4", "deskpink_dk": "#E58FAD", "monwhite": "#F4F4F6", "black": "#25262B", "bulb": "#FFE9A8", "wire": "#C9B7BE", "bookpink": "#FF2EAC", "bookpink_dk": "#D81F8E",
}
_mats = {}


def hex2rgb(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


def mat(name, rough=0.55, emit=0.0):
    key = (name, rough, emit)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(f"M_{name}" + (f"_e{emit}" if emit else ""))
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex2rgb(PAL[name])
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = hex2rgb(PAL[name])
        b.inputs["Emission Strength"].default_value = emit
    _mats[key] = m
    return m


def group(name, parent=None):
    e = bpy.data.objects.new(name, None)
    scene.collection.objects.link(e)
    e.parent = parent
    return e


def _finish(ob, color, parent, rough=0.55, emit=0.0, smooth=True):
    ob.data.materials.append(mat(color, rough, emit))
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    if parent:
        ob.parent = parent
    return ob


def box(name, loc, size, color, bevel=0.04, parent=None, rough=0.55, emit=0.0, rot=(0, 0, 0)):
    """size=(x,y,z) 전체 치수. 둥근 모서리 = Bevel 모디파이어."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = ob.modifiers.new("bevel", "BEVEL")
        md.width = min(bevel, min(size) * 0.49)
        md.segments = 4
        md.limit_method = "NONE"
        ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    return _finish(ob, color, parent, rough, emit, smooth=bool(bevel))


def cyl(name, loc, r, h, color, parent=None, verts=40, bevel=0.02, rot=(0, 0, 0), rough=0.55):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    if bevel:
        md = ob.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = 3
        md.limit_method = "ANGLE"
    return _finish(ob, color, parent, rough)


def ball(name, loc, scale, color, parent=None, rot=(0, 0, 0), rough=0.6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return _finish(ob, color, parent, rough)


# ---------- 방 셸 ----------
room = group("room")
box("floor", (0, 0, -0.1), (4.3, 4.3, 0.2), "floor", 0.03, room, rough=0.7)
for i in range(-3, 4):  # 마루 줄눈
    box(f"plank_{i}", (i * 0.6, 0, 0.002), (0.012, 4.2, 0.004), "floor_edge", 0, room)
box("wall_L", (-2.075, 0, 1.3), (0.15, 4.3, 2.6), "wall", 0.03, room, rough=0.8)
box("wall_B", (0, 2.075, 1.3), (4.3, 0.15, 2.6), "wall", 0.03, room, rough=0.8)
box("wall_L_cap", (-2.075, 0, 2.61), (0.17, 4.32, 0.03), "wall_edge", 0.01, room)
box("wall_B_cap", (0.085, 2.075, 2.61), (4.15, 0.17, 0.03), "wall_edge", 0.01, room)

# ---------- 창문 (왼쪽 벽) ----------
win = group("prop_window")
wy, wz = -0.55, 1.98          # 침대 헤드보드(최고 약 1.32)와 겹치지 않게 높임, 커튼 없음
box("win_sky", (-1.995, wy, wz), (0.02, 1.0, 0.8), "sky", 0, win, emit=0.6)
for dy in (-0.52, 0, 0.52):
    box(f"win_v{dy}", (-1.97, wy + dy, wz), (0.06, 0.06, 0.88), "white", 0.015, win)
for dz in (-0.43, 0, 0.43):
    box(f"win_h{dz}", (-1.97, wy, wz + dz), (0.06, 1.1, 0.06), "white", 0.015, win)

# ---------- 미니전구 가랜드 (왼쪽 벽 + 뒷벽, 클릭 = 켜기/끄기) ----------
fairy = group("prop_fairy")


def _curve_mesh(name, pts, r, color, parent):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = r; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p_ in enumerate(pts):
        sp.points[i].co = (*p_, 1)
    ob = bpy.data.objects.new(name, cu); scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.active_object; ob.name = name
    return _finish(ob, color, parent)


def garland(tag, pins, sag, step=0.15):
    """pins 사이를 늘어진 곡선(포물선)으로 잇고, 일정 간격으로 전구를 매단다."""
    pts = []
    for (a_, b_) in zip(pins, pins[1:]):
        n = 24
        for i in range(n + (1 if (a_, b_) == (pins[-2], pins[-1]) else 0)):
            t = i / n
            pts.append(tuple(a_[k] + (b_[k] - a_[k]) * t for k in range(3)))
            pts[-1] = (pts[-1][0], pts[-1][1], pts[-1][2] - sag * 4 * t * (1 - t))
    _curve_mesh(f"fairy_wire_{tag}", pts, 0.005, "wire", fairy)
    hit = _curve_mesh(f"fairy_hit_{tag}", pts, 0.05, "wire", fairy)      # 웹에서 투명 처리: 클릭 판정용 굵은 관
    hit.hide_render = True
    acc, k = step / 2, 0
    for p0, p1 in zip(pts, pts[1:]):
        acc += math.dist(p0, p1)
        if acc >= step:
            acc -= step
            ball(f"fairy_b_{tag}{k:02d}", (p1[0], p1[1], p1[2] - 0.022), (0.022, 0.022, 0.03), "bulb", fairy, rough=0.3)
            k += 1


LX, BY_ = -1.965, 1.965          # 벽 표면 바로 앞
garland("L", [(LX, -1.9, 2.3), (LX, -1.15, 1.47), (LX, 0.05, 1.47), (LX, 0.9, 2.2), (LX, 1.95, 2.3)], 0.17)
# 뒷벽 줄은 없앰: 미니전구는 창문 벽에만 (뒷벽 TV 위는 코르크보드 자리)

# ---------- 코르크보드 (뒷벽 TV 위. 클릭: 굿즈샵 상품) ----------
# x = -0.2 는 아래 수납장·TV 중심(CX)과 같음
PAL["cork"] = "#D2A877"; PAL["cork_frame"] = "#B98A5E"
cb = group("prop_corkboard")
cb.location = (-0.2, 1.985, 2.08); cb.rotation_euler = (0, 0, -math.pi / 2)   # 뒷벽 TV 위. 아래 끝(1.82)이 안테나 끝(1.73)보다 위
# 회전: 보드 앞면(로컬 +x)이 방 쪽(-y)을 보게
box("cork_frame", (0, 0, 0), (0.03, 0.64, 0.52), "cork_frame", 0.012, cb, rough=0.6)
box("cork_board", (0.009, 0, 0), (0.02, 0.58, 0.46), "cork", 0.004, cb, rough=0.95)   # 굿즈 사진·압정은 웹에서 붙임

# ---------- 침대: 원목 침대 형태(둥근 볼 기둥 + 완만한 곡선 헤드보드 + 접힌 이불), 색은 기존 라벤더/크림 ----------
bed = group("bed")
by = -0.55                      # 침대 중심 y
HX, FX = -1.93, -0.22           # 헤드보드 x, 발치 끝 x
HALF = 0.6                      # 침대 반폭


def arch_panel(name, x, thick, z0, ztop, sag, color, inset=0.0):
    """y 폭 2*HALF, 윗변이 완만한 곡선(가운데가 높음)인 판. 큰 원통과 교집합으로 만든다."""
    w = HALF * 2 - inset
    R = ((w / 2) ** 2 + sag ** 2) / (2 * sag)
    box(name, (x, by, (z0 + ztop) / 2), (thick, w, ztop - z0), color, 0, bed)
    ob = bpy.context.active_object
    bpy.ops.mesh.primitive_cylinder_add(vertices=160, radius=R, depth=thick + 0.2,
                                        location=(x, by, ztop - R), rotation=(0, math.pi / 2, 0))
    cut = bpy.context.active_object
    md = ob.modifiers.new("arc", "BOOLEAN"); md.operation = "INTERSECT"; md.object = cut
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier="arc")
    bpy.data.objects.remove(cut, do_unlink=True)
    bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = 0.015; bv.segments = 3; bv.limit_method = "ANGLE"
    for p_ in ob.data.polygons:
        p_.use_smooth = True
    ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    return ob


# 머리쪽 기둥 2개 + 볼 장식
PY = HALF + 0.02
for s_ in (-1, 1):
    y = by + s_ * PY
    box(f"post{s_}", (HX, y, 0.52), (0.11, 0.11, 1.04), "lavender", 0.025, bed)
# 헤드보드: 판 + 위쪽 두꺼운 곡선 레일 + 아래 가로대
arch_panel("hb_panel", HX, 0.06, 0.32, 0.92, 0.09, "lavender")
arch_panel("hb_rail", HX + 0.005, 0.11, 0.84, 0.98, 0.09, "lavender_dk")
box("hb_low", (HX + 0.005, by, 0.3), (0.1, HALF * 2, 0.08), "lavender_dk", 0.02, bed)
# 옆 레일 + 발치 레일 + 발치 다리
box("rail_n", ((HX + FX) / 2, by - HALF, 0.22), (FX - HX, 0.07, 0.14), "lavender", 0.02, bed)
box("rail_p", ((HX + FX) / 2, by + HALF, 0.22), (FX - HX, 0.07, 0.14), "lavender", 0.02, bed)
box("rail_f", (FX, by, 0.22), (0.07, HALF * 2, 0.14), "lavender", 0.02, bed)
for s_ in (-1, 1):
    box(f"leg_f{s_}", (FX, by + s_ * HALF, 0.17), (0.1, 0.1, 0.34), "lavender", 0.02, bed)
# ---------- 푹신한 패브릭: 격자 박스를 부풀린 뒤 Subdivision + 미세 주름 ----------
import bmesh
_fab = {}


def fabric_mat(color):
    if color in _fab:
        return _fab[color]
    m = bpy.data.materials.new(f"M_fab_{color}")
    m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = hex2rgb(PAL[color])
    bs.inputs["Roughness"].default_value = 0.95
    bs.inputs["Sheen Weight"].default_value = 0.6        # 천 느낌 (glTF KHR_materials_sheen)
    bs.inputs["Sheen Tint"].default_value = (1, 1, 1, 1)
    _fab[color] = m
    return m


def soft(name, loc, size, color, puff=(0.0, 0.0, 0.35), rot=(0, 0, 0), wrinkle=0.0, cuts=6, sag=0.0):
    """size 크기의 둥근 쿠션. puff[k]: k축 두께가 가장자리로 갈수록 얇아지는 정도(베개 볼록함).
    sag: 위쪽 가장자리가 아래로 처지는 정도(이불이 옆으로 늘어지는 느낌)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    for v in bm.verts:
        c = [v.co.x, v.co.y, v.co.z]
        n = list(c)
        for k in range(3):
            if puff[k]:
                o = [abs(c[j]) for j in range(3) if j != k]
                n[k] = c[k] * (1 - puff[k] * max(o) ** 2)
        if sag and c[2] > 0:
            edge = max(abs(c[0]), abs(c[1]))
            n[2] -= sag * c[2] * edge ** 4
        v.co = (n[0] * size[0] / 2, n[1] * size[1] / 2, n[2] * size[2] / 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot
    sd = ob.modifiers.new("sub", "SUBSURF"); sd.levels = 2; sd.render_levels = 2
    if wrinkle:
        tex = bpy.data.textures.new(name + "_n", "CLOUDS"); tex.noise_scale = 0.25
        dp = ob.modifiers.new("wr", "DISPLACE"); dp.texture = tex; dp.strength = wrinkle; dp.mid_level = 0.5
    ob.data.materials.append(fabric_mat(color))
    for p_ in ob.data.polygons:
        p_.use_smooth = True
    ob.parent = bed
    return ob


# 매트리스(시트)
soft("mattress", ((HX + FX) / 2 + 0.02, by, 0.38), (FX - HX - 0.04, HALF * 2 - 0.02, 0.22), "lace", puff=(0, 0, 0.12), cuts=4)
# 베개 2개: 가운데가 빵빵하고 가장자리가 얇은 형태, 헤드보드에 기대어
for i, dy in enumerate((-0.27, 0.27)):
    soft(f"pillow{i}", (HX + 0.21, by + dy, 0.64), (0.24, 0.52, 0.36), "pillow", puff=(0.85, 0, 0), rot=(0, -0.38, 0), wrinkle=0.02, cuts=3)
# 이불: 위는 살짝 부풀고, 옆·발치로 처지며 레일을 덮음 + 미세 주름
SX0 = HX + 0.5                   # 이불 시작(베개 앞)
DX1 = FX + 0.07
soft("duvet", ((SX0 + DX1) / 2, by, 0.39), (DX1 - SX0, HALF * 2 + 0.16, 0.42), "spread", puff=(0, 0, 0.22), sag=0.5, wrinkle=0.04, cuts=3)

# ---------- 이불 위 휴대폰 (클릭: 레진 이벤트 팝업) ----------
# 아이폰 목업 느낌: 모서리가 크게 둥근 판 + 얇은 검은 테두리. 화면 내용(카메라 구멍·시계)은 웹 캔버스에서 그림
PAL["phone_frame"] = "#F3D3DC"; PAL["phone_btn"] = "#E6BCC9"


def rrect_slab(name, loc, w, l, t, r, color, parent, edge=0.0015, rough=0.35, seg=10):
    """평면도에서 모서리 반지름 r 인 둥근 직사각형을 두께 t 로 세운 판. 위·아래 모서리는 edge 만큼 살짝 굴림."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, l / 2 - r, 0), (-w / 2 + r, l / 2 - r, 90), (-w / 2 + r, -l / 2 + r, 180), (w / 2 - r, -l / 2 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, -t / 2)) for x, y in pts]
    top = [bm.verts.new((x, y, t / 2)) for x, y in pts]
    bm.faces.new(bot[::-1]); bm.faces.new(top)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    ob.location = loc
    if edge:
        md = ob.modifiers.new("bevel", "BEVEL"); md.width = edge; md.segments = 3
        md.limit_method = "ANGLE"; md.angle_limit = math.radians(60)   # 둥근 옆면 사이 작은 꺾임은 건드리지 않음
        ob.modifiers.new("wn", "WEIGHTED_NORMAL")
    return _finish(ob, color, parent, rough)


# 침대 가운데에 비스듬히. 이불이 울퉁불퉁해서 휴대폰 네 귀퉁이+가운데 높이를 재고 가장 높은 곳에 올림 (파묻힘 방지)
PHX, PHY, PHR = -1.02, by + 0.02, 0.62
PW, PL, PT = 0.078, 0.162, 0.008
bpy.context.view_layer.update()
_dg = bpy.context.evaluated_depsgraph_get()
_zs = []
for sx, sy in ((0, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
    lx, ly = sx * PW / 2, sy * PL / 2
    wx = PHX + lx * math.cos(PHR) - ly * math.sin(PHR); wy = PHY + lx * math.sin(PHR) + ly * math.cos(PHR)
    _hit, _loc, *_ = bpy.context.scene.ray_cast(_dg, (wx, wy, 3.0), (0, 0, -1))
    if _hit: _zs.append(_loc.z)
phz = (max(_zs) if _zs else 0.62) + 0.001
ph = group("prop_phone")
ph.location = (PHX, PHY, phz); ph.rotation_euler = (0, 0, PHR)   # 웹은 이 회전을 읽어 화면이 똑바로 보이는 방향에서 다가감
rrect_slab("phone_body", (0, 0, PT / 2), PW, PL, PT, 0.0125, "phone_frame", ph, edge=0.0018, rough=0.3)
rrect_slab("phone_screen", (0, 0, PT + 0.0004), PW - 0.003, PL - 0.003, 0.0008, 0.011, "black", ph, edge=0, rough=0.1)
for nm, x, y, ln in (("phone_btn_p", PW / 2 + 0.0006, 0.025, 0.026), ("phone_btn_v1", -PW / 2 - 0.0006, 0.035, 0.014), ("phone_btn_v2", -PW / 2 - 0.0006, 0.015, 0.014)):
    box(nm, (x, y, PT / 2), (0.0022, ln, 0.0032), "phone_btn", 0.0009, ph, rough=0.3)

# ---------- 협탁 + 일기장 ----------
ns = group("nightstand")
cyl("ns_top", (-1.7, -1.72, 0.42), 0.28, 0.32, "lilac", ns, bevel=0.05)
for a in range(3):
    t = a * 2 * math.pi / 3 + 0.5
    cyl(f"ns_leg{a}", (-1.7 + 0.18 * math.cos(t), -1.72 + 0.18 * math.sin(t), 0.13), 0.03, 0.26, "wood", ns)
dia = group("prop_diary")
dia.location = (-1.7, -1.72, 0.58); dia.rotation_euler = (0, 0, math.pi / 2 + 0.12)   # 책등이 방 안쪽(+x)을 향함 → 펼치면 표지가 방 안쪽으로 넘어감
# 핑크 하드커버 책: 위/아래 표지 + 둥근 책등 + 크림색 페이지 + 책등 쪽 고무밴드 (부품 좌표는 책 기준)
box("diary_cover_b", (0, 0, 0.006), (0.31, 0.23, 0.012), "bookpink", 0.005, dia, rough=0.45)
box("diary_pages", (-0.003, 0.004, 0.036), (0.29, 0.205, 0.05), "cream", 0.004, dia, rough=0.8)
box("diary_cover_t", (0, 0, 0.067), (0.31, 0.23, 0.012), "bookpink", 0.005, dia, rough=0.45)
cyl("diary_spine", (0, -0.112, 0.0365), 0.037, 0.31, "bookpink", dia, bevel=0.004, rot=(0, math.pi / 2, 0))
bpy.context.active_object.scale = (1, 0.45, 1)
box("diary_band", (0, -0.072, 0.0735), (0.316, 0.026, 0.003), "bookpink_dk", 0.001, dia, rough=0.5)
for s_ in (-1, 1):
    box(f"diary_band_end{s_}", (s_ * 0.1565, -0.072, 0.037), (0.004, 0.026, 0.074), "bookpink_dk", 0.001, dia, rough=0.5)

# ---------- 책장 ----------
bk = group("prop_bookshelf")
kx, ky = -1.32, 1.78   # 뒷벽 가구 간격 균등(약 0.21): 왼벽 | 책장 | 수납장+TV | 책상 | 바닥 끝
# 앞이 뚫린 프레임: 뒤판 + 옆판 2 + 위/아래판
box("shelf_back", (kx, ky + 0.17, 0.8), (0.95, 0.05, 1.6), "wood", 0.02, bk)
for s in (-1, 1):
    box(f"shelf_side{s}", (kx + s * 0.44, ky, 0.8), (0.07, 0.4, 1.6), "yellow", 0.03, bk)
box("shelf_topb", (kx, ky, 1.57), (0.95, 0.4, 0.07), "yellow", 0.03, bk)
box("shelf_bottom", (kx, ky, 0.04), (0.95, 0.4, 0.08), "yellow", 0.03, bk)
for z in (0.55, 1.05):
    box(f"shelf_board{z}", (kx, ky - 0.04, z), (0.84, 0.36, 0.04), "yellow", 0.01, bk)
# 책은 웹(Three.js)에서 레진 작품 표지로 동적 생성 → 여기선 비워 둠

# ---------- TV + 수납장 ----------
CX = -0.2                                 # 수납장·TV 중심 x
cab = group("cabinet")
box("cab_body", (CX, 1.7, 0.36), (0.85, 0.5, 0.62), "mint", 0.05, cab)
for s in (-1, 1):
    box(f"cab_door{s}", (CX + s * 0.2, 1.44, 0.37), (0.36, 0.03, 0.48), "cream", 0.02, cab)
    ball(f"cab_knob{s}", (CX + s * 0.05, 1.42, 0.4), (0.025, 0.025, 0.025), "yellow", cab)
for x in (CX - 0.35, CX + 0.35):
    cyl(f"cab_leg{x}", (x, 1.7, 0.03), 0.03, 0.06, "wood", cab)
tv = group("prop_tv")
# 레트로 하늘색 TV: 둥근 본체 + 테두리 + 브라운관 화면 + 하단 다이얼/버튼/스피커 + 크롬 안테나
TX, TY, FRONT = CX, 1.72, 1.47          # 중심 x,y / 앞면 y
box("tv_foot", (TX, TY, 0.69), (0.5, 0.36, 0.04), "tvblue_dk", 0.015, tv)
box("tv_body", (TX, TY, 1.02), (0.76, 0.5, 0.62), "tvblue", 0.13, tv, rough=0.35)
box("tv_bezel", (TX, FRONT - 0.002, 1.07), (0.64, 0.02, 0.44), "tvblue_dk", 0.09, tv, rough=0.35)
box("tv_bezel_in", (TX, FRONT - 0.012, 1.07), (0.6, 0.02, 0.4), "tvblue", 0.08, tv, rough=0.35)
box("tv_screen", (TX, FRONT - 0.02, 1.07), (0.53, 0.03, 0.34), "tvscreen", 0.08, tv, rough=0.12)
# 하단 컨트롤 줄 (z 0.8)
for k, dx in enumerate((-0.2, 0.08)):
    cyl(f"tv_knob{k}", (TX + dx, FRONT - 0.012, 0.8), 0.045, 0.03, "tvblue_dk", tv, rot=(math.pi / 2, 0, 0))
    cyl(f"tv_knob_cap{k}", (TX + dx, FRONT - 0.03, 0.8), 0.032, 0.02, "tvblue", tv, rot=(math.pi / 2, 0, 0))
    box(f"tv_knob_mark{k}", (TX + dx, FRONT - 0.042, 0.8), (0.008, 0.006, 0.05), "tvdark", 0, tv, rot=(0, 0.6, 0))
for k in range(4):
    box(f"tv_btn{k}", (TX - 0.11 + k * 0.042, FRONT - 0.008, 0.8), (0.034, 0.02, 0.022), "chrome", 0.005, tv, rough=0.3)
for k in range(5):
    box(f"tv_grille{k}", (TX + 0.23, FRONT - 0.004, 0.77 + k * 0.016), (0.11, 0.01, 0.006), "tvdark", 0, tv)
# 크롬 안테나 2개 (뒤쪽 위에서 V자)
cyl("tv_ant_base", (TX + 0.1, TY + 0.1, 1.335), 0.035, 0.03, "chrome", tv, rough=0.25)
for s_, ang in ((-1, 0.35), (1, -0.45)):
    L = 0.42
    cx, cz = TX + 0.1 + s_ * math.sin(abs(ang)) * L / 2, 1.34 + math.cos(ang) * L / 2
    cyl(f"tv_ant{s_}", (cx, TY + 0.1, cz), 0.007, L, "chrome", tv, rot=(0, -ang, 0), bevel=0, rough=0.2)
    ball(f"tv_ant_tip{s_}", (TX + 0.1 + s_ * math.sin(abs(ang)) * L, TY + 0.1, 1.34 + math.cos(ang) * L), (0.012, 0.012, 0.012), "chrome", tv, rough=0.2)

# ---------- 책상: 핑크 양수 책상(서랍+금색 손잡이) + 모니터 + 핑크 스탠드 + 스툴 ----------
from mathutils import Vector


def rod(name, p0, p1, r, color, parent, rough=0.45):
    """두 점을 잇는 원통(스탠드 팔 등)."""
    v0, v1 = Vector(p0), Vector(p1)
    d = v1 - v0
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=d.length, location=(v0 + v1) / 2)
    ob = bpy.context.active_object
    ob.name = name
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    return _finish(ob, color, parent, rough)


desk = group("desk")
dx, dy = 1.11, 1.62
FY = dy - 0.3                                   # 책상 앞면 y
box("desk_top", (dx, dy, 0.8), (1.36, 0.68, 0.05), "deskpink", 0.02, desk, rough=0.4)
box("desk_top_lip", (dx, dy, 0.77), (1.3, 0.64, 0.025), "deskpink_dk", 0.01, desk)
DRAWERS = {-1: [(0.11, 0.33), (0.36, 0.55), (0.58, 0.745)], 1: [(0.11, 0.43), (0.46, 0.745)]}
for side, rows in DRAWERS.items():
    px = dx + side * 0.47
    box(f"ped{side}", (px, dy, 0.42), (0.36, 0.6, 0.7), "deskpink", 0.02, desk, rough=0.45)
    box(f"plinth{side}", (px, dy - 0.01, 0.045), (0.4, 0.64, 0.09), "deskpink_dk", 0.015, desk)
    for k, (z0, z1) in enumerate(rows):
        zc = (z0 + z1) / 2
        box(f"drawer{side}_{k}", (px, FY - 0.012, zc), (0.3, 0.02, z1 - z0 - 0.02), "deskpink_lt", 0.012, desk, rough=0.4)
        cyl(f"handle{side}_{k}", (px, FY - 0.03, zc + (0.04 if z1 - z0 > 0.25 else 0)), 0.009, 0.11, "gold", desk,
            rot=(0, math.pi / 2, 0), bevel=0, rough=0.25)
box("modesty", (dx, dy + 0.26, 0.52), (0.6, 0.04, 0.5), "deskpink_dk", 0.01, desk)
box("apron", (dx, FY + 0.03, 0.72), (0.6, 0.03, 0.07), "deskpink", 0.01, desk)

# 모니터 + 키보드 + 마우스 (클릭: 1화 보기)
lap = group("prop_laptop")
box("mon_base", (dx, dy + 0.13, 0.832), (0.2, 0.15, 0.014), "monwhite", 0.006, lap, rough=0.3)
box("mon_neck", (dx, dy + 0.17, 0.93), (0.07, 0.025, 0.2), "monwhite", 0.01, lap, rough=0.3, rot=(-0.15, 0, 0))
box("mon_body", (dx, dy + 0.15, 1.12), (0.54, 0.035, 0.38), "monwhite", 0.02, lap, rough=0.3)
box("mon_screen", (dx, dy + 0.13, 1.15), (0.5, 0.01, 0.28), "black", 0.006, lap, rough=0.12)
box("keyboard", (dx - 0.02, dy - 0.12, 0.834), (0.36, 0.12, 0.016), "monwhite", 0.006, lap, rough=0.4)
for r_ in range(3):
    box(f"keys{r_}", (dx - 0.02, dy - 0.16 + r_ * 0.035, 0.843), (0.32, 0.022, 0.004), "chrome", 0, lap)
ball("mouse", (dx + 0.25, dy - 0.11, 0.835), (0.035, 0.05, 0.016), "monwhite", lap)

# 핑크 스탠드 (둥근 받침 + 버튼 + 꺾인 팔 + 관절 + 종 모양 갓 + 전구)
lamp = group("prop_lamp")
LX, LY = dx + 0.5, dy + 0.1
cyl("lamp_base", (LX, LY, 0.85), 0.1, 0.05, "deskpink", lamp, bevel=0.02, rough=0.4)
cyl("lamp_btn", (LX - 0.05, LY - 0.05, 0.885), 0.014, 0.025, "deskpink_dk", lamp, bevel=0.005)
J = (LX + 0.04, LY, 1.1)                        # 팔꿈치 관절
rod("lamp_arm1", (LX, LY, 0.87), J, 0.017, "deskpink", lamp)
cyl("lamp_joint", J, 0.032, 0.05, "deskpink", lamp, rot=(math.pi / 2, 0, 0), bevel=0.01)
cyl("lamp_joint_cap", (J[0], J[1] - 0.028, J[2]), 0.02, 0.01, "deskpink_dk", lamp, rot=(math.pi / 2, 0, 0), bevel=0)
o = Vector((-0.55, -0.45, -0.7)).normalized()   # 갓이 비추는 방향 (책상 앞쪽·아래)
S = Vector((LX - 0.13, LY - 0.02, 1.2))         # 갓 중심
rod("lamp_arm2", J, S - o * 0.09, 0.017, "deskpink", lamp)
bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.1, radius2=0.05, depth=0.13, location=S)
sh = bpy.context.active_object
sh.name = "lamp_shade"
sh.rotation_mode = "QUATERNION"
sh.rotation_quaternion = (-o).to_track_quat("Z", "Y")
md = sh.modifiers.new("solid", "SOLIDIFY"); md.thickness = 0.008
md = sh.modifiers.new("bevel", "BEVEL"); md.width = 0.006; md.segments = 2
_finish(sh, "deskpink", lamp, rough=0.4)
ball("lamp_cap", tuple(S - o * 0.07), (0.052, 0.052, 0.052), "deskpink", lamp)
ball("lamp_bulb", tuple(S + o * 0.01), (0.045, 0.045, 0.045), "bulb", lamp, rough=0.2)

# 레트로 라디오 (책상 왼쪽, 클릭: 배경음악 켜기/끄기)
# 앞면이 카메라 쪽(-y). 왼쪽 둥근 스피커 + 오른쪽 주파수 창(radio_dial: 웹에서 켜지면 빛남) + 손잡이 + 안테나
PAL["radio"] = "#9FD8C8"; PAL["radio_dk"] = "#7FC0AE"
radio = group("prop_radio")
RX, RY, RZ = dx - 0.47, dy + 0.06, 0.825        # 책상 윗면 위
RW, RD, RH = 0.27, 0.11, 0.155
box("radio_body", (RX, RY, RZ + RH / 2), (RW, RD, RH), "radio", 0.025, radio, rough=0.45)
box("radio_face", (RX, RY - RD / 2 - 0.002, RZ + RH / 2 - 0.005), (RW - 0.03, 0.006, RH - 0.04), "cream", 0.012, radio, rough=0.5)
FRONT = RY - RD / 2 - 0.006
cyl("radio_spk", (RX - 0.055, FRONT, RZ + 0.072), 0.045, 0.006, "radio_dk", radio, rot=(math.pi / 2, 0, 0), bevel=0.003)
for k in range(4):   # 스피커 가로줄 무늬
    box(f"radio_grill{k}", (RX - 0.055, FRONT - 0.004, RZ + 0.045 + k * 0.018), (0.07 - abs(k - 1.5) * 0.012, 0.003, 0.005), "cream", 0.001, radio)
box("radio_dial", (RX + 0.06, FRONT - 0.001, RZ + 0.095), (0.09, 0.004, 0.035), "bulb", 0.004, radio, rough=0.3)
box("radio_needle", (RX + 0.05, FRONT - 0.004, RZ + 0.095), (0.003, 0.002, 0.03), "pink", 0, radio)
for i, kx in enumerate((RX + 0.035, RX + 0.085)):
    cyl(f"radio_knob{i}", (kx, FRONT - 0.006, RZ + 0.045), 0.014, 0.014, "deskpink_dk", radio, rot=(math.pi / 2, 0, 0), bevel=0.004)
for sx_ in (-1, 1):   # 손잡이 기둥
    box(f"radio_hpost{sx_}", (RX + sx_ * 0.08, RY, RZ + RH + 0.02), (0.014, 0.03, 0.04), "radio_dk", 0.005, radio)
box("radio_handle", (RX, RY, RZ + RH + 0.04), (0.18, 0.03, 0.014), "radio_dk", 0.006, radio)
rod("radio_ant", (RX + 0.11, RY + 0.02, RZ + RH), (RX + 0.2, RY + 0.06, RZ + RH + 0.22), 0.004, "chrome", radio)
ball("radio_ant_tip", (RX + 0.2, RY + 0.06, RZ + RH + 0.22), (0.009, 0.009, 0.009), "chrome", radio)

# 핑크 스툴 (의자 대신)
stool = group("stool")
sx, sy = dx, dy - 0.68
box("stool_seat", (sx, sy, 0.47), (0.44, 0.34, 0.09), "deskpink_lt", 0.04, stool, rough=0.7)
box("stool_rail", (sx, sy, 0.415), (0.44, 0.34, 0.04), "deskpink", 0.01, stool)
for x in (sx - 0.19, sx + 0.19):
    for y in (sy - 0.14, sy + 0.14):
        box(f"stool_leg{x}{y}", (x, y, 0.2), (0.035, 0.035, 0.4), "deskpink", 0.008, stool)
for y in (sy - 0.14, sy + 0.14):
    box(f"stool_bar{y}", (sx, y, 0.12), (0.38, 0.02, 0.025), "deskpink", 0.005, stool)

# ---------- 액자 (뒷벽) ----------
fr = group("prop_frame")
box("frame_border", (dx, 1.99, 1.88), (0.75, 0.04, 0.9), "white", 0.03, fr)
box("frame_inner", (dx, 1.965, 1.88), (0.6, 0.02, 0.75), "cream", 0, fr, emit=0.15)

# ---------- 러그 ----------
rug = group("prop_rug")   # 클릭하면 앞쪽 귀퉁이가 들춰짐 (이스터에그: 밑에 인형)
# 둥근 러그(방 앞쪽, 책상·의자와 같은 줄): 긴 축은 침대 발치와 나란히(y). 무늬는 웹에서 rug_round.png(투명 배경)로 입힘
bpy.ops.mesh.primitive_plane_add(size=1, location=(0.85, -0.55, 0.008))
rp = bpy.context.active_object
rp.name = "rug_mat"
rp.scale = (1.7, 2.3, 1)        # 이미지 비율 1.48 : 1 (기존의 1.3배)
bpy.ops.object.transform_apply(scale=True)
_finish(rp, "lavender", rug, rough=1.0, smooth=False)

# ---------- 이스터에그: 러그 밑에 숨은 캐릭터 종이 조각 ----------
# 자리만 잡아 둠. 종이(egg_paper.png)는 웹에서 이 자리 바닥에 붙임. 러그 앞 귀퉁이 아래
dl = group("prop_doll")
dl.location = (1.27, -1.12, 0.0); dl.rotation_euler = (0, 0, 0.6)   # 살짝만 들춰도 다 보이게 귀퉁이 가까이

# ---------- 조명 / 카메라 / 렌더 ----------
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = hex2rgb("#E4E1EA")
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9

sun_d = bpy.data.lights.new("key", "AREA")
sun_d.energy = 700
sun_d.size = 4
sun_d.color = (1.0, 0.96, 0.92)
key = bpy.data.objects.new("key", sun_d)
key.location = (3, -4, 6)
key.rotation_euler = (math.radians(40), 0, math.radians(35))
scene.collection.objects.link(key)

cam_d = bpy.data.cameras.new("cam")
cam_d.type = "ORTHO"
cam_d.ortho_scale = 7.2
cam = bpy.data.objects.new("cam", cam_d)
cam.location = (9, -9, 8.2)
scene.collection.objects.link(cam)
tgt = bpy.data.objects.new("cam_target", None)
tgt.location = (0, 0, 1.0)
scene.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO")
tc.target = tgt
tc.track_axis = "TRACK_NEGATIVE_Z"
tc.up_axis = "UP_Y"
scene.camera = cam

scene.render.engine = "CYCLES"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    scene.cycles.device = "GPU"
except Exception as e:  # GPU 없으면 CPU
    print("GPU setup failed:", e)
scene.render.resolution_x = 1400
scene.render.resolution_y = 1300
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = -0.35

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "girl_room.blend"))

# glTF (웹용) - 모디파이어 적용, 조명/카메라 제외
bpy.ops.export_scene.gltf(
    filepath=os.path.join(HERE, "girl_room.glb"),
    export_format="GLB",
    export_apply=True,
    export_cameras=False,
    export_lights=False,
    export_extras=False,
)

if "render" in ARGS:
    scene.render.filepath = os.path.join(HERE, "preview.png")
    bpy.ops.render.render(write_still=True)
print("DIORAMA_DONE")
