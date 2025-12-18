import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useBackgroundStore } from '../store/backgroundStore'
import './ParticleBackground.css'

/**
 * ParticleBackground - 基于原图的3D粒子球体
 * 核心思路：从原图像素生成粒子，添加球面深度，实现3D自转
 */

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

  // Simplex 3D Noise
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
    i = mod289(i);
    vec4 p = permute(permute(permute(
      i.z + vec4(0.0, i1.z, i2.z, 1.0))
      + i.y + vec4(0.0, i1.y, i2.y, 1.0))
      + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ *ns.x + ns.yyyy;
    vec4 y = y_ *ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x;
    p1 *= norm.y;
    p2 *= norm.z;
    p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
  }

  void main() {
    vColor = color;
    
    vec3 pos = aInitialPosition;
    
    // 1. 鼠标交互
    vec4 viewPos = modelViewMatrix * vec4(pos, 1.0);
    vec4 projectedPos = projectionMatrix * viewPos;
    vec2 ndcPos = projectedPos.xy / projectedPos.w;
    float mouseDist = distance(ndcPos, uMouse);
    float mouseRipple = smoothstep(0.5, 0.0, mouseDist);
    
    vec3 normal = normalize(pos);
    pos += normal * (mouseRipple * -15.0);
    
    // 2. 语音激活
    float voiceNoise = snoise(vec3(pos.x * 0.01, pos.y * 0.01, uTime * 1.5));
    float explosion = uActive * aEdgeFactor * (8.0 + voiceNoise * 25.0);
    pos += normal * explosion;

    // 3. 呼吸效果
    float breathe = sin(uTime * 0.3) * 1.5;
    pos += normal * breathe;
    
    // 4. 表面扰动
    float surfaceNoise = snoise(vec3(pos.x * 0.006, pos.y * 0.006, uTime * 0.12)) * 2.5;
    pos += normal * surfaceNoise;

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
    
    // 粒子大小
    float baseSize = aSize * (1.0 + mouseRipple * 0.2 + uActive * 0.15);
    gl_PointSize = baseSize * (550.0 / -mvPosition.z);
    
    // 透明度
    vOpacity = 0.9 + mouseRipple * 0.1;
    
    gl_Position = projectionMatrix * mvPosition;
  }
`

const FRAGMENT_SHADER = `
  varying vec3 vColor;
  varying float vOpacity;
  
  void main() {
    float r = distance(gl_PointCoord, vec2(0.5));
    if (r > 0.5) discard;
    
    float strength = 1.0 - smoothstep(0.0, 0.5, r);
    strength = pow(strength, 1.2);
    
    gl_FragColor = vec4(vColor, strength * vOpacity);
  }
`

const ParticleBackground = ({ imagePath, active = false }) => {
  const containerRef = useRef(null)
  const rendererRef = useRef(null)
  const sceneRef = useRef(null)
  const cameraRef = useRef(null)
  const particlesRef = useRef(null)
  const animationFrameRef = useRef(null)
  const clockRef = useRef(new THREE.Clock())
  const mouseRef = useRef(new THREE.Vector2(-2, -2))
  const targetMouseRef = useRef(new THREE.Vector2(-2, -2))
  const setBackgroundLoaded = useBackgroundStore((state) => state.setBackgroundLoaded)
  const setParticlesInitialized = useBackgroundStore((state) => state.setParticlesInitialized)

  useEffect(() => {
    if (!containerRef.current) return

    const scene = new THREE.Scene()
    sceneRef.current = scene

    const camera = new THREE.PerspectiveCamera(
      45, 
      containerRef.current.clientWidth / containerRef.current.clientHeight, 
      1, 
      3000
    )
    camera.position.set(0, 0, 650)
    camera.lookAt(0, 0, 0)
    cameraRef.current = camera

    const renderer = new THREE.WebGLRenderer({ 
      antialias: true, 
      alpha: true,
      powerPreference: "high-performance"
    })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight)
    containerRef.current.appendChild(renderer.domElement)
    rendererRef.current = renderer

    const onResize = () => {
      if (!containerRef.current || !cameraRef.current || !rendererRef.current) return
      cameraRef.current.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight
      cameraRef.current.updateProjectionMatrix()
      rendererRef.current.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight)
    }

    const onMouseMove = (e) => {
      targetMouseRef.current.x = (e.clientX / window.innerWidth) * 2 - 1
      targetMouseRef.current.y = -(e.clientY / window.innerHeight) * 2 + 1
    }

    window.addEventListener('resize', onResize)
    window.addEventListener('mousemove', onMouseMove)

    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate)
      const time = clockRef.current.getElapsedTime()
      
      mouseRef.current.lerp(targetMouseRef.current, 0.08)

      if (particlesRef.current) {
        const material = particlesRef.current.material
        material.uniforms.uTime.value = time
        material.uniforms.uActive.value = active ? 1.0 : 0.0
        material.uniforms.uMouse.value = mouseRef.current
        
        // 3D自转
        particlesRef.current.rotation.y = time * 0.05
        particlesRef.current.rotation.x = Math.sin(time * 0.02) * 0.03
      }

      if (rendererRef.current && sceneRef.current && cameraRef.current) {
        rendererRef.current.render(sceneRef.current, cameraRef.current)
      }
    }

    animate()

    return () => {
      window.removeEventListener('resize', onResize)
      window.removeEventListener('mousemove', onMouseMove)
      cancelAnimationFrame(animationFrameRef.current)
      if (rendererRef.current && containerRef.current) {
        containerRef.current.removeChild(rendererRef.current.domElement)
      }
    }
  }, [])

  useEffect(() => {
    if (particlesRef.current?.material?.uniforms) {
      particlesRef.current.material.uniforms.uActive.value = active ? 1.0 : 0.0
    }
  }, [active])

  useEffect(() => {
    if (!imagePath || !sceneRef.current) return

    setBackgroundLoaded(false)
    setParticlesInitialized(false)

    const loader = new THREE.TextureLoader()
    loader.setCrossOrigin('anonymous')
    
    loader.load(imagePath, (texture) => {
      if (particlesRef.current) sceneRef.current?.remove(particlesRef.current)

      const img = texture.image
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      const sampleSize = 500
      canvas.width = sampleSize
      canvas.height = sampleSize
      ctx.drawImage(img, 0, 0, sampleSize, sampleSize)
      
      const imageData = ctx.getImageData(0, 0, sampleSize, sampleSize).data

      // 找到非黑色区域边界
      let minX = sampleSize, maxX = 0, minY = sampleSize, maxY = 0
      const brightnessThreshold = 8
      
      for (let y = 0; y < sampleSize; y++) {
        for (let x = 0; x < sampleSize; x++) {
          const index = (y * sampleSize + x) * 4
          const r = imageData[index]
          const g = imageData[index + 1]
          const b = imageData[index + 2]
          const brightness = (r + g + b) / 3
          
          if (brightness > brightnessThreshold) {
            minX = Math.min(minX, x)
            maxX = Math.max(maxX, x)
            minY = Math.min(minY, y)
            maxY = Math.max(maxY, y)
          }
        }
      }
      
      const imgCenterX = (minX + maxX) / 2
      const imgCenterY = (minY + maxY) / 2
      const imgRadius = Math.max(maxX - minX, maxY - minY) / 2

      const positions = []
      const colors = []
      const sizes = []
      const edgeFactors = []

      const sphereRadius = 220
      const spacing = 1.0

      // 计算图片内容的实际形状
      // 检测是否是圆形图片（星球）还是其他形状
      let circularPixels = 0
      let totalPixels = 0
      
      for (let y = 0; y < sampleSize; y += 2) {
        for (let x = 0; x < sampleSize; x += 2) {
          const index = (y * sampleSize + x) * 4
          const brightness = (imageData[index] + imageData[index + 1] + imageData[index + 2]) / 3
          if (brightness > brightnessThreshold) {
            totalPixels++
            const relX = x - imgCenterX
            const relY = y - imgCenterY
            const dist = Math.sqrt(relX * relX + relY * relY)
            if (dist < imgRadius * 0.95) {
              circularPixels++
            }
          }
        }
      }
      
      // 如果大部分内容在圆形区域内，认为是球形图片
      const isSphericalImage = totalPixels > 0 && (circularPixels / totalPixels) > 0.7
      console.log(`📊 图片形状分析: 圆形=${isSphericalImage}, 圆内比例=${(circularPixels/totalPixels*100).toFixed(1)}%`)

      for (let y = 0; y < sampleSize; y += spacing) {
        for (let x = 0; x < sampleSize; x += spacing) {
          const index = (Math.floor(y) * sampleSize + Math.floor(x)) * 4
          const r = imageData[index]
          const g = imageData[index + 1]
          const b = imageData[index + 2]
          const a = imageData[index + 3]
          
          const brightness = (r + g + b) / 3
          
          if (brightness > brightnessThreshold && a > 30) {
            const relX = x - imgCenterX
            const relY = imgCenterY - y
            
            // 计算到中心的距离（归一化）
            const nx = relX / imgRadius
            const ny = relY / imgRadius
            const dist2D = Math.sqrt(nx * nx + ny * ny)
            
            // 对于非球形图片，使用圆形遮罩裁切
            // 并在边缘添加淡出效果
            if (!isSphericalImage) {
              // 圆形遮罩 - 只保留圆形区域内的粒子
              if (dist2D > 1.0) continue
              
              // 边缘淡出 - 越靠近边缘，越可能被跳过
              const edgeFade = 1.0 - Math.pow(dist2D, 3)
              if (Math.random() > edgeFade && dist2D > 0.7) continue
            }
            
            const px = nx * sphereRadius
            const py = ny * sphereRadius
            
            const isSpherePart = dist2D < 0.98
            
            if (isSpherePart) {
              // 球体部分 - 在球体体积内随机分布粒子
              const maxZ = Math.sqrt(Math.max(0, 1 - dist2D * dist2D))
              
              // 根据位置决定粒子数量 - 中心区域更密集
              const numParticles = Math.max(1, Math.floor((1 - dist2D * 0.5) * 3))
              
              for (let p = 0; p < numParticles; p++) {
                // 在 -maxZ 到 +maxZ 范围内随机选择Z位置
                const randomZ = (Math.random() * 2 - 1) * maxZ
                const zPos = randomZ * sphereRadius
                
                // 每个粒子都有独立的随机X/Y偏移
                const jitter = 2.5
                const jx = (Math.random() - 0.5) * jitter
                const jy = (Math.random() - 0.5) * jitter
                const jz = (Math.random() - 0.5) * jitter
                
                positions.push(px + jx, py + jy, zPos + jz)
                
                // 颜色根据深度渐变 - 正面亮，背面稍暗
                const zNorm = (randomZ + 1) / 2 // 0到1
                const depthDim = 0.6 + zNorm * 0.4
                
                colors.push(
                  Math.min(1, (r / 255) * 1.25 * depthDim),
                  Math.min(1, (g / 255) * 1.25 * depthDim),
                  Math.min(1, (b / 255) * 1.25 * depthDim)
                )
                
                const brightnessNorm = brightness / 255
                sizes.push(1.6 + brightnessNorm * 1.2 + Math.random() * 0.6)
                edgeFactors.push(dist2D)
              }
            }
          }
        }
      }

      console.log(`✨ 生成粒子数量: ${positions.length / 3}`)

      const geometry = new THREE.BufferGeometry()
      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
      geometry.setAttribute('aInitialPosition', new THREE.Float32BufferAttribute(positions, 3))
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
      geometry.setAttribute('aSize', new THREE.Float32BufferAttribute(sizes, 1))
      geometry.setAttribute('aEdgeFactor', new THREE.Float32BufferAttribute(edgeFactors, 1))

      const material = new THREE.ShaderMaterial({
        uniforms: {
          uTime: { value: 0 },
          uActive: { value: 0 },
          uMouse: { value: new THREE.Vector2(-2, -2) },
          uRadius: { value: sphereRadius }
        },
        vertexShader: VERTEX_SHADER,
        fragmentShader: FRAGMENT_SHADER,
        transparent: true,
        vertexColors: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        depthTest: true
      })

      const points = new THREE.Points(geometry, material)
      particlesRef.current = points
      sceneRef.current?.add(points)

      setParticlesInitialized(true)
      setBackgroundLoaded(true)
    }, undefined, (error) => {
      console.error('❌ 图片加载失败:', error)
      setBackgroundLoaded(true)
      setParticlesInitialized(true)
    })
  }, [imagePath, setBackgroundLoaded, setParticlesInitialized])

  return <div ref={containerRef} className="particle-background-container" />
}

export default ParticleBackground
