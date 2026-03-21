#!/usr/bin/env python3
"""
parabolic-outlet — aerodynamic air outlet template generator

Generates a 3D visualization + 2D flat-cut template for a parabolic
air outlet intended for fabrication from 1mm (or any) PET/acrylic sheet.

Geometry (top view):
    x(s) = D · (1 - s²)     s ∈ [-1, 1]
    y(s) = (W/2) · s

The outlet has two flat-cut pieces:
    A  — top face (parabolic outline, no bending)
    B  — side wall strip (rectangle, bend along length to follow curve)

Usage:
    python outlet.py
    python outlet.py --width 120 --depth 150 --output my_outlet.png
    python outlet.py -w 60 -d 80 --dpi 300 --show
"""

import argparse
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# ─── colours ──────────────────────────────────────────────────────────────────
BG     = '#0d0d12'
CYAN   = '#00d4ff'
GOLD   = '#ffc72c'
ORANGE = '#ff6b35'
GREEN  = '#39ff14'
WHITE  = '#e8e8e8'


# ─── geometry ─────────────────────────────────────────────────────────────────
def compute_geometry(W, D, N=400):
    """Return parabola curve arrays and arc-length data."""
    H   = W / 2
    s   = np.linspace(-1, 1, N)
    xp  = D * (1 - s**2)
    yp  = (W / 2) * s
    dxds = np.gradient(xp, s)
    dyds = np.gradient(yp, s)
    elem = np.sqrt(dxds**2 + dyds**2)
    arc_cum   = np.concatenate([[0], np.cumsum(
        0.5 * (elem[:-1] + elem[1:]) * np.diff(s))])
    arc_total = arc_cum[-1]
    return H, s, xp, yp, arc_total


# ─── helpers ──────────────────────────────────────────────────────────────────
def dim_h(ax, x1, x2, y, label, dy=0):
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='<->', color=GOLD,
                                lw=1.1, shrinkA=0, shrinkB=0))
    ax.text((x1+x2)/2, y+dy, label, color=GOLD, fontsize=7.5,
            ha='center', va='center', fontfamily='monospace',
            bbox=dict(fc=BG, ec='none', pad=1.5))


def dim_v(ax, y1, y2, x, label, dx=0):
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='<->', color=GOLD,
                                lw=1.1, shrinkA=0, shrinkB=0))
    ax.text(x+dx, (y1+y2)/2, label, color=GOLD, fontsize=7.5,
            ha='center', va='center', fontfamily='monospace',
            rotation=90, bbox=dict(fc=BG, ec='none', pad=1.5))


# ─── main render ──────────────────────────────────────────────────────────────
def render(W, D, output, dpi, show):
    H, s, xp, yp, arc_total = compute_geometry(W, D)
    arc_half = arc_total / 2

    fig = plt.figure(figsize=(22, 11), facecolor=BG)
    fig.text(0.5, 0.978,
             f'PARABOLIC AIR OUTLET  |  W={W:.0f}mm  H={H:.0f}mm  D={D:.0f}mm  |  1mm PET TEMPLATE',
             ha='center', va='top', color=WHITE, fontsize=12,
             fontfamily='monospace', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.4', fc='#1a1a26', ec=CYAN, lw=0.7, alpha=0.9))

    # ── 3D view ───────────────────────────────────────────────────────────────
    ax3 = fig.add_axes([0.01, 0.05, 0.40, 0.90], projection='3d')
    ax3.set_facecolor(BG)

    # top face surface
    u_t  = np.linspace(0, 0.999, 70)
    v_t  = np.linspace(-1, 1, 50)
    U, V = np.meshgrid(u_t, v_t)
    Xt = U * D
    Yt = V * (W/2) * np.sqrt(1 - U)
    Zt = np.full_like(Xt, H)
    ax3.plot_surface(Xt, Yt, Zt, alpha=0.30, color=CYAN, linewidth=0, antialiased=True)

    # side wall surface
    s_sw      = np.linspace(-1, 1, 100)
    z_sw      = np.linspace(0, H, 40)
    Ssw, Zsw  = np.meshgrid(s_sw, z_sw)
    Xsw = D * (1 - Ssw**2)
    Ysw = (W/2) * Ssw
    ax3.plot_surface(Xsw, Ysw, Zsw, alpha=0.18, color=CYAN, linewidth=0, antialiased=True)

    # edges
    ax3.plot(xp, yp, H,  color=CYAN, lw=1.8)
    ax3.plot(xp, yp, 0,  color=CYAN, lw=0.8, alpha=0.25, ls='--')
    ax3.plot([0,0], [-W/2, W/2], [H, H], color=CYAN, lw=2.0)
    ax3.plot([0,0], [-W/2, W/2], [0,  0], color=CYAN, lw=0.8, alpha=0.25)
    ax3.plot([0,0], [ W/2,  W/2], [0, H], color=CYAN, lw=1.5)
    ax3.plot([0,0], [-W/2, -W/2], [0, H], color=CYAN, lw=1.5)
    ax3.plot([D,D], [0, 0], [0, H], color=CYAN, lw=1.2, alpha=0.45)

    # front opening face
    fp = [[0,-W/2,0],[0,W/2,0],[0,W/2,H],[0,-W/2,H]]
    ax3.add_collection3d(Poly3DCollection(
        [fp], alpha=0.22, facecolor='#4488ff', edgecolor=CYAN, lw=1.0))

    ax3.text(D/2,  W/2+12, H+3, f'W={W:.0f}mm',  color=GOLD, fontsize=7.5, fontfamily='monospace')
    ax3.text(D+5,  0,      H/2, f'H={H:.0f}mm',  color=GOLD, fontsize=7.5, fontfamily='monospace')
    ax3.text(D/2, -W/2-14, -4,  f'D={D:.0f}mm',  color=GOLD, fontsize=7.5, fontfamily='monospace')

    ax3.set_xlabel('depth',  color='#555', fontsize=7, labelpad=1)
    ax3.set_ylabel('width',  color='#555', fontsize=7, labelpad=1)
    ax3.set_zlabel('height', color='#555', fontsize=7, labelpad=1)
    ax3.tick_params(colors='#3a3a3a', labelsize=5)
    for pane in [ax3.xaxis.pane, ax3.yaxis.pane, ax3.zaxis.pane]:
        pane.fill = False
        pane.set_edgecolor('#1e1e1e')
    ax3.set_box_aspect([D, W, H])
    ax3.view_init(elev=24, azim=-52)
    ax3.set_title('3D VIEW', color='#888', fontsize=10, fontfamily='monospace', pad=6)

    # ── Piece A: top face ─────────────────────────────────────────────────────
    ax_a = fig.add_axes([0.43, 0.38, 0.28, 0.57])
    ax_a.set_facecolor(BG)
    ax_a.set_aspect('equal')

    ox = np.concatenate([[0], xp, [0]])
    oy = np.concatenate([[-W/2], yp, [W/2]])
    ax_a.fill(ox, oy, color=CYAN, alpha=0.10)
    ax_a.plot(ox, oy, color=CYAN, lw=2.0)

    for xg in np.arange(10, D, 10):
        y_max = (W/2) * np.sqrt(max(0.0, 1 - xg/D))
        ax_a.plot([xg, xg], [-y_max, y_max], color=WHITE, alpha=0.06, lw=0.5)
    for yg in np.arange(-W/2+10, W/2, 10):
        x_edge = D * (1 - (yg/(W/2))**2)
        ax_a.plot([0, x_edge], [yg, yg], color=WHITE, alpha=0.06, lw=0.5)

    dim_h(ax_a, 0, D, -W/2-10, f'D = {D:.0f} mm', dy=-4)
    dim_v(ax_a, -W/2, W/2, D+10, f'W = {W:.0f} mm', dx=4)

    ax_a.text(D*0.42, 0,   'A',         color=CYAN,  fontsize=36, ha='center', va='center',
              fontfamily='monospace', alpha=0.15, fontweight='bold')
    ax_a.text(D*0.20, -2,  'TOP FACE',  color='#777', fontsize=7.5, ha='center', va='center',
              fontfamily='monospace', style='italic')
    ax_a.text(D*0.20, -8, 'flat  no bending', color='#555', fontsize=6.5, ha='center', va='center',
              fontfamily='monospace')
    ax_a.plot([0,0], [-W/2, W/2], color=GREEN, lw=2.5)
    ax_a.text(-3, 0, 'opening\nedge', color=GREEN, fontsize=6.5, ha='right', va='center',
              fontfamily='monospace')

    ax_a.set_xlim(-15, D+26)
    ax_a.set_ylim(-W/2-22, W/2+14)
    ax_a.axis('off')
    ax_a.set_title('PIECE  A  --  TOP FACE\nCut 1x  from 1mm PET',
                   color='#aaa', fontsize=9, fontfamily='monospace', pad=6)

    # ── Piece B: side wall strip ───────────────────────────────────────────────
    ax_b = fig.add_axes([0.43, 0.04, 0.55, 0.30])
    ax_b.set_facecolor(BG)
    ax_b.set_aspect('equal')

    rect = mpatches.FancyBboxPatch(
        (0, 0), arc_total, H, boxstyle='square,pad=0', lw=2,
        edgecolor=CYAN, facecolor=CYAN, alpha=0.10)
    ax_b.add_patch(rect)

    ax_b.plot([arc_half, arc_half], [0, H], color=ORANGE, lw=1.6, ls='--')
    ax_b.plot(arc_half, H, 'v', color=ORANGE, ms=7)
    ax_b.plot(arc_half, 0, '^', color=ORANGE, ms=7)
    ax_b.text(arc_half, H*1.10,
              f'fold ref -- back tip  ({arc_half:.1f} mm)',
              color=ORANGE, fontsize=7, fontfamily='monospace', ha='center', va='bottom')

    ax_b.text(arc_half/2,           H/2, 'LEFT WALL',  color=CYAN, fontsize=8,
              fontfamily='monospace', ha='center', va='center', alpha=0.7)
    ax_b.text(arc_half+arc_half/2,  H/2, 'RIGHT WALL', color=CYAN, fontsize=8,
              fontfamily='monospace', ha='center', va='center', alpha=0.7)

    ax_b.plot([0, 0],               [0, H], color=GREEN, lw=2.8)
    ax_b.plot([arc_total, arc_total],[0, H], color=GREEN, lw=2.8)
    ax_b.text(-2,           H/2, '< opening\n  edge', color=GREEN, fontsize=6.5,
              fontfamily='monospace', ha='right', va='center')
    ax_b.text(arc_total+2,  H/2, 'opening\nedge >', color=GREEN, fontsize=6.5,
              fontfamily='monospace', ha='left', va='center')

    dim_h(ax_b, 0, arc_total, -H*0.38, f'L = {arc_total:.1f} mm  (arc length)', dy=-3)
    dim_h(ax_b, 0, arc_half,  -H*0.16, f'{arc_half:.1f} mm', dy=-3)
    dim_v(ax_b, 0, H, arc_total+H*0.30, f'H = {H:.0f} mm', dx=4)

    ax_b.text(arc_total*0.5, H*0.5, 'B', color=CYAN, fontsize=50,
              ha='center', va='center', fontfamily='monospace', alpha=0.12, fontweight='bold')

    ax_b.set_xlim(-arc_total*0.10, arc_total*1.14)
    ax_b.set_ylim(-H*0.65, H*1.40)
    ax_b.axis('off')
    ax_b.set_title(
        f'PIECE  B  --  SIDE WALL STRIP  |  bend gradually along length to follow parabola\n'
        f'Cut 1x  from 1mm PET  |  {arc_total:.1f} mm x {H:.0f} mm',
        color='#aaa', fontsize=9, fontfamily='monospace', pad=6)

    # ── legend + assembly note ─────────────────────────────────────────────────
    handles = [
        mpatches.Patch(color=CYAN,   label='cut line'),
        mpatches.Patch(color=GREEN,  label='opening edge'),
        mpatches.Patch(color=ORANGE, label='fold reference'),
        mpatches.Patch(color=GOLD,   label='dimension'),
    ]
    fig.legend(handles=handles, loc='upper right', bbox_to_anchor=(0.985, 0.965),
               framealpha=0.15, facecolor='#1a1a26', edgecolor='#333',
               labelcolor=WHITE, ncol=4,
               prop={'family': 'monospace', 'size': 7.5})

    fig.text(0.435, 0.012,
             '[1] Cut A and B.  '
             '[2] Bend strip B at center mark into a U-shape (both walls, one piece).  '
             '[3] Attach B top edge to curved edges of A (solvent cement or tape).  '
             '[4] Green edges = opening -- mount flush on surface.',
             ha='left', va='bottom', color='#666', fontsize=7, fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=0.3', fc='#1a1a24', ec='#2a2a2a', lw=0.5))

    # ── save ──────────────────────────────────────────────────────────────────
    plt.savefig(output, dpi=dpi, bbox_inches='tight', facecolor=BG)
    if show:
        matplotlib.use('TkAgg')
        plt.show()
    plt.close()


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Generate a parabolic air outlet template for cutting from PET sheet.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)

    parser.add_argument('-w', '--width',  type=float, default=80.0,
                        help='Opening width in mm (default: 80)')
    parser.add_argument('-d', '--depth',  type=float, default=100.0,
                        help='Outlet depth in mm (default: 100)')
    parser.add_argument('-o', '--output', default='outlet_template.png',
                        help='Output PNG filename (default: outlet_template.png)')
    parser.add_argument('--dpi', type=int, default=150,
                        help='Output resolution in DPI (default: 150)')
    parser.add_argument('--show', action='store_true',
                        help='Open the image after saving (requires display)')

    args = parser.parse_args()

    if args.width <= 0 or args.depth <= 0:
        print("Error: width and depth must be positive.", file=sys.stderr)
        sys.exit(1)

    H = args.width / 2
    _, _, _, _, arc = compute_geometry(args.width, args.depth)

    print(f"  Width   W = {args.width:.1f} mm")
    print(f"  Height  H = {H:.1f} mm  (W/2)")
    print(f"  Depth   D = {args.depth:.1f} mm")
    print(f"  Arc length (strip B) = {arc:.1f} mm")
    print()

    render(args.width, args.depth, args.output, args.dpi, args.show)

    print(f"Saved -> {args.output}")
    print()
    print("Cut list:")
    print(f"  Piece A  top face      parabolic flat   {args.depth:.0f} mm x {args.width:.0f} mm")
    print(f"  Piece B  side walls    rectangle strip  {arc:.1f} mm x {H:.0f} mm")


if __name__ == '__main__':
    main()
