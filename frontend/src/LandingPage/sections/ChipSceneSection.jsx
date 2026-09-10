import React, { useEffect, useRef, useState } from "react";

const VW = 1400;
const VH = 500;

const CHIP = { x: 570, y: 155, w: 260, h: 140 };

const MODULES = [
    { id: "soil", label: "SOIL AI", dir: "in", color: [16, 185, 129], pts: [[40, 90], [460, 90], [460, 167], [561, 167]], delay: 0, dur: 6.0 },
    { id: "irrigation", label: "IRRIGATION", dir: "out", color: [255, 140, 66], pts: [[561, 183], [100, 183], [100, 148], [40, 148]], delay: 1.6, dur: 7.0 },
    { id: "pest", label: "PEST CNNs", dir: "in", color: [236, 72, 153], pts: [[40, 230], [460, 230], [460, 199], [561, 199]], delay: 0.8, dur: 6.5 },
    { id: "crop", label: "CROP REC", dir: "out", color: [245, 158, 11], pts: [[561, 215], [110, 215], [110, 310], [40, 310]], delay: 2.4, dur: 7.2 },
    { id: "nextjs", label: "NEXT.JS", dir: "in", color: [132, 204, 22], pts: [[460, 22], [460, 95], [625, 95], [625, 147]], delay: 0.3, dur: 5.8 },
    { id: "fastapi", label: "FASTAPI", dir: "out", color: [20, 184, 166], pts: [[655, 147], [655, 22]], delay: 1.4, dur: 5.5 },
    { id: "tensorflow", label: "TensorFlow", dir: "in", color: [255, 107, 107], pts: [[860, 22], [860, 80], [715, 80], [715, 147]], delay: 2.2, dur: 6.2 },
    { id: "nextapi", label: "NEXT·API", dir: "in", color: [139, 92, 246], pts: [[1040, 22], [1040, 60], [775, 60], [775, 147]], delay: 3.2, dur: 6.4 },
    { id: "python", label: "PYTHON", dir: "in", color: [250, 204, 21], pts: [[150, 478], [150, 360], [625, 360], [625, 303]], delay: 0.5, dur: 7.2 },
    { id: "lstm", label: "LSTM", dir: "in", color: [217, 119, 6], pts: [[340, 478], [340, 400], [655, 400], [655, 303]], delay: 1.8, dur: 6.6 },
    { id: "cnn", label: "CNN", dir: "in", color: [139, 92, 246], pts: [[715, 478], [715, 303]], delay: 2.8, dur: 5.8 },
    { id: "transformers", label: "TRANSFORMERS", dir: "in", color: [236, 72, 153], pts: [[980, 478], [980, 380], [775, 380], [775, 303]], delay: 3.8, dur: 6.8 },
    { id: "yield", label: "YIELD LSTM", dir: "in", color: [132, 204, 22], pts: [[1360, 130], [1050, 130], [1050, 167], [839, 167]], delay: 0.9, dur: 7.0 },
    { id: "market", label: "MARKET AI", dir: "out", color: [255, 140, 66], pts: [[839, 183], [1360, 183]], delay: 2.0, dur: 6.4 },
    { id: "growth", label: "GROWTH MON", dir: "in", color: [20, 184, 166], pts: [[1360, 290], [1180, 290], [1180, 199], [839, 199]], delay: 1.4, dur: 6.8 },
    { id: "kubernetes", label: "KUBERNETES", dir: "in", color: [250, 204, 21], pts: [[1360, 400], [1100, 400], [1100, 215], [839, 215]], delay: 3.4, dur: 7.5 },
];

const PIN_W = 12;
const PIN_H = 16;
const TOP_BOT_PIN_CENTERS = [625, 655, 685, 715, 745, 775];
const ACTIVE_PIN_CENTERS = new Set([625, 655, 715, 775]);
const TOP_PIN_Y = 155 - PIN_H;
const BOT_PIN_Y = 295;

function buildPath(pts) {
    const segs = [];
    let total = 0;
    for (let i = 1; i < pts.length; i++) {
        const dx = pts[i][0] - pts[i - 1][0];
        const dy = pts[i][1] - pts[i - 1][1];
        const len = Math.sqrt(dx * dx + dy * dy);
        segs.push({ x0: pts[i - 1][0], y0: pts[i - 1][1], x1: pts[i][0], y1: pts[i][1], len, start: total });
        total += len;
    }
    return { segs, total };
}

function pointAt(path, t) {
    const d = Math.max(0, Math.min(path.total, t));
    for (const seg of path.segs) {
        if (d <= seg.start + seg.len) {
            const r = (d - seg.start) / seg.len;
            return [seg.x0 + r * (seg.x1 - seg.x0), seg.y0 + r * (seg.y1 - seg.y0)];
        }
    }
    const last = path.segs[path.segs.length - 1];
    return [last.x1, last.y1];
}

function chipOcclusion(x, y) {
    if (x >= CHIP.x && x <= CHIP.x + CHIP.w && y >= CHIP.y && y <= CHIP.y + CHIP.h) return 1.0;
    const pad = 10;
    const cx = CHIP.x - pad, cy = CHIP.y - pad;
    const cw = CHIP.w + pad * 2, ch = CHIP.h + pad * 2;
    if (x < cx || x > cx + cw || y < cy || y > cy + ch) return 0;
    const dx = Math.min(x - cx, cx + cw - x) / pad;
    const dy = Math.min(y - cy, cy + ch - y) / pad;
    return Math.min(Math.min(dx, dy, 1), 1);
}

export default function ChipSceneSection() {
    const canvasRef = useRef(null);
    const svgRef = useRef(null);
    const rafRef = useRef(null);
    const sectionRef = useRef(null);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setIsVisible(true);
                    observer.disconnect();
                }
            },
            { threshold: 0.15 }
        );

        if (sectionRef.current) {
            observer.observe(sectionRef.current);
        }

        return () => observer.disconnect();
    }, []);

    const paths = MODULES.map(m => buildPath(m.pts));

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        let startTime = null;
        let isOnScreen = false;
        let isPausedForResize = false;

        canvas.width = VW;
        canvas.height = VH;

        function drawFrame(ts) {
            if (!isOnScreen || isPausedForResize) {
                if (isOnScreen) rafRef.current = requestAnimationFrame(drawFrame);
                return;
            }
            if (!startTime) startTime = ts;
            const elapsed = (ts - startTime) / 1000;

            ctx.clearRect(0, 0, VW, VH);

            MODULES.forEach((m, i) => {
                const path = paths[i];
                const [r, g, b] = m.color;

                const raw = (elapsed - m.delay) % m.dur;
                if (raw < 0) return;
                const cycleT = raw / m.dur;

                const headDist = cycleT * (path.total + 180) - 60;
                const tailLen = 160;

                let envAlpha = 1;
                if (cycleT < 0.08) envAlpha = cycleT / 0.08;
                else if (cycleT > 0.90) envAlpha = (1 - cycleT) / 0.10;
                envAlpha = Math.max(0, Math.min(1, envAlpha));
                if (envAlpha < 0.01) return;

                const STEPS = 36;
                ctx.lineCap = "round";
                ctx.lineJoin = "round";

                for (let s = 0; s < STEPS - 1; s++) {
                    const tNorm0 = s / (STEPS - 1);
                    const tNorm1 = (s + 1) / (STEPS - 1);

                    const dist0 = headDist - tailLen * (1 - tNorm0);
                    const dist1 = headDist - tailLen * (1 - tNorm1);

                    if (dist1 < -10 || dist0 > path.total + 10) continue;

                    const [px, py] = pointAt(path, dist0);
                    const [nx, ny] = pointAt(path, dist1);

                    const occ0 = chipOcclusion(px, py);
                    const occ1 = chipOcclusion(nx, ny);
                    const depth = 1 - (occ0 + occ1) * 0.5;

                    const trailAlpha = Math.pow(tNorm0, 2.2);
                    const flicker = tNorm0 > 0.3 && tNorm0 < 0.85
                        ? 0.88 + 0.12 * Math.sin(elapsed * 12 + dist0 * 0.04 + i * 1.3)
                        : 1.0;

                    const alpha = trailAlpha * envAlpha * depth * flicker;
                    if (alpha < 0.004) continue;

                    ctx.beginPath();
                    ctx.moveTo(px, py);
                    ctx.lineTo(nx, ny);
                    ctx.strokeStyle = `rgba(${r},${g},${b},${alpha * 0.5})`;
                    ctx.lineWidth = 3.5;
                    ctx.stroke();

                    ctx.beginPath();
                    ctx.moveTo(px, py);
                    ctx.lineTo(nx, ny);
                    ctx.strokeStyle = `rgba(${r},${g},${b},${alpha * 0.98})`;
                    ctx.lineWidth = 1.5;
                    ctx.stroke();

                    if (tNorm0 > 0.5) {
                        const coreA = Math.pow((tNorm0 - 0.5) / 0.5, 1.5) * alpha;
                        ctx.beginPath();
                        ctx.moveTo(px, py);
                        ctx.lineTo(nx, ny);
                        ctx.strokeStyle = `rgba(255, 255, 255, ${coreA * 0.95})`;
                        ctx.lineWidth = 0.7;
                        ctx.stroke();
                    }
                }
            });

            rafRef.current = requestAnimationFrame(drawFrame);
        }

        const visObs = new IntersectionObserver(
            ([entry]) => {
                const wasOnScreen = isOnScreen;
                isOnScreen = entry.isIntersecting;
                if (isOnScreen && !wasOnScreen) {
                    rafRef.current = requestAnimationFrame(drawFrame);
                }
            },
            { threshold: 0 }
        );
        if (canvas.parentElement) visObs.observe(canvas.parentElement);

        let resizeTimer = null;
        const handleResize = () => {
            isPausedForResize = true;
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => { isPausedForResize = false; }, 250);
        };
        window.addEventListener('resize', handleResize);

        rafRef.current = requestAnimationFrame(drawFrame);

        return () => {
            isOnScreen = false;
            cancelAnimationFrame(rafRef.current);
            clearTimeout(resizeTimer);
            window.removeEventListener('resize', handleResize);
            visObs.disconnect();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const LR_PIN_W = 18;
    const LR_PIN_H = 10;
    const lrPinYs = [167, 183, 199, 215];

    return (
        <>
            <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=Sora:wght@300;400;600&display=swap');

        .chip-scene-section-chipsection {
          background: var(--chip-scene-bg);
          padding: 60px 0 72px;
          position: relative;
          overflow: hidden;
          background-image:
            linear-gradient(to right, var(--chip-grid-line) 1px, transparent 1px),
            linear-gradient(to bottom, var(--chip-grid-line) 1px, transparent 1px);
          background-size: 40px 40px;
          background-position: 40px 40px;
        }

        .chip-scene-section-chipsection .chip-scene-container-chipsection { max-width:1120px; margin:0 auto; padding:0 24px; }
        .chip-scene-section-chipsection .chip-scene-header-chipsection  { text-align:center; margin-bottom:40px; }
        .chip-scene-section-chipsection .section-eyebrow-chipsection {
          font-family:'Orbitron',monospace; font-size:11px; font-weight:600;
          letter-spacing:4px; color:var(--chip-eyebrow-color); text-transform:uppercase; margin-bottom:16px;
        }
        .chip-scene-section-chipsection .section-title-chipsection {
          font-family:'Orbitron',monospace;
          font-size:clamp(23px,3.5vw,37px); font-weight:900;
          color:var(--chip-title-color); line-height:1.2; margin:0 0 14px; letter-spacing:1px;
        }
        .chip-scene-section-chipsection .text-green-chipsection { color:var(--chip-brand-accent); }
        .chip-scene-section-chipsection .section-sub-chipsection {
          font-family:'Sora',sans-serif; font-size:14px; color:var(--chip-sub-color);
          max-width:580px; margin:0 auto; line-height:1.7; font-weight:300;
        }

        .chip-scene-section-chipsection .chip-scene-wrap-chipsection {
          width:100%; border-radius:16px;
          background-color: var(--chip-wrap-bg);
          position:relative; overflow:visible;
          padding: 24px 0;
        }

        .chip-scene-section-chipsection .chip-scene-inner-chipsection { position:relative; width:100%; z-index:1; }
        .chip-scene-section-chipsection .chip-canvas-chipsection {
          position:absolute; inset:0; width:100%; height:100%; pointer-events:none; z-index:2;
        }
        .chip-scene-section-chipsection .chip-svg-layer-chipsection { display:block; width:100%; height:auto; position:relative; z-index:1; }

        .filter-container {
          width: 100%; height: 100%; position: absolute; inset: 0;
          pointer-events: none; z-index: 3; border-radius: 16px;
        }

        .chip-scene-header-chipsection,
        .chip-scene-wrap-chipsection {
            opacity: 0; transform: translateY(60px);
            transition: opacity 2.0s cubic-bezier(0.16, 1, 0.3, 1), transform 2.0s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .chip-scene-wrap-chipsection { transition-delay: 0.5s; }

        .chip-scene-fade-in.visible .chip-scene-header-chipsection,
        .chip-scene-fade-in.visible .chip-scene-wrap-chipsection {
            opacity: 1; transform: translateY(0);
        }
      `}</style>

            <section ref={sectionRef} className={`chip-scene-section-chipsection chip-scene-fade-in ${isVisible ? 'visible' : ''}`} id="poweredby">
                <div className="chip-scene-container-chipsection">
                    <div className="chip-scene-header-chipsection">
                        <div className="section-eyebrow-chipsection">Silicon Core</div>
                        <h2 className="section-title-chipsection">
                            The Neural{' '}
                            <span className="text-green-chipsection">Processing</span>
                            <br />
                            Architecture
                        </h2>
                        <p className="section-sub-chipsection">
                            Visualizing the data pathways that connect every AI model, sensor feed,
                            and decision engine inside FarmXpert's silicon brain.
                        </p>
                    </div>

                    <div className="chip-scene-wrap-chipsection">
                        <div className="filter-container"></div>
                        <div className="chip-scene-inner-chipsection" style={{ aspectRatio: `${VW}/${VH}` }}>

                            <canvas ref={canvasRef} className="chip-canvas-chipsection" width={VW} height={VH} />

                            <svg
                                ref={svgRef}
                                className="chip-svg-layer-chipsection"
                                viewBox={`0 0 ${VW} ${VH}`}
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <defs>
                                    <clipPath id="chipClip">
                                        <rect x="570" y="155" width="260" height="140" rx="12" />
                                    </clipPath>
                                    <linearGradient id="shineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stopColor="var(--chip-shine-color)" stopOpacity="0" />
                                        <stop offset="40%" stopColor="var(--chip-shine-color)" stopOpacity="0.3" />
                                        <stop offset="50%" stopColor="var(--chip-shine-color)" stopOpacity="0.6" />
                                        <stop offset="60%" stopColor="var(--chip-shine-color)" stopOpacity="0.3" />
                                        <stop offset="100%" stopColor="var(--chip-shine-color)" stopOpacity="0" />
                                    </linearGradient>
                                    <linearGradient id="leftGlowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stopColor="var(--chip-left-glow-start)" stopOpacity="1" />
                                        <stop offset="30%" stopColor="var(--chip-left-glow-mid)" stopOpacity="1" />
                                        <stop offset="100%" stopColor="var(--chip-left-glow-end)" stopOpacity="1" />
                                    </linearGradient>
                                    <linearGradient id="chipGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                                        <stop offset="0%" stopColor="var(--chip-body-start)" />
                                        <stop offset="25%" stopColor="var(--chip-body-mid1)" />
                                        <stop offset="50%" stopColor="var(--chip-body-mid2)" />
                                        <stop offset="75%" stopColor="var(--chip-body-mid3)" />
                                        <stop offset="100%" stopColor="var(--chip-body-end)" />
                                    </linearGradient>
                                    <linearGradient id="chipSheen2" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stopColor="var(--chip-sheen-edge)" stopOpacity="1" />
                                        <stop offset="40%" stopColor="var(--chip-sheen-mid)" stopOpacity="1" />
                                        <stop offset="60%" stopColor="var(--chip-sheen-mid)" stopOpacity="1" />
                                        <stop offset="100%" stopColor="var(--chip-sheen-edge)" stopOpacity="1" />
                                    </linearGradient>
                                    <radialGradient id="chipAura" cx="50%" cy="50%" r="50%">
                                        <stop offset="0%" stopColor="var(--chip-aura-center)" stopOpacity="1" />
                                        <stop offset="100%" stopColor="var(--chip-aura-edge)" stopOpacity="1" />
                                    </radialGradient>
                                </defs>

                                <rect width={VW} height={VH} fill="transparent" />

                                {/* Static traces */}
                                <g fill="none" stroke="var(--chip-trace-color)" strokeWidth="1.3"
                                    strokeLinecap="round" strokeLinejoin="round">
                                    {MODULES.map(m => {
                                        const d = m.pts.map((p, j) => `${j === 0 ? 'M' : 'L'} ${p[0]},${p[1]}`).join(' ');
                                        return <path key={`st-${m.id}`} d={d} />;
                                    })}
                                </g>

                                {/* Chip body */}
                                <rect x="570" y="155" width="260" height="140" rx="12" fill="url(#chipGrad2)" />
                                <rect x="570" y="155" width="260" height="6" rx="3" fill="url(#chipSheen2)" />
                                <rect x="570" y="155" width="260" height="140" rx="12"
                                    fill="none" stroke="var(--chip-border)" strokeWidth="1.3" />
                                <rect x="580" y="165" width="240" height="120" rx="8"
                                    fill="none" stroke="var(--chip-inner-border)" strokeWidth="0.8" />

                                {/* Shine sweep */}
                                <g clipPath="url(#chipClip)">
                                    <rect y="155" width="90" height="140" fill="url(#shineGrad)"
                                        transform="skewX(-10)">
                                        <animateTransform attributeName="transform" type="translate"
                                            values="400,0; -150,0" additive="sum"
                                            dur="3.8s" repeatCount="indefinite" calcMode="spline"
                                            keySplines="0.4 0 0.6 1" />
                                    </rect>
                                </g>

                                {/* Glow pulse */}
                                <g clipPath="url(#chipClip)">
                                    <rect x="570" y="155" width="80" height="140" fill="url(#leftGlowGrad)"
                                        opacity="0.42" transform="skewX(-12)">
                                        <animateTransform attributeName="transform" type="translate"
                                            values="340,0; -120,0" additive="sum"
                                            dur="2.6s" repeatCount="indefinite" begin="1.2s"
                                            calcMode="spline" keySplines="0.25 0 0.6 1" />
                                    </rect>
                                </g>

                                <ellipse cx="700" cy="225" rx="160" ry="90" fill="url(#chipAura)" opacity="0.15" />

                                {/* TOP PINS */}
                                <g strokeWidth="0.7">
                                    {TOP_BOT_PIN_CENTERS.map((cx, i) => {
                                        const active = ACTIVE_PIN_CENTERS.has(cx);
                                        return (
                                            <rect key={`tp${i}`}
                                                x={cx - PIN_W / 2} y={TOP_PIN_Y}
                                                width={PIN_W} height={PIN_H} rx="2"
                                                fill={active ? "var(--chip-pin-active)" : "var(--chip-pin-inactive)"}
                                                stroke="var(--chip-pin-stroke)" />
                                        );
                                    })}
                                </g>

                                {/* BOTTOM PINS */}
                                <g strokeWidth="0.7">
                                    {TOP_BOT_PIN_CENTERS.map((cx, i) => {
                                        const active = ACTIVE_PIN_CENTERS.has(cx);
                                        return (
                                            <rect key={`bp${i}`}
                                                x={cx - PIN_W / 2} y={BOT_PIN_Y}
                                                width={PIN_W} height={PIN_H} rx="2"
                                                fill={active ? "var(--chip-pin-active)" : "var(--chip-pin-inactive)"}
                                                stroke="var(--chip-pin-stroke)" />
                                        );
                                    })}
                                </g>

                                {/* LEFT PINS */}
                                <g strokeWidth="0.7">
                                    {lrPinYs.map((py, i) => (
                                        <rect key={`lp${i}`}
                                            x={570 - LR_PIN_W} y={py - LR_PIN_H / 2}
                                            width={LR_PIN_W} height={LR_PIN_H} rx="2"
                                            fill="var(--chip-pin-active)" stroke="var(--chip-pin-stroke)" />
                                    ))}
                                </g>

                                {/* RIGHT PINS */}
                                <g strokeWidth="0.7">
                                    {lrPinYs.map((py, i) => (
                                        <rect key={`rp${i}`}
                                            x={830} y={py - LR_PIN_H / 2}
                                            width={LR_PIN_W} height={LR_PIN_H} rx="2"
                                            fill="var(--chip-pin-active)" stroke="var(--chip-pin-stroke)" />
                                    ))}
                                </g>

                                {/* Status LED */}
                                <circle cx="582" cy="167" r="4" fill="var(--chip-led-color)" opacity="0.25">
                                    <animate attributeName="opacity" values="0.12;0.7;0.12" dur="2.4s" repeatCount="indefinite" />
                                    <animate attributeName="r" values="3;5;3" dur="2.4s" repeatCount="indefinite" />
                                </circle>
                                <circle cx="582" cy="167" r="8" fill="var(--chip-led-color)" opacity="0.04">
                                    <animate attributeName="opacity" values="0.02;0.1;0.02" dur="2.4s" repeatCount="indefinite" />
                                </circle>

                                {/* Chip text */}
                                <text x="700" y="204" textAnchor="middle"
                                    fontFamily="'Orbitron',monospace" fontSize="10" fontWeight="600"
                                    fill="var(--chip-powered-text)" letterSpacing="5">POWERED BY</text>
                                <text x="700" y="236" textAnchor="middle"
                                    fontFamily="'Orbitron',monospace" fontSize="22" fontWeight="900"
                                    fill="var(--chip-brand-text)" letterSpacing="1">
                                    Farm<tspan fill="var(--chip-brand-accent)">X</tspan>pert
                                </text>
                                <text x="700" y="258" textAnchor="middle"
                                    fontFamily="'Sora',sans-serif" fontSize="8" fontWeight="300"
                                    fill="var(--chip-tagline-text)" letterSpacing="6">MULTI-AGENT AI PLATFORM</text>

                                {/* Module labels */}
                                <g fontFamily="'Orbitron',monospace" fontSize="12" fill="var(--chip-label-text)" letterSpacing="1">
                                    <text x="44" y="86" >SOIL AI</text>
                                    <text x="44" y="144">IRRIGATION</text>
                                    <text x="44" y="226">PEST CNNs</text>
                                    <text x="44" y="307">CROP REC</text>
                                    <text x="420" y="16" >NEXT.JS</text>
                                    <text x="612" y="16" >FASTAPI</text>
                                    <text x="812" y="16" >TensorFlow</text>
                                    <text x="990" y="16" >NEXT·API</text>
                                    <text x="110" y="492">PYTHON</text>
                                    <text x="300" y="492">LSTM</text>
                                    <text x="692" y="492">CNN</text>
                                    <text x="900" y="492">TRANSFORMERS</text>
                                    <text x="1190" y="126">YIELD LSTM</text>
                                    <text x="1240" y="179">MARKET AI</text>
                                    <text x="1190" y="286">GROWTH MON</text>
                                    <text x="1190" y="396">KUBERNETES</text>
                                </g>
                            </svg>
                        </div>
                    </div>
                </div>
            </section>
        </>
    );
}
