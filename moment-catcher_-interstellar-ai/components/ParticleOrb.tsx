
import React, { useEffect, useRef } from 'react';
import * as THREE from 'https://esm.sh/three@0.160.0';

interface ParticleOrbProps {
  active?: boolean;
  imageUrl?: string;
}

const VERTEX_SHADER = `
  uniform float uTime;
  uniform float uActive;
  uniform vec2 uMouse;
  uniform float uRadius;
  attribute float aSize;
  attribute vec3 aInitialPosition;
  attribute float aEdgeFactor; 
  varying vec3 vColor;
  varying float vOpacity;

  vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
  vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
  float snoise(vec3 v) {
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    vec4 p = permute(permute(permute(i.z + vec4(0.0, i1.z, i2.z, 1.0)) + i.y + vec4(0.0, i1.y, i2.y, 1.0)) + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    vec4 norm = taylorInvSqrt(vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)));
    p *= norm;
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    return 42.0 * dot(m*m*m*m, vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)));
  }

  void main() {
    vColor = color * 1.6; 
    vec3 pos = aInitialPosition;
    
    // 1. MOUSE GRAVITY
    vec4 viewPos = modelViewMatrix * vec4(pos, 1.0);
    vec4 projectedPos = projectionMatrix * viewPos;
    vec2 ndcPos = projectedPos.xy / projectedPos.w;
    float mouseDist = distance(ndcPos, uMouse);
    float mouseRipple = smoothstep(0.4, 0.0, mouseDist);
    
    // Gravitational warping
    pos += normalize(pos) * (mouseRipple * -45.0);
    
    // 2. VOICE REACTION (Explosion effect on edges)
    float voiceNoise = snoise(vec3(pos.x * 0.015, pos.y * 0.015, uTime * 2.5));
    float explosion = uActive * aEdgeFactor * (30.0 + voiceNoise * 90.0);
    pos += normalize(pos) * explosion;

    // Subtle drift
    pos += normalize(pos) * snoise(vec3(pos.x * 0.01, pos.y * 0.01, uTime * 0.4)) * 5.0;

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
    
    // 3. RADIAL FEATHERING: Fade edges into space
    float distFromCenter = length(aInitialPosition.xy);
    float edgeAlpha = 1.0 - smoothstep(uRadius * 0.75, uRadius * 1.0, distFromCenter);
    
    // Size and Depth adjustment
    gl_PointSize = aSize * (1.4 + mouseRipple + uActive * aEdgeFactor * 0.5) * (1100.0 / -mvPosition.z);
    
    vOpacity = edgeAlpha * (0.8 + mouseRipple * 0.2);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const FRAGMENT_SHADER = `
  varying vec3 vColor;
  varying float vOpacity;
  void main() {
    float r = distance(gl_PointCoord, vec2(0.5));
    if (r > 0.5) discard;
    float strength = pow(1.0 - (r * 2.0), 2.0);
    gl_FragColor = vec4(vColor, strength * vOpacity);
  }
`;

const ParticleOrb: React.FC<ParticleOrbProps> = ({ active = false, imageUrl }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const particlesRef = useRef<THREE.Points | null>(null);
  const animationFrameRef = useRef<number>(0);
  const clockRef = useRef(new THREE.Clock());
  const mouseRef = useRef(new THREE.Vector2(-2, -2));
  const targetMouseRef = useRef(new THREE.Vector2(-2, -2));

  useEffect(() => {
    if (!containerRef.current) return;

    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(38, containerRef.current.clientWidth / containerRef.current.clientHeight, 1, 5000);
    camera.position.z = 1100;
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const onResize = () => {
      if (!containerRef.current || !cameraRef.current || !rendererRef.current) return;
      cameraRef.current.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    };

    const onMouseMove = (e: MouseEvent) => {
      targetMouseRef.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      targetMouseRef.current.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };

    window.addEventListener('resize', onResize);
    window.addEventListener('mousemove', onMouseMove);

    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate);
      const time = clockRef.current.getElapsedTime();
      
      mouseRef.current.lerp(targetMouseRef.current, 0.08);

      if (particlesRef.current) {
        const material = particlesRef.current.material as THREE.ShaderMaterial;
        material.uniforms.uTime.value = time;
        material.uniforms.uActive.value = active ? 1.0 : 0.0;
        material.uniforms.uMouse.value = mouseRef.current;
        
        // Planet Rotation
        particlesRef.current.rotation.y = time * 0.15;
        particlesRef.current.rotation.x = Math.sin(time * 0.08) * 0.1;
      }

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      window.removeEventListener('resize', onResize);
      window.removeEventListener('mousemove', onMouseMove);
      cancelAnimationFrame(animationFrameRef.current);
      if (rendererRef.current && containerRef.current) {
        containerRef.current.removeChild(rendererRef.current.domElement);
      }
    };
  }, [active]);

  useEffect(() => {
    if (!imageUrl || !sceneRef.current) return;

    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin('anonymous');
    
    loader.load(imageUrl, (texture) => {
      if (particlesRef.current) sceneRef.current?.remove(particlesRef.current);

      const img = texture.image;
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const size = 220; 
      canvas.width = size;
      canvas.height = size;
      ctx.drawImage(img, 0, 0, size, size);
      
      const imageData = ctx.getImageData(0, 0, size, size).data;
      const positions = [];
      const colors = [];
      const sizes = [];
      const edgeFactors = [];

      const spacing = 4.5; 
      const radius = (size / 2) * spacing;

      for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
          const index = (y * size + x) * 4;
          const a = imageData[index + 3];

          const px = (x - size / 2) * spacing;
          const py = (size / 2 - y) * spacing;
          const dist2D = Math.sqrt(px * px + py * py);

          // 1. MASKING: Only take pixels within the circle radius to avoid square borders
          if (dist2D < radius && a > 40) {
            const r = imageData[index];
            const g = imageData[index + 1];
            const b = imageData[index + 2];
            
            // 2. SPHERICAL PROJECTION: Create Z-depth for a full 3D orb feel
            const pzBase = Math.sqrt(radius * radius - dist2D * dist2D);
            
            // Add particles for both front and back to create a "thick" or "solid" volume
            const layers = 2; 
            for (let i = 0; i < layers; i++) {
              const sign = i === 0 ? 1 : -1;
              const depthVariance = (Math.random() - 0.5) * 10.0;
              const pz = (pzBase * sign) + depthVariance;

              const edgeFactor = Math.pow(dist2D / radius, 3.5);

              positions.push(px, py, pz);
              colors.push(r / 255, g / 255, b / 255);
              sizes.push(Math.random() * 2.5 + 1.2);
              edgeFactors.push(edgeFactor);
            }
          }
        }
      }

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('aInitialPosition', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
      geometry.setAttribute('aSize', new THREE.Float32BufferAttribute(sizes, 1));
      geometry.setAttribute('aEdgeFactor', new THREE.Float32BufferAttribute(edgeFactors, 1));

      const material = new THREE.ShaderMaterial({
        uniforms: {
          uTime: { value: 0 },
          uActive: { value: 0 },
          uMouse: { value: new THREE.Vector2(-2, -2) },
          uRadius: { value: radius }
        },
        vertexShader: VERTEX_SHADER,
        fragmentShader: FRAGMENT_SHADER,
        transparent: true,
        vertexColors: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });

      const points = new THREE.Points(geometry, material);
      particlesRef.current = points;
      sceneRef.current?.add(points);
    });
  }, [imageUrl]);

  return <div ref={containerRef} className="w-full h-full" />;
};

export default ParticleOrb;
