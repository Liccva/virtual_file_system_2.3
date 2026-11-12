"""Генератор UML-диаграмм классов варианта 2.3 (SVG, ортогональные связи).

Запуск: python diagrams_gen.py <папка_для_svg>
Создаёт class_diagram.svg (2.3.1) и class_diagram_extension.svg (2.3.3).
"""
import html
import os
import sys

FONT = "Arial, Helvetica, sans-serif"
LINE = 18
STROKE = "#37474F"
C_PATTERN = "#FFE0B2"
C_ROLE = "#BBDEFB"
C_DOMAIN = "#C8E6C9"
C_ROOT = "#E0E0E0"
C_NEW = "#E1BEE7"
C_OLD = "#ECEFF1"
C_CHANGED = "#FFF59D"

DEFS = '''<defs>
  <marker id="tri" viewBox="0 0 20 20" refX="19" refY="10" markerWidth="16" markerHeight="16" markerUnits="userSpaceOnUse" orient="auto">
    <path d="M1,1 L19,10 L1,19 z" fill="#FFFFFF" stroke="#37474F" stroke-width="1.6"/></marker>
  <marker id="dia" viewBox="0 0 24 12" refX="1" refY="6" markerWidth="22" markerHeight="11" markerUnits="userSpaceOnUse" orient="auto">
    <path d="M1,6 L12,1 L23,6 L12,11 z" fill="#37474F" stroke="#37474F" stroke-width="1.2"/></marker>
  <marker id="odia" viewBox="0 0 24 12" refX="1" refY="6" markerWidth="22" markerHeight="11" markerUnits="userSpaceOnUse" orient="auto">
    <path d="M1,6 L12,1 L23,6 L12,11 z" fill="#FFFFFF" stroke="#37474F" stroke-width="1.4"/></marker>
  <marker id="arr" viewBox="0 0 14 14" refX="13" refY="7" markerWidth="13" markerHeight="13" markerUnits="userSpaceOnUse" orient="auto">
    <path d="M1,1 L13,7 L1,13" fill="none" stroke="#37474F" stroke-width="1.6"/></marker>
</defs>'''


class Canvas:
    def __init__(self):
        self.parts = []
        self.boxes = []

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, size=12.5, anchor="start", weight="normal", style="normal", fill="#212121"):
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" font-style="{style}" fill="{fill}" xml:space="preserve">'
                 f'{html.escape(s, quote=False)}</text>')

    def label(self, x, y, s, anchor="start", size=11.5):
        w = len(s) * size * 0.52 + 8
        rx = {"start": x - 4, "middle": x - w / 2, "end": x - w + 4}[anchor]
        self.add(f'<rect x="{rx}" y="{y - size}" width="{w}" height="{size + 5}" fill="#FFFFFF" opacity="0.92"/>')
        self.text(x, y, s, size=size, anchor=anchor, fill="#263238")

    def poly(self, points, dashed=False, start=None, end=None):
        d = " ".join(f"{px},{py}" for px, py in points)
        extra = ' stroke-dasharray="7,5"' if dashed else ""
        ms = f' marker-start="url(#{start})"' if start else ""
        me = f' marker-end="url(#{end})"' if end else ""
        self.add(f'<polyline points="{d}" fill="none" stroke="{STROKE}" stroke-width="1.4"{extra}{ms}{me}/>')

    def zone(self, x, y, w, h, title, color, tab=14, bottom=False):
        ty = y + h if bottom else y
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{color}" fill-opacity="0.16" '
                 f'stroke="{color}" stroke-width="2" stroke-dasharray="10,6"/>')
        tw = len(title) * 8.3 + 26
        self.add(f'<rect x="{x + tab}" y="{ty - 13}" width="{tw}" height="26" rx="6" fill="#FFFFFF" '
                 f'stroke="{color}" stroke-width="2"/>')
        self.text(x + tab + 12, ty + 5, title, size=13.5, weight="bold", fill="#263238")

    def box(self, *args, **kw):
        b = Box(*args, **kw)
        self.boxes.append(b)
        return b

    def legend(self, x, y, w, colors, notation=True, note=None):
        h = 36 + len(colors) * 22 + (80 if notation else 0) + (22 if note else 0)
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#FAFAFA" stroke="#90A4AE" stroke-width="1.2"/>')
        self.text(x + 14, y + 22, "Обозначения", size=13.5, weight="bold")
        yy = y + 36
        for c, t in colors:
            self.add(f'<rect x="{x + 14}" y="{yy}" width="26" height="15" fill="{c}" stroke="{STROKE}" stroke-width="1"/>')
            self.text(x + 50, yy + 12, t, size=12)
            yy += 22
        if notation:
            nx, ny = x + 14, yy + 12
            rows = [(dict(end="tri"), "наследование", dict(dashed=True, end="tri"), "реализация интерфейса"),
                    (dict(start="dia"), "композиция (владеет)", dict(start="odia"), "агрегация (ссылается)"),
                    (dict(end="arr"), "ассоциация", dict(dashed=True, end="arr"), "зависимость")]
            for a, ta, b, tb in rows:
                self.poly([(nx, ny), (nx + 52, ny)], **a)
                self.text(nx + 62, ny + 4, ta, size=12)
                self.poly([(nx + 215, ny), (nx + 267, ny)], **b)
                self.text(nx + 277, ny + 4, tb, size=12)
                ny += 26
            yy = ny - 4
        if note:
            self.text(x + 14, yy + 6, note, size=11.5, fill="#BF360C")
        return h

    def save(self, path, w, h, title):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
               DEFS, f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>']
        self.parts, body = [], self.parts
        self.text(w / 2, 36, title, size=19, anchor="middle", weight="bold")
        for b in self.boxes:
            b.draw(self)
        out += self.parts[:1] + body + self.parts[1:] + ["</svg>"]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(out))


class Box:
    def __init__(self, x, y, w, name, stereo=None, attrs=None, ops=None, fill=C_DOMAIN,
                 italic_name=False, italic_ops=()):
        self.x, self.y, self.w = x, y, w
        self.name, self.stereo, self.attrs, self.ops = name, stereo, attrs, ops
        self.fill, self.italic_name, self.italic_ops = fill, italic_name, set(italic_ops)
        self.head = 48 if stereo else 32
        self.ha = (10 + LINE * len(attrs)) if attrs is not None else 0
        self.ho = (10 + LINE * len(ops)) if ops is not None else 0
        self.h = self.head + self.ha + self.ho

    cx = property(lambda s: s.x + s.w / 2)
    cy = property(lambda s: s.y + s.h / 2)
    r = property(lambda s: s.x + s.w)
    b = property(lambda s: s.y + s.h)

    def draw(self, cv):
        x, y, w = self.x, self.y, self.w
        cv.add(f'<rect x="{x}" y="{y}" width="{w}" height="{self.h}" rx="3" fill="{self.fill}" '
               f'stroke="{STROKE}" stroke-width="1.3"/>')
        if self.stereo:
            cv.text(self.cx, y + 18, self.stereo, size=11.5, anchor="middle", style="italic", fill="#455A64")
            cv.text(self.cx, y + 37, self.name, size=14.5, anchor="middle", weight="bold",
                    style="italic" if self.italic_name else "normal")
        else:
            cv.text(self.cx, y + 21, self.name, size=14.5, anchor="middle", weight="bold",
                    style="italic" if self.italic_name else "normal")
        cy = y + self.head
        for section in (self.attrs, self.ops):
            if section is None:
                continue
            cv.add(f'<line x1="{x}" y1="{cy}" x2="{x + w}" y2="{cy}" stroke="{STROKE}" stroke-width="1"/>')
            for i, m in enumerate(section):
                st = "italic" if m in self.italic_ops else "normal"
                if "  [" in m:
                    main, tag = m.split("  [", 1)
                    cv.text(x + 10, cy + 18 + i * LINE, main, style=st)
                    cv.text(x + w - 8, cy + 18 + i * LINE, "[" + tag, size=11.5, anchor="end",
                            weight="bold", fill="#BF360C")
                else:
                    cv.text(x + 10, cy + 18 + i * LINE, m, style=st)
            cy += 10 + LINE * len(section)


NODE_OPS = ["+ size(): int",
            "+ print_tree(depth: int = 0): str",
            "+ find(name: str): FileSystemNode | None",
            "+ contains(node: FileSystemNode): bool"]


# =============================================================== 2.3.1
def class_diagram(path):
    cv = Canvas()
    fsn = cv.box(390, 70, 380, "FileSystemNode", "«abstract» · Composite: Component · Proxy: Subject",
                 attrs=["- _name: str"], ops=["+ name: str «property»"] + NODE_OPS,
                 fill=C_PATTERN, italic_name=True, italic_ops=NODE_OPS)
    ZTOP = fsn.b + 75
    ROW = ZTOP + 40
    dirc = cv.box(55, ROW, 340, "DirectoryComposite", "Composite: Composite",
                  attrs=["- _children: list[FileSystemNode]"],
                  ops=["+ children: tuple «property»",
                       "+ add(child: FileSystemNode)",
                       "+ remove(child: FileSystemNode)"] + NODE_OPS, fill=C_ROLE)
    leaf = cv.box(415, ROW, 330, "FileLeaf", "Composite: Leaf",
                  attrs=["- _size: int"], ops=list(NODE_OPS), fill=C_ROLE)
    proxy = cv.box(820, ROW, 430, "ProtectedNodeProxy", "Proxy: Protection Proxy",
                   attrs=["- _subject: FileSystemNode", "- _access: AccessService", "- _user: User"],
                   ops=["+ size(): int  [READ]",
                        "+ print_tree(depth: int = 0): str  [LIST+READ]",
                        "+ find(name: str): FileSystemNode | None  [LIST]",
                        "+ contains(node: FileSystemNode): bool",
                        "- _allowed(permission: Permission): bool"], fill=C_PATTERN)
    svc = cv.box(1325, ROW, 455, "AccessService", "«interface» (ABC) · сервис прав",
                 attrs=None, ops=["+ is_allowed(user: User, node: FileSystemNode,",
                                  "      permission: Permission): bool"],
                 fill=C_DOMAIN, italic_name=True)
    acl = cv.box(1325, svc.b + 60, 455, "AclAccessService",
                 attrs=["- _acl: dict[FileSystemNode, dict[str, set[Permission]]]"],
                 ops=["+ grant(user: User, node: FileSystemNode,",
                      "      *permissions: Permission)",
                      "+ is_allowed(user, node, permission): bool"], fill=C_DOMAIN)
    user = cv.box(1345, acl.b + 60, 170, "User", "«dataclass»",
                  attrs=["+ id: str", "+ name: str"], fill=C_DOMAIN)
    perm = cv.box(1590, acl.b + 60, 170, "Permission", "«enumeration»",
                  attrs=["READ", "LIST"], fill=C_DOMAIN)
    ERR_Y = max(dirc.b, proxy.b) + 60
    inv = cv.box(dirc.cx - 135, ERR_Y, 270, "InvalidTreeOperationError", "«exception»",
                 attrs=["(сообщение об ошибке)"], fill=C_DOMAIN)
    den = cv.box(proxy.cx - 135, ERR_Y, 270, "AccessDeniedError", "«exception»",
                 attrs=["+ user_name: str", "+ node_name: str", "+ permission: Permission"], fill=C_DOMAIN)
    ZBOT = max(inv.b, den.b, user.b, perm.b) + 30
    app = cv.box(proxy.cx - 240, ZBOT + 75, 480, "main", "«module» · composition root",
                 ops=["+ build_base_tree(access, user): FileSystemNode",
                      "+ client(root: FileSystemNode)"], fill=C_ROOT)
    W, H = 1810, app.b + 40

    cv.zone(30, ZTOP, 745, ZBOT - ZTOP, "Composite — структура дерева", "#1E88E5", tab=268)
    cv.zone(800, ZTOP, 470, ZBOT - ZTOP, "Proxy — контроль доступа", "#FB8C00")
    cv.zone(1300, ZTOP, 500, ZBOT - ZTOP, "Сервис прав", "#43A047")

    BUS = fsn.b + 38
    cv.poly([(dirc.cx, dirc.y), (dirc.cx, BUS), (proxy.cx, BUS), (proxy.cx, proxy.y)])
    cv.poly([(leaf.cx, leaf.y), (leaf.cx, BUS)])
    cv.poly([(fsn.cx, BUS), (fsn.cx, fsn.b)], end="tri")
    cv.label(fsn.cx + 10, BUS - 12, "наследование: все узлы выполняют один контракт")

    MID = fsn.y + 100
    cx0 = dirc.x + 45
    cv.poly([(cx0, dirc.y), (cx0, MID), (fsn.x, MID)], start="dia", end="arr")
    cv.label(cx0 + 10, dirc.y - 14, "1", size=12)
    cv.label(fsn.x - 8, MID - 8, "children  0..*", anchor="end", size=12)
    cv.label(cx0 + 10, MID + 22, "рекурсивная композиция")

    ax = proxy.r - 50
    cv.poly([(ax, proxy.y), (ax, MID), (fsn.r, MID)], start="odia", end="arr")
    cv.label(fsn.r + 8, MID - 8, "_subject  1", size=12)
    cv.label(fsn.r + 8, MID + 22, "реальный узел (передаётся извне)")

    ay = svc.cy
    cv.poly([(proxy.r, ay), (svc.x, ay)], end="arr")
    cv.label(proxy.r + 8, ay - 8, "_access 1")

    gx = 1285
    cv.poly([(proxy.r, proxy.b - 28), (gx, proxy.b - 28), (gx, user.cy), (user.x, user.cy)], end="arr")
    cv.label(gx + 8, user.cy - 8, "_user 1")

    cv.poly([(acl.cx, acl.y), (acl.cx, svc.b)], dashed=True, end="tri")
    cv.label(acl.cx + 12, (acl.y + svc.b) / 2 + 5, "реализует")
    cv.poly([(user.cx, acl.b), (user.cx, user.y)], dashed=True, end="arr")
    cv.poly([(perm.cx, acl.b), (perm.cx, perm.y)], dashed=True, end="arr")
    cv.label(user.cx + 10, acl.b + 33, "«use»")
    cv.label(perm.cx + 10, acl.b + 33, "«use»")

    cv.poly([(dirc.cx, dirc.b), (dirc.cx, inv.y)], dashed=True, end="arr")
    cv.label(dirc.cx + 10, (dirc.b + inv.y) / 2 + 5, "«raise»  (каталог в самого себя)")
    cv.poly([(proxy.cx, proxy.b), (proxy.cx, den.y)], dashed=True, end="arr")
    cv.label(proxy.cx + 10, (proxy.b + den.y) / 2 + 5, "«raise»  (нет права)")

    cy0 = app.y + 30
    cv.poly([(app.cx, app.y), (app.cx, ZBOT)], dashed=True, end="arr")
    cv.poly([(app.x, cy0), (400, cy0), (400, ZBOT)], dashed=True, end="arr")
    cv.poly([(app.r, cy0), (1550, cy0), (1550, ZBOT)], dashed=True, end="arr")
    cv.label(app.cx + 10, ZBOT + 40, "«create»")
    cv.label(410, ZBOT + 40, "«create»  узлы")
    cv.label(1560, ZBOT + 40, "«create»  сервис прав")

    cv.legend(1325, 62, 455, [(C_PATTERN, "введено шаблоном"),
                              (C_ROLE, "предметная область, получившая роль в шаблоне"),
                              (C_DOMAIN, "предметная область"),
                              (C_ROOT, "точка сборки объектов")],
              note="[READ] / [LIST] — право, которое Proxy проверяет до делегирования")
    cv.save(path, W, H, "Вариант 2.3. Виртуальная файловая система — диаграмма классов (Composite + Proxy)")
    return W, H


# =============================================================== 2.3.3
def extension_diagram(path):
    cv = Canvas()
    fsn = cv.box(560, 70, 380, "FileSystemNode", "«abstract» · Component / Subject",
                 ops=list(NODE_OPS), fill=C_PATTERN, italic_name=True, italic_ops=NODE_OPS)
    ZTOP = fsn.b + 75
    ROW = ZTOP + 40
    leaf = cv.box(50, ROW, 160, "FileLeaf", "Leaf", fill=C_OLD)
    dirc = cv.box(230, ROW, 210, "DirectoryComposite", "Composite", fill=C_OLD)
    prot = cv.box(460, ROW, 210, "ProtectedNodeProxy", "Protection Proxy", fill=C_OLD)
    link = cv.box(730, ROW, 330, "SymbolicLink", "Proxy (ссылка на цель)",
                  attrs=["- _target: FileSystemNode", "- _resolving: bool"],
                  ops=["+ target: FileSystemNode «property»",
                       "+ size(): int  [0, не следует]",
                       "+ print_tree(depth: int = 0): str  [следует]",
                       "+ find(name: str): FileSystemNode | None  [следует]",
                       "+ contains(node): bool",
                       "- _follow()  «contextmanager»"], fill=C_NEW)
    lazy = cv.box(1100, ROW, 380, "LazyRemoteFileProxy", "Virtual Proxy + кэш метаданных",
                  attrs=["- _storage: RemoteStorage", "- _remote_path: str",
                         "- _metadata: RemoteMetadata | None"],
                  ops=["+ is_loaded: bool «property»",
                       "+ size(): int  [загрузка]",
                       "+ print_tree(depth: int = 0): str  [загрузка]",
                       "+ find(name: str): FileSystemNode | None",
                       "+ contains(node): bool",
                       "- _load(): RemoteMetadata"], fill=C_NEW)
    meta = cv.box(1530, ROW + 20, 220, "RemoteMetadata", "«dataclass»", attrs=["+ size: int"], fill=C_NEW)
    R2 = max(link.b, lazy.b) + 60
    cyc = cv.box(link.cx - 125, R2, 250, "CycleDetectedError", "«exception»", fill=C_NEW)
    store = cv.box(1100, R2, 380, "RemoteStorage", "«interface» (ABC)",
                   ops=["+ fetch_metadata(path: str): RemoteMetadata"], fill=C_NEW, italic_name=True)
    mem = cv.box(1100, store.b + 60, 380, "InMemoryRemoteStorage", "заглушка сервера без сети",
                 attrs=["- _objects: dict[str, int]", "+ requests: list[str]"],
                 ops=["+ put(path: str, size: int)", "+ fetch_metadata(path: str): RemoteMetadata"],
                 fill=C_NEW)
    rerr = cv.box(1530, mem.y + 20, 220, "RemoteStorageError", "«exception»", fill=C_NEW)
    ZBOT = max(mem.b, cyc.b) + 30
    old_bot = prot.b + 30
    app = cv.box(560, ZBOT + 75, 470, "main", "«module» · composition root — изменён",
                 ops=["+ build_extended_tree(access, user, storage): FileSystemNode",
                      "  cloud.add(ProtectedNodeProxy(LazyRemoteFileProxy(...)))",
                      "  docs.add(SymbolicLink(\"loop\", docs))"], fill=C_CHANGED)
    W, H = 1790, app.b + 40

    cv.zone(30, ZTOP, 660, old_bot - ZTOP, "Существующие классы — не менялись", "#78909C", bottom=True)
    cv.zone(710, ZTOP, 1060, ZBOT - ZTOP, "Добавлено в 2.3.3 — новые файлы symlink.py, remote.py", "#8E24AA", tab=110, bottom=True)

    BUS = fsn.b + 38
    xs = [leaf.cx, dirc.cx, prot.cx, link.cx, lazy.cx]
    cv.poly([(xs[0], leaf.y), (xs[0], BUS), (xs[-1], BUS), (xs[-1], lazy.y)])
    for b in (dirc, prot, link):
        cv.poly([(b.cx, b.y), (b.cx, BUS)])
    cv.poly([(fsn.cx, BUS), (fsn.cx, fsn.b)], end="tri")
    cv.label(fsn.cx + 10, BUS - 12, "все новые узлы реализуют тот же контракт")

    MID = fsn.y + 70
    tx = link.r - 40
    cv.poly([(tx, link.y), (tx, MID), (fsn.r, MID)], start="odia", end="arr")
    cv.label(fsn.r + 8, MID - 8, "_target  1", size=12)
    cv.label(fsn.r + 8, MID + 22, "цель ссылки (не владеет ею)")

    cv.poly([(link.cx, link.b), (link.cx, cyc.y)], dashed=True, end="arr")
    cv.label(link.cx + 10, (link.b + cyc.y) / 2 + 5, "«raise» (повторный вход)")

    cv.poly([(lazy.cx, lazy.b), (lazy.cx, store.y)], end="arr")
    cv.label(lazy.cx + 10, (lazy.b + store.y) / 2 + 5, "_storage 1")
    my = meta.cy
    cv.poly([(lazy.r, my), (meta.x, my)], start="dia")
    cv.label(lazy.r + 6, my - 8, "0..1 кэш", size=11)

    cv.poly([(mem.cx, mem.y), (mem.cx, store.b)], dashed=True, end="tri")
    cv.label(mem.cx + 12, (mem.y + store.b) / 2 + 5, "реализует")
    sy = store.cy
    cv.poly([(store.r, sy), (meta.cx, sy), (meta.cx, meta.b)], dashed=True, end="arr")
    cv.label(store.r + 8, sy - 8, "«create»")
    ey = rerr.cy
    cv.poly([(mem.r, ey), (rerr.x, ey)], dashed=True, end="arr")
    cv.label(mem.r + 6, ey - 8, "«raise»", size=11)

    cv.poly([(app.cx, app.y), (app.cx, ZBOT)], dashed=True, end="arr")
    cv.label(app.cx + 10, ZBOT + 40, "«create»  новые узлы и цепочку Protected(Lazy)")

    note_y = old_bot + 50
    cv.add(f'<rect x="40" y="{note_y}" width="630" height="128" rx="6" fill="#FFFDE7" stroke="#B0A060"/>')
    for i, t in enumerate(["Цепочка для удалённого файла (собирается в main):",
                           "DirectoryComposite → ProtectedNodeProxy → LazyRemoteFileProxy → RemoteStorage",
                           "Права проверяются снаружи, поэтому при отказе загрузки нет.",
                           "FileLeaf и DirectoryComposite зависят только от FileSystemNode,",
                           "поэтому новые виды узлов встраиваются без их изменения (OCP)."]):
        cv.text(54, note_y + 24 + i * 22, t, size=12.5, weight="bold" if i == 0 else "normal")

    cv.legend(30, 62, 470, [(C_OLD, "существующий класс, не изменялся"),
                            (C_NEW, "добавлено при расширении"),
                            (C_CHANGED, "изменённый модуль (только точка сборки)"),
                            (C_PATTERN, "общий контракт")], notation=False)
    cv.save(path, W, H, "Вариант 2.3. Расширение 2.3.3: SymbolicLink и LazyRemoteFileProxy")
    return W, H


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    for name, fn in (("class_diagram.svg", class_diagram), ("class_diagram_extension.svg", extension_diagram)):
        w, h = fn(os.path.join(out, name))
        print(name, w, h)
