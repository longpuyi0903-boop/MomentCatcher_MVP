
import React, { useEffect, useRef } from 'react';

const ParticleSphere: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: { x: number; y: number; z: number; px: number; py: number }[] = [];
    const count = 300;
    const radius = 220;

    const init = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      particles = [];
      for (let i = 0; i < count; i++) {
        const theta = Math.random() * 2 * Math.PI;
        const phi = Math.acos(2 * Math.random() - 1);
        particles.push({
          x: radius * Math.sin(phi) * Math.cos(theta),
          y: radius * Math.sin(phi) * Math.sin(theta),
          z: radius * Math.cos(phi),
          px: 0,
          py: 0
        });
      }
    };

    let rotX = 0;
    let rotY = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const focalLength = 500;

      // Slower, more cinematic rotation
      rotX += 0.001;
      rotY += 0.0015;

      particles.forEach((p) => {
        let y1 = p.y * Math.cos(rotX) - p.z * Math.sin(rotX);
        let z1 = p.y * Math.sin(rotX) + p.z * Math.cos(rotX);
        let x1 = p.x * Math.cos(rotY) - z1 * Math.sin(rotY);
        let z2 = p.x * Math.sin(rotY) + z1 * Math.cos(rotY);

        const scale = focalLength / (focalLength + z2);
        const x2 = x1 * scale + centerX;
        const y2 = y1 * scale + centerY;

        const alpha = Math.max(0.05, scale * 0.15);
        // Using zinc/white tones for minimalism
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx.beginPath();
        ctx.arc(x2, y2, scale * 1, 0, Math.PI * 2);
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    init();
    render();

    const handleResize = () => init();
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-0 opacity-40" />;
};

export default ParticleSphere;
