import React, { useEffect, useRef } from 'react';

/**
 * Procedural low-poly geometric mesh art panel.
 * Adapted to the Frozen Lake palette (Deep Navy → Ice/Cyan Blue).
 * Features interactive triangle hover elevation, glow, and dynamic SVG stack re-ordering.
 */
export default function AuthMeshArt() {
  const meshHostRef = useRef(null);

  useEffect(() => {
    const host = meshHostRef.current;
    if (!host) return;

    host.innerHTML = '';

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function mulberry32(seed) {
      return function () {
        seed |= 0;
        seed = (seed + 0x6d2b79f5) | 0;
        let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };
    }

    const rand = mulberry32(1337);

    function lerp(a, b, t) { return a + (b - a) * t; }
    function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

    function facetColor(cx, cy, w, h) {
      const t = clamp((cx / w) * 0.55 + (cy / h) * 0.75, 0, 1);
      let hue = lerp(164, 142, t);
      let sat = lerp(68, 85, t);
      let light = lerp(24, 48, t);
      const jitter = (rand() - 0.5) * 10;
      light = clamp(light + jitter, 18, 58);
      hue += (rand() - 0.5) * 4;
      if (rand() > 0.975) {
        light = clamp(light + 18, 0, 70);
        sat = clamp(sat - 6, 0, 100);
      } else if (rand() > 0.955) {
        light = clamp(light - 10, 12, 100);
      }
      return `hsl(${hue.toFixed(1)} ${sat.toFixed(0)}% ${light.toFixed(0)}%)`;
    }

    const W = 1000, H = 1000;
    const cols = 10, rows = 10;
    const cellW = W / cols, cellH = H / rows;
    const jitterAmt = Math.min(cellW, cellH) * 0.3;

    const pts = [];
    for (let r = 0; r <= rows; r++) {
      pts[r] = [];
      for (let c = 0; c <= cols; c++) {
        const edge = r === 0 || r === rows || c === 0 || c === cols;
        const jx = edge ? 0 : (rand() - 0.5) * jitterAmt;
        const jy = edge ? 0 : (rand() - 0.5) * jitterAmt;
        pts[r][c] = [c * cellW + jx, r * cellH + jy];
      }
    }

    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid slice');

    const frag = document.createDocumentFragment();
    const order = [];

    for (let ri = 0; ri < rows; ri++) {
      for (let ci = 0; ci < cols; ci++) {
        const a = pts[ri][ci];
        const b = pts[ri][ci + 1];
        const d = pts[ri + 1][ci];
        const e = pts[ri + 1][ci + 1];
        const flip = rand() > 0.5;
        const triA = flip ? [a, b, d] : [a, b, e];
        const triB = flip ? [b, e, d] : [a, e, d];
        order.push(triA, triB);
      }
    }

    order.forEach((tri) => {
      const cx = (tri[0][0] + tri[1][0] + tri[2][0]) / 3;
      const cy = (tri[0][1] + tri[1][1] + tri[2][1]) / 3;

      const poly = document.createElementNS(svgNS, 'polygon');
      poly.setAttribute(
        'points',
        tri.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ')
      );
      poly.setAttribute('fill', facetColor(cx, cy, W, H));
      poly.classList.add('facet-poly-auth');

      if (!reduceMotion) {
        poly.style.animationDelay = (rand() * 0.5).toFixed(2) + 's';
      }

      poly.addEventListener('mouseenter', () => {
        svg.appendChild(poly);
        poly.classList.add('poly-hovered-auth');
      });

      poly.addEventListener('mouseleave', () => {
        poly.classList.remove('poly-hovered-auth');
      });

      frag.appendChild(poly);
    });

    svg.appendChild(frag);
    host.appendChild(svg);

    let raf = null;
    const artPanel = host.closest('.panel-art-auth');

    const handleMouseMove = (e) => {
      if (reduceMotion || !artPanel) return;
      const rect = artPanel.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / rect.width - 0.5;
      const ny = (e.clientY - rect.top) / rect.height - 0.5;

      if (raf) cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        if (svg) {
          svg.style.transform = `translate(${(nx * -14).toFixed(1)}px, ${(ny * -10).toFixed(1)}px) scale(1.03)`;
        }
      });
    };

    const handleMouseLeave = () => {
      if (svg) {
        svg.style.transform = 'translate(0,0) scale(1)';
      }
    };

    if (artPanel && !reduceMotion && window.matchMedia('(pointer: fine)').matches) {
      artPanel.addEventListener('mousemove', handleMouseMove);
      artPanel.addEventListener('mouseleave', handleMouseLeave);
    }

    return () => {
      if (raf) cancelAnimationFrame(raf);
      if (artPanel) {
        artPanel.removeEventListener('mousemove', handleMouseMove);
        artPanel.removeEventListener('mouseleave', handleMouseLeave);
      }
    };
  }, []);

  return (
    <>
      <div className="art-mesh-auth" id="artMesh" ref={meshHostRef} />
      <div className="art-shade-auth" />
    </>
  );
}
